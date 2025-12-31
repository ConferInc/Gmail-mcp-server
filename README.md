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
cd Gmail-mcp-server
pip install -r requirements.txt
```

### 2. Get Google OAuth Credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create project → Enable **Gmail API**
3. **APIs & Services** → **Credentials** → **Create OAuth Client ID** → **Desktop App**
4. Download JSON → rename to `credentials.json` → place in this folder (gmail-mcp-server)

### 3. Authenticate (one-time)
```bash
python authenticate.py
```
This opens browser for Google login and creates `token.json` automatically.

---

## Running the Server

Add this to your config file, make sure to give path of server.py

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

like this :
<img width="632" height="202" alt="image" src="https://github.com/user-attachments/assets/f051873a-92e7-41be-a8d4-87730280a676" />

Next refresh your IDE and you should be able to use the server.


### Test with MCP Inspector
```bash
npx @modelcontextprotocol/inspector python "D:/path/to/gmail-mcp-server/server.py"
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

