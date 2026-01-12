# Deploying Email MCP to Coolify 🚀

This guide specifically covers **Scenario B: Using the Web Configuration UI** with persistent storage. This ensures your beautiful setup page works in production and your credentials are saved across restarts.

## Prerequisites
- A running instance of **Coolify**.
- Access to your **GitHub/GitLab** where this repo is hosted.

---

## Step 1: Create the Project
1. Go to your Coolify Dashboard.
2. Click **+ New Resource**.
3. Select **Public Repository** (or Private if you have connected your GitHub).
4. Enter your repository URL and Branch (usually `main`).
5. Click **Check Repository**.

## Step 2: Build Configuration
Keep the defaults mostly as is, but verify:
- **Build Pack**: `Nixpacks` or `Docker Configuration` (Nixpacks usually works great for Python).
- **Port**: `8000` (This is where our Web UI lives).

## Step 3: 💾 Persistent Storage (CRITICAL)
Since you want to use the Web UI to save credentials, we must ensure `credentials.json` isn't lost if the container restarts.

1.  In your Project Dashboard, go to the **Storage** tab.
2.  Click **+ Add**.
3.  **Volume Name**: `email_mcp_data` (or any name you like).
4.  **Destination Path**: `/app/credentials.json`
    *   *Note: In Docker, our app lives in `/app`. We are mapping this specific file to a persistent volume.*
5.  Click **Save**.

## Step 4: Environment Variables
We need to tell the app where it lives so it can generate the correct "Configuration Link" for you.

1.  Go to the **Environment Variables** tab.
2.  Add a new variable:
    - **Key**: `APP_URL`
    - **Value**: `https://[your-coolify-domain-for-this-app]`
    - *Example*: `https://email-agent.coolify.io`

## Step 5: Deploy
1.  Go back to the **Configuration** tab.
2.  Click **Deploy**.
3.  Wait for the build to finish.

---

## How to Use After Deployment

### 1. Configure
once deployed, navigate to your app's URL. You will likely see a `404 Not Found` or raw JSON because the root path `/` isn't defined. This is normal!

You need to **check your Coolify Logs** to get the setup token.
1.  Click **Logs** in Coolify.
2.  Look for a line like:
    ```text
    INFO:     HTTP Setup Server running on http://0.0.0.0:8000/setup
    DEBUG:    Setup token generated (length=22)
    ```
    *(Wait... actually, since you are on Coolify, checking logs is annoying. The SMARTER way involving the agent is below)* 👇

### The Smart Way
Just use the Agent!
1.  Connect your MCP Client (Cursor/Claude) to this new Remote MCP URL (the Coolify URL).
2.  Ask the Agent: `get configuration link`
3.  The Agent will return the correct secure link with the token.
4.  Click the link -> **Use the Beautiful UI** -> Save.

### 2. Auto-Shutdown
After you save the config:
- The Web Server will shut down (for security).
- Your Agent continues running with the saved credentials.
- If you ever need to re-configure, just **Restart** the container in Coolify to bring the Web UI back up for a few minutes.

---

## Troubleshooting
- **"Server not configured"**: Did you mount the volume correctly in Step 3?
- **"Connection Refused"**: Ensure Port `8000` is exposed in Coolify settings.
- **Link doesn't work**: Ensure `APP_URL` matches your actual domain exactly.
