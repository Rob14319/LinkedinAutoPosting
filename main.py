import os
import requests
import argparse
import time
import base64
import resend
import sys
from google import genai
from dotenv import load_dotenv
from datetime import date, datetime, timedelta
import json
from twilio.rest import Client
import traceback

# Ensure console supports emojis/unicode on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

# ─── Topics rotation ───────────────────────────────────────────────────────────
TOPICS = [
    "Creative Branding and identity design for modern Indian D2C brands",
    "Creative Marketing strategies that are disrupting the Indian market",
    "the reality of scaling a startup in Mumbai/Bangalore",
    "why Indian founders should prioritize global personal branding",
    "decoding the latest marketing trend seen in Indian consumer brands",
    "lessons from a failed pivot in my entrepreneurial journey",
    "how AI agents are disrupting traditional SaaS workflows in India",
    "the future of Tech and Entrepreneurship in the Indian market: 2025 and beyond",
    "building a brand that resonates with both Gen Z and traditional Indian businesses",
    "Startup trends and venture capital shifts in the Indian ecosystem",
    "psychology of color and design in creative branding",
    "how story-driven marketing wins in the Indian social media landscape"
]

# ─── Generate post with Gemini ─────────────────────────────────────────────────
def generate_post() -> str:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # Determine post type based on time (2 short, 2 long)
    # 10 AM (4:30 UTC) & 6 PM (12:30 UTC) = Long (Story-driven)
    # 2 PM (8:30 UTC) & 11 PM (17:30 UTC) = Short (Punchy/Insightful)
    # Manual trigger usually happens around 3 PM - 4 PM IST (Slot 15)
    current_hour_ist = (datetime.utcnow() + timedelta(hours=5, minutes=30)).hour
    is_long = current_hour_ist in [10, 18, 15, 16, 17, 19] # Included manual test hours
    
    post_type = "Long Form Story (200-300 words)" if is_long else "Short & Punchy (50-100 words)"
    
    # Select a fresh topic
    import random
    topic = random.choice(TOPICS)

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
def post_to_linkedin(content: str) -> str:
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
    return post_id



# ─── Grok Image Generation ───────────────────────────────────────────────────
def generate_image_with_grok(post_content: str) -> str:
    api_key = os.getenv("XAI_API_KEY")
    if not api_key or api_key == "your_xai_api_key_here":
        return None

    print("🎨 Generating image with Grok...")
    try:
        # First, get a good image prompt from Gemini based on the post
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        prompt_request = f"Create a short, professional, high-quality image generation prompt for a LinkedIn post with this content: {post_content[:500]}. Style: Modern, entrepreneurial, high-tech, clean. Focus on one central object or a conceptual scene."
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt_request)
        image_prompt = response.text.strip()

        # Call xAI Image Generation API
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "prompt": image_prompt,
            "model": "grok-beta", # xAI's vision/generation capable model
            "n": 1,
            "size": "1024x1024"
        }
        
        resp = requests.post("https://api.x.ai/v1/images/generations", headers=headers, json=payload)
        resp.raise_for_status()
        
        data = resp.json()
        return data['data'][0]['url']
    except Exception as e:
        print(f"⚠️ Grok Image error: {e}")
        return None


# ─── Post Discovery (Engagement Bot) ──────────────────────────────────────────
def discover_relevant_posts() -> list:
    """Finds relevant LinkedIn post URLs using Gemini Search."""
    print("🔍 Discovering relevant posts in your niche...")
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    import random
    topic = random.choice(TOPICS)
    
    prompt = f"Find 5 current LinkedIn post URLs about {topic} from the last 24 hours. Just provide the URLs."

    try:
        config = {'tools': [{'google_search': {}}]}
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=config
        )
        
        print(f"DEBUG: Gemini raw response length: {len(response.text)}")
        # Match various LinkedIn post/activity patterns
        urls = re.findall(r'https?://(?:www\.)?linkedin\.com/[\w\d\-\./?=&%:]+', response.text)
        # Filter for actual post/activity links
        urls = [u for u in urls if '/posts/' in u or 'activity' in u]
            
        print(f"DEBUG: Found filtered URLs: {urls}")
        print(f"✅ Found {len(urls)} potential posts to engage with.")
        return list(set(urls))[:15]
    except Exception as e:
        print(f"⚠️ Discovery error: {e}")
        return []

def generate_engagement_comment(post_url: str) -> str:
    """Generates an insightful comment for a target post."""
    print(f"✍️ Drafting comment for: {post_url}")
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    prompt = f"""You are a top-tier Indian Entrepreneur and Tech Visionary. 
    You found this trending LinkedIn post: {post_url}
    
    Write a short, insightful, and professional comment (20-40 words).
    - Add value or share a unique perspective.
    - Sound human, not generic ("Great post!", "Agree!").
    - Relate it to the Indian tech/startup context if possible.
    - No hashtags, no emojis.
    
    Write ONLY the comment."""

    try:
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ Comment generation error: {e}")
        return None

def send_comment_review_email(post_url: str, comment: str) -> None:
    """Sends an email to approve a comment on someone else's post."""
    api_key = os.getenv("RESEND_API_KEY")
    to_email = os.getenv("USER_EMAIL")
    portal_url = os.getenv("PORTAL_URL", "http://localhost:5173")
    
    if not api_key or not to_email:
        return

    # Extract activity ID for the portal link
    # URL format: ...activity-723456...
    import re
    match = re.search(r'activity-(\d+)', post_url)
    activity_id = match.group(1) if match else None
    if not activity_id:
        print(f"⚠️ Could not extract activity ID from {post_url}. Skipping.")
        return

    payload = {
        "t": "engagement", # Type: engagement
        "c": comment,
        "aid": activity_id, # Activity ID
        "url": post_url
    }
    
    encoded_payload = base64.b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8')
    review_link = f"{portal_url}?p={encoded_payload}"

    html_content = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;">
        <h2 style="color: #0a66c2;">💬 New Engagement Opportunity</h2>
        <p>Found a trending post related to your field. Should we comment?</p>
        
        <div style="background-color: #f1f5f9; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p><strong>Target Post:</strong> <a href="{post_url}">{post_url}</a></p>
            <p><strong>Draft Comment:</strong><br/><em>{comment}</em></p>
        </div>
        
        <div style="text-align: center;">
            <a href="{review_link}" style="background-color: #0a66c2; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                Review & Approve Comment
            </a>
        </div>
    </div>
    """

    resend.api_key = api_key
    try:
        resend.Emails.send({
            "from": "Engagement Bot <onboarding@resend.dev>",
            "to": [to_email],
            "subject": "💬 Review: Auto-Comment on LinkedIn",
            "html": html_content,
        })
        print(f"✅ Comment review email sent for {post_url}")
    except Exception as e:
        print(f"❌ Failed to send comment email: {e}")


# ─── Send Premium Email Notification ──────────────────────────────────────────
def send_premium_email(content: str, image_url: str = None) -> None:
    api_key = os.getenv("RESEND_API_KEY")
    to_email = os.getenv("USER_EMAIL")
    portal_url = os.getenv("PORTAL_URL", "http://localhost:5173")
    
    if not api_key or not to_email:
        print("⚠️ Resend API Key or User Email missing. Skipping email notification.")
        return

    resend.api_key = api_key

    # Encode payload for the portal link (Complex payload: Text + Image)
    payload = {"c": content}
    if image_url:
        payload["i"] = image_url
        
    encoded_payload = base64.b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8')
    review_link = f"{portal_url}?p={encoded_payload}"

    html_content = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #ffffff;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: #0a66c2; margin-bottom: 5px;">🚀 Post Ready for Review</h1>
            <p style="color: #64748b; font-size: 16px;">Your daily LinkedIn draft is generated and waiting.</p>
        </div>
        
        <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; border-left: 4px solid #0a66c2; margin-bottom: 30px;">
            <p style="white-space: pre-wrap; color: #1e293b; line-height: 1.6; font-size: 15px;">{content}</p>
        </div>
        
        {f'<div style="margin-bottom: 30px;"><img src="{image_url}" style="width:100%; border-radius:12px; border: 1px solid #e2e8f0;" /></div>' if image_url else ""}
        
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


# ─── Generate Comment with Gemini ──────────────────────────────────────────────
def generate_comment(post_content: str) -> str:
    print("🤖 Generating comment...")
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        prompt = f"""You are the author of this LinkedIn post. Write a short, engaging follow-up comment to post on your own post immediately after publishing. 
        It should ask a question to the audience or share one extra tiny insight to kickstart engagement.
        Keep it under 3 sentences. No hashtags. No emojis.
        
        Post Content:
        {post_content}
        """
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ Comment generation failed: {e}")
        return "Would love to hear your thoughts on this! Drop a comment below 👇"


# ─── Post Comment to LinkedIn ──────────────────────────────────────────────────
def post_comment_to_linkedin(post_id: str, comment: str) -> None:
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    urn = os.getenv("LINKEDIN_PERSON_URN")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    payload = {
        "actor": urn,
        "object": post_id,
        "message": {
            "text": comment
        }
    }

    import urllib.parse
    encoded_post_id = urllib.parse.quote(post_id)

    try:
        response = requests.post(
            f"https://api.linkedin.com/v2/socialActions/{encoded_post_id}/comments",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        print(f"✅ Comment posted successfully!")
    except Exception as e:
        print(f"❌ Failed to post comment: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")


# ─── Send Twilio Notification ─────────────────────────────────────────────────
def send_twilio_notification(message: str) -> None:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")
    to_number = os.getenv("TWILIO_TO_NUMBER")

    if not all([account_sid, auth_token, from_number, to_number]):
        print("⚠️ Twilio credentials missing. Skipping SMS/WhatsApp notification.")
        return

    try:
        client = Client(account_sid, auth_token)
        if from_number.startswith("whatsapp:") and not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"
            
        msg = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        print(f"✅ Twilio notification sent! Message SID: {msg.sid}")
    except Exception as e:
        print(f"❌ Failed to send Twilio notification: {e}")


# ─── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--generate', action='store_true', help='Generate post and send review email')
    parser.add_argument('--engage', action='store_true', help='Discover posts and draft engagement comments')
    parser.add_argument('--post', action='store_true', help='Publish the post to LinkedIn')
    parser.add_argument('--content', type=str, help='Direct content to post (overrides draft.txt)')
    parser.add_argument('--comment', type=str, help='First comment to post under the content')
    parser.add_argument('--activity_id', type=str, help='External activity URN to comment on')
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
                
            # Generate image for long slots
            current_hour_ist = (datetime.utcnow() + timedelta(hours=5, minutes=30)).hour
            image_url = None
            if current_hour_ist in [10, 18, 15, 16]:
                image_url = generate_image_with_grok(post)

            write_github_summary(post)
            send_premium_email(post, image_url)
            
            # Send Twilio Notification
            portal_url = os.getenv("PORTAL_URL", "http://localhost:5173")
            send_twilio_notification(f"📝 LinkedIn Draft Ready for Review!\nReview here: {portal_url}")
            
            print("🎉 Generation complete! Check your email for the review link.")
        except Exception as e:
            error_msg = f"❌ LinkedIn Generation Failed: {e}"
            print(error_msg)
            print(traceback.format_exc())
            send_twilio_notification(error_msg)
            exit(1)

    elif args.engage:
        print("🔍 Engagement discovery started (Auto-Publishing)...")
        try:
            posts = discover_relevant_posts()
            published_count = 0
            for url in posts:
                print(f"🔍 Processing URL: {url}")
                # Extract activity ID
                import re
                # Try to find a long number (7000... or 7200...) which is the activity ID
                match = re.search(r'(\d{10,25})', url)
                activity_id = match.group(1) if match else None
                
                if not activity_id:
                    continue

                comment = generate_engagement_comment(url)
                if comment:
                    try:
                        print(f"🚀 Auto-Publishing comment to: {url}")
                        post_comment_to_linkedin(f"urn:li:activity:{activity_id}", comment)
                        published_count += 1
                        # Sleep to avoid rate limits
                        time.sleep(5)
                    except Exception as pe:
                        print(f"⚠️ Failed to auto-post: {pe}")
            
            print(f"🎉 Engagement complete! Auto-published {published_count} comments.")
        except Exception as e:
            print(f"❌ Error during engagement discovery: {e}")
            exit(1)

    elif args.post:
        print("📤 Preparing to post...")
        try:
            if args.activity_id:
                # Commenting on an external post
                print(f"🚀 Engagement: Commenting on external activity {args.activity_id}...")
                post_comment_to_linkedin(f"urn:li:activity:{args.activity_id}", args.comment)
            else:
                # Normal posting flow
                if args.content:
                    post = args.content
                else:
                    with open("draft.txt", "r", encoding="utf-8") as f:
                        post = f.read()
                
                print("🚀 Posting to LinkedIn...")
                post_id = post_to_linkedin(post)
                
                # Post comment
                print("⏳ Waiting 3s before posting comment...")
                time.sleep(3)
                
                if args.comment:
                    comment = args.comment
                else:
                    print("💬 Generating comment...")
                    comment = generate_comment(post)
                
                post_comment_to_linkedin(post_id, comment)
                
                send_twilio_notification(f"✅ LinkedIn Post Published Successfully!\nPost ID: {post_id}\nComment: {comment}")
            print("🎉 Done!")
        except Exception as e:
            error_msg = f"❌ LinkedIn Posting Failed: {e}"
            print(error_msg)
            print(traceback.format_exc())
            send_twilio_notification(error_msg)
            exit(1)
    else:
        # Default behavior: generate and post immediately
        try:
            post = generate_post()
            post_id = post_to_linkedin(post)
            comment = generate_comment(post)
            post_comment_to_linkedin(post_id, comment)
            send_twilio_notification(f"✅ Auto LinkedIn Post Published!\nPost ID: {post_id}")
        except Exception as e:
            error_msg = f"❌ Auto LinkedIn Process Failed: {e}"
            print(error_msg)
            print(traceback.format_exc())
            send_twilio_notification(error_msg)
            exit(1)
