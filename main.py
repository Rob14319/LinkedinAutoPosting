import os
import requests
import argparse
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


# ─── Write to GitHub Step Summary ──────────────────────────────────────────────
def write_github_summary(content: str) -> None:
    summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write("## 📝 LinkedIn Post Draft\n\n")
            f.write("> **Please review the generated post below.**\n> \n")
            f.write("> If it looks good, click the **Review deployments** button to approve the Production environment and publish it!\n\n")
            f.write("---\n\n")
            for line in content.split("\n"):
                f.write(f"{line}<br>\n")
            f.write("\n---\n")
            f.write("🚀 *This post will be published automatically upon your approval.*\n")
        print("✅ Added draft to GitHub Step Summary.")


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
    parser.add_argument('--generate', action='store_true', help='Generate post and add to GitHub Summary')
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
            
        write_github_summary(post)
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
