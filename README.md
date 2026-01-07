# Email MCP Server

A Model Context Protocol (MCP) server implementation for interacting with custom email providers via SMTP and IMAP. This server allows LLMs to list folders, read emails, draft emails, and send emails using your own email infrastructure.

## Features

-   **Check Connection**: Verify SMTP and IMAP connectivity.
-   **List Folders**: Retrieve all available mailboxes.
-   **List Emails**: Fetch metadata for emails in a specific folder, with filtering options.
-   **Read Email**: Get the full content of a specific email.
-   **Draft Email**: Create emails and save them to the Drafts folder.
-   **Send Email**: Send emails via SMTP and save a copy to the Sent folder.

## Quickstart

Follow these steps to set up the Email MCP server.

### 1. Installation

1.  **Clone the repository**:
    ```bash
    git clone <your-repo-url>
    cd "Custom email MCP"
    ```

2.  **Create and activate a virtual environment**:
    *   **Windows**:
        ```powershell
        python -m venv venv
        .\venv\Scripts\activate
        ```
    *   **macOS/Linux**:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### 2. Configuration

1.  **Create the `.env` file**:
    Copy `.env.example` to `.env`:
    ```bash
    cp .env.example .env
    # OR on Windows
    copy .env.example .env
    ```

2.  **Update `.env`**:
    Open the `.env` file and fill in your email provider details (SMTP/IMAP settings and credentials).

### 3. Add to MCP Client (IDE/Claude Desktop)

Add the following configuration to your MCP settings file (e.g., `claude_desktop_config.json` or your IDE's MCP config).

**Important**: Use the **absolute path** to the python executable inside your virtual environment and the absolute path to the `src/server.py` script.

```json
{
  "mcpServers": {
    "custom-email": {
      "command": "C:/path/to/Custom email MCP/venv/Scripts/python",
      "args": [
        "C:/path/to/Custom email MCP/src/server.py"
      ],
      "env": {
        "PYTHONPATH": "C:/path/to/Custom email MCP"
      }
    }
  }
}
```

### Configuration Breakdown

Here is what each part of the configuration does:

*   **`command`**: The absolute path to the Python executable **inside your virtual environment**.
    *   *Why?* This ensures the server runs with the correct installed dependencies (aioimaplib, aiosmtplib, etc.) independent of your system Python.
    *   *How to find it*: In your terminal, with `venv` activated, run:
        *   Windows (PowerShell): `(Get-Command python).Source`
        *   macOS/Linux: `which python`

*   **`args`**: A list of arguments passed to the command.
    *   The first argument is the **absolute path** to the `src/server.py` file.
    *   *Why?* This tells python which script to execute.

*   **`env` -> `PYTHONPATH`**: The absolute path to the project root directory.
    *   *Why?* This tells Python where to look for the `src` module. Without this, you might see "Module not found: src" errors because the script is running from outside the project context.
