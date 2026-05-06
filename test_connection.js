import axios from 'axios';
import dotenv from 'dotenv';
dotenv.config();

async function testVercelLogic() {
  const GITHUB_TOKEN = (process.env.GITHUB_TOKEN || '').trim();
  const REPO_OWNER = (process.env.REPO_OWNER || '').trim();
  const REPO_NAME = (process.env.REPO_NAME || '').trim();
  const content = "Verification test from Mirror Script";

  console.log(`🔍 Testing Connection to: ${REPO_OWNER}/${REPO_NAME}`);
  
  try {
    const response = await axios.post(
      `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/dispatches`,
      {
        event_type: 'publish_post',
        client_payload: { content }
      },
      {
        headers: {
          'Authorization': `Bearer ${GITHUB_TOKEN}`,
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'Vercel-Test-Script'
        }
      }
    );
    console.log("✅ SUCCESS! GitHub accepted the signal.");
  } catch (error) {
    console.error("❌ FAILED!");
    console.error("Status:", error.response?.status);
    console.error("Data:", error.response?.data);
    console.error("Message:", error.message);
  }
}

testVercelLogic();
