# Gmail MCP Server

MCP server for Gmail integration with Claude, Cursor, Kiro, and other MCP clients.

## Tools
| Tool | Description |
|------|-------------|
| `list_emails` | List/search emails (returns id, snippet, subject, from, date) |
| `read_email` | Read full email content by ID |
| `create_draft` | Create a draft email (requires `send_draft` to actually send) |
| `send_draft` | Send a drafted email |

## Prompts
| Prompt | Description |
|--------|-------------|
| `summarize_unread` | Summarize unread emails with priority |
| `draft_reply` | Draft reply to an email |
| `compose_email` | Compose new email |
| `search_emails` | Natural language email search |
| `daily_digest` | Daily email digest by category |

---

## Setup Details for running it locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get Google OAuth Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → Enable **Gmail API**
3. **APIs & Services** → **Credentials** → **Create OAuth Client ID** → **Desktop App**
4. Download JSON → rename to `credentials.json` → place in this folder (gmail-mcp-server)

### 3. Authenticate
The server supports **Login-on-Demand**. You don't need to authenticate before running the server.

1.  **Start the Server**: Run it locally or in the cloud.
2.  **Ask a Question**: e.g., "Check my unread emails".
3.  **Follow Instructions**: If you aren't logged in, the server will reply with a **URL**.
4.  **Authorize**: Click the URL, authorize Google, and copy the code.
5.  **Submit Code**: Paste the code into the chat using the `submit_auth_code` tool (or just tell the model "Here is the code: ...").

---

## Running the Server

Add this to your config file:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "python",
      "args": ["<ABSOLUTE_PATH_TO_REPO>/server.py"]
    }
  }
}
```
*Note: Replace `<ABSOLUTE_PATH_TO_REPO>` with the actual full path to this directory.*
Now paste the config in your mcp.json file. to use the server in IDE

Next refresh your IDE and you should be able to use the server.

### Test with MCP Inspector
```bash
npx @modelcontextprotocol/inspector python "D:/path/to/gmail-mcp-server/server.py"
```

---

## Configuration

You can configure the server using environment variables to avoid hardcoding files or to support different environments. You can either set these in your system, in the `mcp.json` env block, or by creating a `.env` file in the project directory (copy `.env.example`).

| Variable | Description | Default |
|----------|-------------|---------|
| `GMAIL_CREDENTIALS_PATH` | Path to `credentials.json` | `credentials.json` (in repo) |
| `GMAIL_TOKEN_PATH` | Path to `token.json` | `token.json` (in repo) |

### Option 1: Using `.env` file (Recommended for local)
1. Copy `.env.example` to `.env`
2. Update the values in `.env`
3. The server will automatically load them.

### Option 2: `mcp.json` with Env Vars

```json
{
  "mcpServers": {
    "gmail": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {
        "GMAIL_CREDENTIALS_PATH": "/secure/path/to/credentials.json",
        "GMAIL_TOKEN_PATH": "/secure/path/to/token.json"
      }
    }
  }
}
```

---

## File Structure
```
gmail-mcp-server/
├── server.py          # MCP server (FastMCP)
├── gmail_client.py    # Gmail API wrapper
├── auth.py            # OAuth2 handling
├── authenticate.py    # One-time auth script
├── credentials.json   # Google OAuth creds (you provide)
├── token.json         # Auth token (auto-generated)
└── requirements.txt   # Dependencies
```

## Security - IMPORTANT

*   **`credentials.json`**: This file identifies the **Application** (the code), NOT you.
    *   *Risk Level*: Low.
    *   *If shared*: Someone can run the app pretending to be your project, but they **cannot** access your emails without logging in.
*   **`token.json`**: This file contains the **Access Keys** to your specific Gmail account.
    *   *Risk Level*: **CRITICAL**.
    *   *If shared*: Someone **CAN** read and send emails as you.
    *   **NEVER SHARE `token.json`.** Ensure it is in your `.gitignore` (it is by default in this repo).

- `send_draft` sends real emails - use carefully

