import os
import requests
import argparse
import time
import base64
import resend
import sys
from google import genai
from dotenv import load_dotenv
from datetime import date

# Ensure console supports emojis/unicode on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

# ─── Topics rotation ───────────────────────────────────────────────────────────
TOPICS = [
    "recent AI breakthroughs in India's tech ecosystem",
    "the reality of scaling a startup in Mumbai/Bangalore",
    "why Indian founders should prioritize global personal branding",
    "decoding the latest marketing trend seen in Indian D2C brands",
    "lessons from a failed pivot in my entrepreneurial journey",
    "how AI agents are disrupting traditional SaaS workflows in India",
    "the future of Tech in the Indian market: 2025 and beyond",
    "building a brand that resonates with both Gen Z and traditional Indian businesses",
    "what Silicon Valley can learn from Indian 'Jugaad' innovation",
    "the impact of open-source AI on Indian software engineering",
]

# ─── Generate post with Gemini ─────────────────────────────────────────────────
def generate_post() -> str:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # Determine post type based on time (2 short, 2 long)
    # 10 AM & 6 PM = Long (Story-driven)
    # 2 PM & 11 PM = Short (Punchy/Insightful)
    current_hour_ist = (datetime.now().hour + 5) % 24  # Simple UTC to IST approx
    is_long = current_hour_ist in [10, 18, 15] # 15 is for manual tests
    
    post_type = "Long Form Story (200-300 words)" if is_long else "Short & Punchy (50-100 words)"
    
    prompt = f"""You are a top-tier Indian Entrepreneur and Tech Visionary. 
    Your voice is natural, authoritative, and deeply relatable to the Indian business ecosystem.

    Topic: {topic}
    Post Type: {post_type}

    PERSONA GUIDELINES:
    - You are an Indian founder. Use subtle cultural context (Bangalore tech, Mumbai hustle, etc.) where natural.
    - Mention relevant brands, organizations, or tech frameworks (e.g., NVIDIA, OpenAI, Zomato, Reliance, etc.) if they align with the trend.
    - Avoid "corporate speak." Sound like you're talking to a peer over coffee.

    RESEARCH REQUIREMENT:
    Please search for the latest news and trends (from the last 24 hours) related to {topic}. 
    Incorporate one specific recent development or insight to make it authoritative.

    Instructions:
    - Start with a strong 'hook' sentence.
    - {f"Tell a story or share a detailed lesson. Use 1-2 sentence paragraphs." if is_long else "Be direct, punchy, and share a quick hot take."}
    - Share one clear, actionable takeaway.
    - End with a genuine, short question.
    - Use 3-4 hashtags. No emojis. Short paragraphs only.

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
        print(f"🤖 Attempting to generate with model: {model_name} (with Search Grounding)...")
        try:
            # Configure search tools
            config = {
                'tools': [{'google_search': {}}]
            }

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
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


# ─── Send Premium Email Notification ──────────────────────────────────────────
def send_premium_email(content: str) -> None:
    api_key = os.getenv("RESEND_API_KEY")
    to_email = os.getenv("USER_EMAIL")
    portal_url = os.getenv("PORTAL_URL", "http://localhost:5173") # Default to local for dev
    
    if not api_key or not to_email:
        print("⚠️ Resend API Key or User Email missing. Skipping email notification.")
        return

    resend.api_key = api_key

    # Encode content for the portal URL
    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    review_link = f"{portal_url}?c={encoded_content}"

    html_content = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #ffffff;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #0a66c2; margin-bottom: 5px;">🚀 Post Ready for Review</h1>
            <p style="color: #64748b; font-size: 16px;">Your daily LinkedIn draft is generated and waiting.</p>
        </div>
        
        <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; border-left: 4px solid #0a66c2; margin-bottom: 30px;">
            <p style="white-space: pre-wrap; color: #1e293b; line-height: 1.6; font-size: 15px;">{content}</p>
        </div>
        
        <div style="text-align: center;">
            <a href="{review_link}" style="background-color: #0a66c2; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 18px; display: inline-block;">
                Review & Publish Now
            </a>
        </div>
        
        <div style="margin-top: 40px; border-top: 1px solid #e2e8f0; padding-top: 20px; text-align: center; color: #94a3b8; font-size: 12px;">
            <p>Sent by Antigravity LinkedIn Agent • Automated Content System</p>
        </div>
    </div>
    """

    try:
        params = {
            "from": "LinkedIn Agent <onboarding@resend.dev>",
            "to": [to_email],
            "subject": "📝 Review your LinkedIn Post for Today",
            "html": html_content,
        }
        resend.Emails.send(params)
        print(f"✅ Premium review email sent to {to_email}!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--generate', action='store_true', help='Generate post and send review email')
    parser.add_argument('--post', action='store_true', help='Publish the post to LinkedIn')
    parser.add_argument('--content', type=str, help='Direct content to post (overrides draft.txt)')
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
            send_premium_email(post)
            print("🎉 Generation complete! Check your email for the review link.")
        except Exception as e:
            print(f"❌ Error during generation: {e}")
            exit(1)

    elif args.post:
        print("📤 Preparing to post...")
        try:
            if args.content:
                post = args.content
            else:
                with open("draft.txt", "r", encoding="utf-8") as f:
                    post = f.read()
            
            print("🚀 Posting to LinkedIn...")
            post_to_linkedin(post)
            print("🎉 Done!")
        except Exception as e:
            print(f"❌ Error during posting: {e}")
            exit(1)
    else:
        # Default behavior: generate and post immediately
        post = generate_post()
        post_to_linkedin(post)
