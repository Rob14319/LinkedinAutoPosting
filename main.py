import os
import requests
import argparse
import urllib.parse
from google import genai
from dotenv import load_dotenv
from datetime import date

load_dotenv()

# ─── Topics rotation ───────────────────────────────────────────────────────────
TOPICS = [
    "a lesson I learned about entrepreneurship the hard way",
    "why personal branding is more than just a buzzword",
    "a digital marketing strategy that completely surprised me",
    "what building a digital presence taught me about consistency",
    "how marketing automation saved my sanity",
    "a real-world application of AI that changed how I work",
]

# ─── Generate post with Gemini ─────────────────────────────────────────────────
def generate_post() -> str:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    topic = TOPICS[date.today().toordinal() % len(TOPICS)]

    prompt = f"""You are writing a LinkedIn post for a business founder and entrepreneur.

Topic: {topic}

Instructions:
- Write in first person, storytelling style — personal, honest, and human
- Start with a single compelling sentence that hooks the reader (no "I'm excited to share" openers)
- Tell a short story or specific moment — make it feel real, not generic
- Share one clear insight or lesson that emerges naturally from the story
- End with a short, genuine question that invites others to share their experience
- Use short paragraphs (1-2 sentences each) for easy reading on mobile
- Total length: 180-250 words
- Add 3-4 relevant hashtags at the very end on their own line
- Do NOT use bullet points, emojis, or corporate jargon
- Sound like a real person, not a content marketer

Write only the post. No titles, no preamble."""

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text.strip()


# ─── Send WhatsApp Notification ─────────────────────────────────────────────────
def send_whatsapp_notification(content: str, run_id: str) -> None:
    phone = os.getenv("WHATSAPP_PHONE")
    apikey = os.getenv("CALLMEBOT_API_KEY")
    repo = os.getenv("GITHUB_REPOSITORY")
    
    if not phone or not apikey:
        print("⚠️ WhatsApp credentials not found. Skipping notification.")
        return

    approval_url = f"https://github.com/{repo}/actions/runs/{run_id}" if repo and run_id else "GitHub Actions"
    
    message = f"🤖 *LinkedIn Post Draft Ready for Approval!*\n\n{content}\n\n👉 *Approve here:* {approval_url}"
    encoded_message = urllib.parse.quote(message)
    
    url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_message}&apikey={apikey}"
    response = requests.get(url)
    if response.status_code == 200:
        print("✅ WhatsApp notification sent!")
    else:
        print(f"❌ Failed to send WhatsApp notification. Error: {response.text}")


# ─── Post to LinkedIn ──────────────────────────────────────────────────────────
def post_to_linkedin(content: str) -> None:
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    urn = os.getenv("LINKEDIN_PERSON_URN")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    payload = {
        "author": urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    response = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers=headers,
        json=payload,
    )
    response.raise_for_status()
    post_id = response.json().get("id", "unknown")
    print(f"✅ Posted successfully! Post ID: {post_id}")


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--generate', action='store_true', help='Generate post and notify via WhatsApp')
    parser.add_argument('--post', action='store_true', help='Publish the post from draft file to LinkedIn')
    args = parser.parse_args()

    if args.generate:
        print("🤖 Generating post with Gemini Flash...")
        post = generate_post()
        
        print("\n--- Generated Post ---")
        print(post)
        print("----------------------\n")
        
        # Save to file so the next job can pick it up
        with open("draft.txt", "w", encoding="utf-8") as f:
            f.write(post)
            
        print("📤 Sending WhatsApp notification for approval...")
        run_id = os.getenv("GITHUB_RUN_ID", "")
        send_whatsapp_notification(post, run_id)
        print("🎉 Generation complete! Waiting for approval on GitHub.")

    elif args.post:
        print("📤 Reading draft from file...")
        try:
            with open("draft.txt", "r", encoding="utf-8") as f:
                post = f.read()
            print("🚀 Posting to LinkedIn...")
            post_to_linkedin(post)
            print("🎉 Done!")
        except FileNotFoundError:
            print("❌ Error: draft.txt not found. Cannot post.")
            exit(1)
    else:
        print("🤖 Generating post with Gemini Flash...")
        post = generate_post()
        print("\n--- Generated Post ---")
        print(post)
        print("----------------------\n")
        print("📤 Posting to LinkedIn...")
        post_to_linkedin(post)
        print("🎉 Done!")
