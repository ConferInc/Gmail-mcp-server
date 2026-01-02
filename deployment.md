# Deployment Guide (Render, Railway, Docker)

This server uses **Login-on-Demand**. You deploy it *without* authentication, and the first user to query it will be asked to log in via a secure link.

## 1. Prerequisites
*   **GitHub Repo**: Push this code to a private GitHub repository.
*   **Credentials**: You need your `credentials.json` (Google OAuth Client Secrets).

## 2. Deploy to Render (Recommended)
Render is effectively free for simple Docker apps and very easy to set up.

1.  **Dashboard**: Go to [dashboard.render.com](https://dashboard.render.com/).
2.  **New Web Service**: Click **New +** -> **Web Service**.
3.  **Source**: Connect your GitHub repository.
4.  **Configuration**:
    *   **Runtime**: `Docker`
    *   **Region**: Any (e.g., Oregon)
    *   **Free Instance Type**: Yes
5.  **Environment Variables**:
    *   (Optional) `GMAIL_CREDENTIALS_PATH`: `/etc/secrets/credentials.json`
6.  **Secret Files**:
    *   Click **Advanced** -> **Secret Files**.
    *   Filename: `credentials.json` (or whatever path you set above)
    *   Content: Paste the contents of your local `credentials.json`.
7.  **Deploy**: Click **Create Web Service**.

## 3. How to Use
Once deployed, Render gives you a URL (e.g., `https://gmail-mcp.onrender.com`).

1.  **Configure Client**:
    Add to your `mcp.json` (or Cursor/Claude config):
    ```json
    {
      "mcpServers": {
        "gmail-remote": {
          "url": "https://gmail-mcp.onrender.com/sse",
          "transport": "sse"
        }
      }
    }
    ```
2.  **First Run**:
    *   Ask: "Check my email"
    *   Response: "Authentication Required! Visit..."
    *   Click link -> Get Code -> Paste Code.
    *   Done! The server is now authenticated for this session.

## 4. Deploying via Docker (Generic)
If you use another provider (Railway, AWS, VPS):

1.  **Build**: `docker build -t gmail-mcp .`
2.  **Run**: You must mount your credentials file.
    ```bash
    docker run -p 8000:8000 -v $(pwd)/credentials.json:/app/credentials.json gmail-mcp
    ```
