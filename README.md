# LinkedIn AI Agent — Daily Auto-Poster

Automatically posts a daily thought leadership story to your LinkedIn profile.
Powered by **Google Gemini Flash** (free) + **GitHub Actions** (free).

---

## Stack

| What | Service | Cost |
|---|---|---|
| AI post generation | Google Gemini 1.5 Flash | Free (15 req/day) |
| Scheduling & running | GitHub Actions | Free (2,000 min/month) |
| LinkedIn posting | LinkedIn API | Free |

---

## Setup (one-time, ~30 minutes)

### Step 1 — Get your Gemini API key

1. Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Click **Create API key**
3. Copy and save it

---

### Step 2 — Create a LinkedIn Developer App

1. Go to [developer.linkedin.com](https://developer.linkedin.com) and sign in
2. Click **Create App**, give it any name, link it to a LinkedIn page
   - If you don't have a company page, create a free one — it's just required by LinkedIn
3. Under **Products**, request access to:
   - **Share on LinkedIn**
   - **Sign In with LinkedIn using OpenID Connect**
4. Copy your **Client ID** and **Client Secret** from the **Auth** tab

---

### Step 3 — Get your LinkedIn access token

1. In your LinkedIn App, go to **Auth** tab → add redirect URL:
   ```
   https://localhost:3000/callback
   ```

2. Open this URL in your browser (replace `YOUR_CLIENT_ID`):
   ```
   https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=https://localhost:3000/callback&scope=openid%20profile%20w_member_social
   ```

3. Authorize the app. You'll land on a broken page — that's fine. Copy the `code=...` value from the URL bar.

4. Run this curl command to exchange the code for a token:
   ```bash
   curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
     -d grant_type=authorization_code \
     -d code=PASTE_YOUR_CODE_HERE \
     -d client_id=YOUR_CLIENT_ID \
     -d client_secret=YOUR_CLIENT_SECRET \
     -d redirect_uri=https://localhost:3000/callback
   ```

5. Copy the `access_token` from the response. It lasts **60 days**.

---

### Step 4 — Find your LinkedIn Person URN

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://api.linkedin.com/v2/userinfo
```

Look for the `sub` field. Your URN is: `urn:li:person:{sub}`

---

### Step 5 — Set up the GitHub repo

1. Create a **private** GitHub repository
2. Push this project:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOU/linkedin-agent.git
   git push -u origin main
   ```

3. Go to **Settings → Secrets and variables → Actions** and add:
   - `GEMINI_API_KEY`
   - `LINKEDIN_ACCESS_TOKEN`
   - `LINKEDIN_PERSON_URN`

---

### Step 6 — Test it

1. Go to the **Actions** tab in your repo
2. Click **Daily LinkedIn Post** → **Run workflow**
3. Watch the logs — you should see the generated post and a success message
4. Check your LinkedIn profile to confirm it posted

---

## Customization

### Change post topics
Edit the `TOPICS` list in `main.py` to match your specific niche or experiences.

### Change posting time
Edit the cron schedule in `.github/workflows/post.yml`.
- Format: `minute hour * * *` (UTC time)
- Current setting: `30 3 * * *` = 9:00 AM IST daily
- For 8:00 AM IST: `30 2 * * *`

### Tweak the tone
Edit the prompt inside the `generate_post()` function in `main.py`.

---

## Token refresh reminder

Your LinkedIn access token expires every **60 days**.
Set a calendar reminder to repeat Step 3 and update the GitHub secret.

---

## Troubleshooting

| Error | Fix |
|---|---|
| `401 Unauthorized` | Your LinkedIn token expired — refresh it |
| `403 Forbidden` | LinkedIn app products not approved yet — wait 1-2 days |
| `Gemini quota exceeded` | You've hit 15 req/day — unlikely for 1 post/day |
| Workflow not running | Check Actions tab is enabled in repo settings |
