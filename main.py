import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import date

load_dotenv()

# ─── Topics rotation ───────────────────────────────────────────────────────────
TOPICS = [
    "a mistake I made as an entrepreneur and what it taught me",
    "the unglamorous side of building a business nobody talks about",
    "a counterintuitive lesson about money and business growth",
    "how I learned to make decisions with incomplete information",
    "what a failure taught me about resilience and starting over",
    "the moment I realized I was thinking about business all wrong",
    "a small habit that quietly changed how I run my business",
    "what I wish I knew before starting my entrepreneurial journey",
    "a conversation that shifted how I think about leadership",
    "the difference between being busy and actually building something",
    "what building a business taught me about human nature",
    "a risk I took that didn't pay off — and why I'd do it again",
    "how I learned to say no and why it changed everything",
    "the mentor advice I ignored (and later regretted)",
    "what entrepreneurship really feels like at 2am",
]


# ─── Generate post with Gemini ─────────────────────────────────────────────────
def generate_post() -> str:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-1.5-flash")

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

    response = model.generate_content(prompt)
    return response.text.strip()


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
    print("🤖 Generating post with Gemini Flash...")
    post = generate_post()

    print("\n--- Generated Post ---")
    print(post)
    print("----------------------\n")

    print("📤 Posting to LinkedIn...")
    post_to_linkedin(post)
    print("🎉 Done!")
