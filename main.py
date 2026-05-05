import os
import requests
import argparse
import time
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

    # Robust model selection
    print("🔍 Fetching available models...")
    try:
        available_models = [m.name for m in client.models.list()]
        print(f"✅ Found {len(available_models)} models: {available_models}")
    except Exception as e:
        print(f"⚠️ Could not list models: {e}. Falling back to default names.")
        available_models = []

    # Aggressive search: try every model that contains 'flash', 'pro', or 'gemma'
    models_to_try = []
    for m in available_models:
        name = m.replace("models/", "")
        # Only try models that are likely to be text generation models
        if any(keyword in name.lower() for keyword in ["flash", "pro", "gemma", "nano"]):
            # Skip models that are obviously for other tasks
            if any(skip in name.lower() for skip in ["embedding", "imagen", "veo", "aqa", "tts"]):
                continue
            models_to_try.append(name)
    
    # Sort them to prioritize 'flash' and 'lite' models
    models_to_try.sort(key=lambda x: ("flash" not in x.lower(), "lite" not in x.lower(), x))

    print(f"📋 Will attempt these models in order: {models_to_try}")

    for model_name in models_to_try:
        print(f"🤖 Attempting to generate with model: {model_name}...")
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"⚠️ {model_name} failed: {e}")
            # If it's a transient 503 error, try once more with a sleep
            if "503" in str(e):
                print("   Retrying once after 10s...")
                time.sleep(10)
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    return response.text.strip()
                except:
                    pass
            # Otherwise, just move to the next model in the list
            continue

    raise Exception("❌ All available models failed. Your API key might have 0 quota for all generation models.")

    raise Exception("❌ All models failed to generate content. Please check your API key and quota.")


# ─── Write to GitHub Step Summary ──────────────────────────────────────────────
def write_github_summary(content: str) -> None:
    import urllib.parse
    summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_file:
        # Create a WhatsApp Smart Link
        encoded_text = urllib.parse.quote(f"Please review this LinkedIn draft:\n\n{content}")
        whatsapp_url = f"https://wa.me/?text={encoded_text}"
        
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write("# 🚀 LinkedIn Post Ready for Review\n\n")
            f.write("| Feature | Action |\n")
            f.write("| :--- | :--- |\n")
            f.write(f"| **WhatsApp Preview** | [📲 Open in WhatsApp]({whatsapp_url}) |\n")
            f.write("| **Publishing** | Click 'Review deployments' above to Approve |\n\n")
            
            f.write("## 📝 Generated Draft Content\n")
            f.write("> [!NOTE]\n")
            f.write("> This post was generated using Gemini 1.5 Flash based on today's rotation topic.\n\n")
            
            f.write("```text\n")
            f.write(f"{content}\n")
            f.write("```\n\n")
            
            f.write("---\n")
            f.write("### 🛠 Next Steps\n")
            f.write("1. Click the **WhatsApp link** above to read it comfortably on your phone.\n")
            f.write("2. If you want to change anything, click **Reject** and edit the script.\n")
            f.write("3. If it looks great, click **Approve** to publish it live to LinkedIn! 🚀\n")
            
        print("✅ Added professional draft summary to GitHub.")


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


# ─── Send Telegram Notification ──────────────────────────────────────────────
def send_telegram_notification(content: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    run_id = os.getenv("GITHUB_RUN_ID")
    repository = os.getenv("GITHUB_REPOSITORY")
    
    if not token or not chat_id:
        print("⚠️ Telegram token or chat_id missing. Skipping notification.")
        return

    # Link directly to the GitHub Action run page for one-click approval
    approval_url = f"https://github.com/{repository}/actions/runs/{run_id}"
    
    message = f"📝 *New LinkedIn Draft Ready*\n\n{content}\n\n🚀 *Review and Approve here:*"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "✅ REVIEW & APPROVE", "url": approval_url}
            ]]
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("✅ Telegram notification sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send Telegram notification: {e}")


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--generate', action='store_true', help='Generate post and add to GitHub Summary')
    parser.add_argument('--post', action='store_true', help='Publish the post from draft file to LinkedIn')
    args = parser.parse_args()

    if args.generate:
        print("🤖 Generating post process started...")
        try:
            post = generate_post()
            print("\n--- Generated Post ---")
            print(post)
            print("----------------------\n")
            
            with open("draft.txt", "w", encoding="utf-8") as f:
                f.write(post)
                
            write_github_summary(post)
            send_telegram_notification(post)
            print("🎉 Generation complete! Waiting for approval on Telegram/GitHub.")
        except Exception as e:
            print(f"❌ Error during generation: {e}")
            exit(1)

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
        # Default behavior: generate and post immediately
        post = generate_post()
        post_to_linkedin(post)
