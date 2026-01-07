import asyncio
import ssl
import re
import logging
import time
import aiosmtplib
import aioimaplib
import secrets
from pathlib import Path
from starlette.responses import HTMLResponse, JSONResponse
from starlette.requests import Request
from fastmcp import FastMCP


from email.policy import default
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import email

try:
    from src.config import config
    from src.utils import find_folder, extract_email_body, parse_folder_line, check_attachment
except ImportError:
    from config import config
    from utils import find_folder, extract_email_body, parse_folder_line, check_attachment

# Initialize FastMCP Server
mcp = FastMCP("Custom Email MCP")
# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security: Generate a random token for the setup link
SETUP_TOKEN = secrets.token_urlsafe(16)
logger.debug("Setup token generated (length=%d)", len(SETUP_TOKEN))


@mcp.tool()
async def get_configuration_link() -> str:
    """
    Returns a secure link to configure the server via browser.
    """
    base_url = config.APP_URL or "http://localhost:8000"
    # Remove trailing slash if present
    base_url = base_url.rstrip("/")
    
    link = f"{base_url}/setup?token={SETUP_TOKEN}"
    
    if not config.APP_URL:
        return f"Link: {link} \n(Note: Set APP_URL env var in Coolify to your domain to get a correct public link)"
    return f"Click here to configure: {link}"

@mcp.custom_route("/setup", methods=["GET"])
async def setup_page(request: Request):
    token = request.query_params.get("token")
    if token != SETUP_TOKEN:
        return HTMLResponse("<h1>Invalid or missing token</h1>", status_code=403)
    
    # Load template
    template_path = Path(__file__).parent / "templates" / "setup.html"
    try:
        html_content = template_path.read_text(encoding="utf-8")
        html_content = html_content.replace("{{TOKEN}}", SETUP_TOKEN)
        return HTMLResponse(html_content)
    except Exception as e:
        logger.error(f"Template parsing error: {e}")
        return HTMLResponse("<h1>Error loading template</h1>", status_code=500)

@mcp.custom_route("/setup", methods=["POST"])
async def handle_setup(request: Request):
    token = request.query_params.get("token")
    if token != SETUP_TOKEN:
        return JSONResponse({"error": "Invalid token"}, status_code=403)
    
    form_data = await request.form()
    
    try:
        config.save_to_file(
            smtp_host=form_data.get("smtp_host"),
            smtp_port=int(form_data.get("smtp_port")),
            imap_host=form_data.get("imap_host"),
            imap_port=int(form_data.get("imap_port")),
            email_user=form_data.get("email_user"),
            email_pass=form_data.get("email_pass")
        )
        return HTMLResponse("<h1>Configuration Saved!</h1><p>You can close this window and start using the agent.</p>")
    except Exception as e:
        return HTMLResponse(f"<h1>Error</h1><p>{e}</p>", status_code=500)

@mcp.tool()
async def configure_email(
    email_user: str, 
    email_pass: str, 
    smtp_host: str = "smtp.gmail.com", 
    smtp_port: int = 465, 
    imap_host: str = "imap.gmail.com", 
    imap_port: int = 993
) -> str:
    """
    Configures the email server with credentials. 
    This is persistent and saves to a file on the server.
    """
    try:
        config.save_to_file(smtp_host, smtp_port, imap_host, imap_port, email_user, email_pass)
        return "✅ Configuration saved successfully. You can now use email tools."
    except Exception as e:
        return f"❌ Failed to save configuration: {e}"

@mcp.tool()
async def check_connection() -> dict:
    """
    Validates the ability to connect and authenticate with both SMTP and IMAP servers.
    Returns a dictionary with status checks and latency stats.
    """
    if not config.is_configured:
        return {"error": "Server not configured. Please use `configure_email` first."}

    results = {
        "smtp": {"status": "pending", "host": config.SMTP_HOST},
        "imap": {"status": "pending", "host": config.IMAP_HOST}
    }

    # Check SMTP
    try:
        logger.info(f"Connecting to SMTP: {config.SMTP_HOST}:{config.SMTP_PORT}")
        
        use_tls = config.SMTP_PORT == 465
        
        smtp_client = aiosmtplib.SMTP(hostname=config.SMTP_HOST, port=config.SMTP_PORT, use_tls=use_tls)
        await smtp_client.connect()
        
        if not use_tls:
            await smtp_client.starttls()

        await smtp_client.login(config.EMAIL_USER, config.EMAIL_PASS)
        await smtp_client.quit()
        results["smtp"]["status"] = "success"
        results["smtp"]["message"] = "Authenticated successfully"
    except Exception as e:
        logger.error(f"SMTP Error: {e}")
        results["smtp"]["status"] = "failed"
        results["smtp"]["error"] = str(e)

    # Check IMAP
    try:
        logger.info(f"Connecting to IMAP: {config.IMAP_HOST}:{config.IMAP_PORT}")
        ssl_context = ssl.create_default_context()
        imap_client = aioimaplib.IMAP4_SSL(host=config.IMAP_HOST, port=config.IMAP_PORT, ssl_context=ssl_context)
        await imap_client.wait_hello_from_server()
        
        login_response = await imap_client.login(config.EMAIL_USER, config.EMAIL_PASS)
        if login_response.result == 'OK':
             results["imap"]["status"] = "success"
             results["imap"]["message"] = "Authenticated successfully"
        else:
             results["imap"]["status"] = "failed"
             results["imap"]["error"] = f"Login failed: {login_response}"
        
        await imap_client.logout()

    except Exception as e:
        logger.error(f"IMAP Error: {e}")
        results["imap"]["status"] = "failed"
        results["imap"]["error"] = str(e)

    return results

@mcp.tool()
async def list_folders() -> list[dict]:
    """
    Lists all available IMAP folders/mailboxes on the email server.
    
    Returns:
        List of dictionaries containing 'name' and 'flags' for each folder.
    """
    if not config.is_configured:
        return [{"error": "Server not configured. Please use `configure_email` first."}]

    try:
        ssl_context = ssl.create_default_context()
        client = aioimaplib.IMAP4_SSL(host=config.IMAP_HOST, port=config.IMAP_PORT, ssl_context=ssl_context)
        await client.wait_hello_from_server()
        await client.login(config.EMAIL_USER, config.EMAIL_PASS)
        
        # List all folders
        status, folders_data = await client.list('""', '*')
        
        folders = []
        if status == 'OK':

            for folder_line in folders_data:
                parsed = parse_folder_line(folder_line)
                if parsed:
                    folders.append(parsed)
        
        await client.logout()
        return folders
        
    except Exception as e:
        logger.error(f"List Folders Error: {e}")
        return [{"error": str(e)}]

@mcp.tool()
async def list_emails(folder: str = "INBOX", limit: int = 10, sender: str | None = None, to: str | None = None) -> list[dict]:
    """
    Fetches email metadata from a specific folder.
    
    Args:
        folder: The folder to search (default="INBOX")
        limit: Max number of emails to return (default=10).
        sender: Optional sender email address to filter by (FROM "email").
        to: Optional recipient email address to filter by (TO "email").
    """
    if not config.is_configured:
        return [{"error": "Server not configured. Please use `configure_email` first."}]

    try:
        ssl_context = ssl.create_default_context()
        client = aioimaplib.IMAP4_SSL(host=config.IMAP_HOST, port=config.IMAP_PORT, ssl_context=ssl_context)
        await client.wait_hello_from_server()
        
        await client.login(config.EMAIL_USER, config.EMAIL_PASS)
        
        # Select folder logic
        res = await client.select(folder)
        if res.result != 'OK':
             candidates = [folder]
             if folder.lower() in ["sent", "sent items", "sent mail"]:
                 candidates = ["Sent Mail", "Sent", "Sent Items", "INBOX.Sent", "[Gmail]/Sent Mail"]
             elif folder.lower() in ["drafts", "draft"]:
                 candidates = ["Drafts", "Draft", "INBOX.Drafts", "[Gmail]/Drafts"]
             elif folder.lower() in ["trash", "bin", "deleted items"]:
                 candidates = ["Trash", "Bin", "Deleted Items", "[Gmail]/Trash"]
             elif folder.lower() in ["junk", "spam"]:
                 candidates = ["Junk", "Spam", "Junk E-mail", "[Gmail]/Spam"]
                 
             real_folder = await find_folder(client, candidates)
             res = await client.select(real_folder)
             if res.result != 'OK':
                  await client.logout()
                  return [{"error": f"Folder {folder} not found"}]

        # Build Query
        query_parts = []
        if sender:
            query_parts.append(f'(FROM "{sender}")')
        if to:
            query_parts.append(f'(TO "{to}")')
        
        # If no specific filters, default to ALL
        if not query_parts:
            query_str = "ALL"
        else:
            query_str = " ".join(query_parts)
        
        logger.info(f"Searching in {folder} with query: {query_str}")
        status, data = await client.search(query_str)
        if status != 'OK':
             await client.logout()
             return [{"error": f"Search failed: {status}"}]

        # Get the list of email IDs
        email_ids = data[0].split()
        
        # Taking the last 'limit' emails (most recent if server appends new ones at end)
        # Usually IMAP sequence numbers increase with time.
        start_index = max(0, len(email_ids) - limit)
        recent_ids = email_ids[start_index:]
        
        # Inverse to show newest first
        recent_ids.reverse()

        emails = []
        for e_id in recent_ids:
            # Decode bytes to string for fetch command
            e_id_str = e_id.decode() if isinstance(e_id, bytes) else str(e_id)
            
            # Fetch envelope (headers)
            status, info = await client.fetch(e_id_str, '(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])')
            
            if status == 'OK':
                # aioimaplib returns: [command_line, header_content (bytearray), closing_paren, completion]
                # The actual header content is at index 1 as bytes or bytearray
                raw_header = b""
                if len(info) >= 2:
                    header_data = info[1]
                    if isinstance(header_data, (bytes, bytearray)):
                        raw_header = bytes(header_data)
                
                # Parse header
                msg = email.message_from_bytes(raw_header, policy=default)
                
                subject = msg.get("subject", "No Subject")
                sender = msg.get("from", "Unknown")
                date = msg.get("date", "Unknown")
                
                # Decode subject if necessary (though policy=default handles most)


                emails.append({
                    "id": e_id_str,
                    "sender": str(sender),
                    "subject": str(subject),
                    "date": str(date)
                })

        await client.logout()
        return emails

    except Exception as e:
        logger.error(f"List Emails Error: {e}")
        return [{"error": str(e)}]

@mcp.tool()
async def read_email(email_id: str, folder: str = "INBOX") -> str:
    """
    Fetches the full content of a specific email.
    
    Args:
        email_id: The unique ID from list_emails.
        folder: The folder to search (default="INBOX").
        
    Returns:
        Full text body (HTML stripped to Markdown).
    """
    if not config.is_configured:
        return "Error: Server not configured. Please use `configure_email` first."

    try:
        ssl_context = ssl.create_default_context()
        client = aioimaplib.IMAP4_SSL(host=config.IMAP_HOST, port=config.IMAP_PORT, ssl_context=ssl_context)
        await client.wait_hello_from_server()
        await client.login(config.EMAIL_USER, config.EMAIL_PASS)
        
        # Select folder
        res = await client.select(folder)
        if res.result != 'OK':
             await client.logout()
             return f"Error: Failed to select folder '{folder}': {res}"
        
        # Fetch full body
        status, data = await client.fetch(email_id, '(RFC822)')
        
        content = ""
        
        if status == 'OK':


            
            raw_email = b""
            # Loop through response from aioimaplib
            for part in data:
                 if isinstance(part, (bytes, bytearray)):
                     part_bytes = bytes(part)
                     if b"RFC822" in part_bytes and part_bytes.strip().endswith(b"}"):
                         continue
                     if part_bytes.strip() == b")":
                         continue
                     raw_email += part_bytes
            
            msg = email.message_from_bytes(raw_email, policy=default)
            content = extract_email_body(msg)

        await client.logout()
        return content  if content else "No content found or empty email."

    except Exception as e:
        logger.error(f"Read Email Error: {e}")
        return f"Error reading email: {str(e)}"

@mcp.tool()
async def draft_email(to_recipients: list[str], subject: str, body_text: str) -> str:
    """
    Creates a new email and saves it to the provider's Drafts folder.
    
    Args:
        to_recipients: List of email addresses.
        subject: Email subject.
        body_text: Body content (text).
    """
    if not config.is_configured:
        return "Error: Server not configured. Please use `configure_email` first."

    try:
        # Create Message
        msg = MIMEMultipart()
        msg['From'] = config.EMAIL_USER
        msg['To'] = ", ".join(to_recipients)
        msg['Subject'] = subject
        msg['Date'] = email.utils.formatdate(localtime=True)
        # Ensure newlines are treated correctly
        body_text = body_text.replace("\\n", "\n")
        msg.attach(MIMEText(body_text, 'plain'))

        # Connect to IMAP
        ssl_context = ssl.create_default_context()
        client = aioimaplib.IMAP4_SSL(host=config.IMAP_HOST, port=config.IMAP_PORT, ssl_context=ssl_context)
        await client.wait_hello_from_server()
        await client.login(config.EMAIL_USER, config.EMAIL_PASS)

        # Append to Drafts
        # Note: "Drafts" is common, but some providers use "INBOX.Drafts" or "[Gmail]/Drafts"
        folder = "Drafts"
        
        # APPEND command requires the message to be bytes and usually flags
        msg_bytes = msg.as_bytes()
        
        # specific format: "dd-Mon-yyyy hh:mm:ss +timezone"
        # Simple format:
        now = time.strftime("%d-%b-%Y %H:%M:%S +0000", time.gmtime())
        date_time = f'"{now}"'
        
        response = await client.append(msg_bytes, mailbox=folder, flags=r'(\Seen \Draft)', date=date_time)
        
        await client.logout()
        
        if response.result == 'OK':
             return "✅ Saved to Drafts folder successfully."
        else:
             return f"❌ Failed to save draft. Server response: {response}"

    except Exception as e:
        logger.error(f"Draft Email Error: {e}")
        return f"Error saving draft: {str(e)}"




@mcp.tool()
async def send_email(to_recipients: list[str], subject: str, body_text: str, cc_recipients: list[str] = None) -> str:
    """
    Sends an email immediately using SMTP and saves a copy to Sent.
    
    Args:
        to_recipients: List of email addresses.
        subject: Email subject.
        body_text: Body content (text).
        cc_recipients: Optional list of CC addresses.
    """
    if not config.is_configured:
        return "Error: Server not configured. Please use `configure_email` first."

    try:
        msg = EmailMessage()
        msg['From'] = config.EMAIL_USER
        msg['To'] = ", ".join(to_recipients)
        msg['Subject'] = subject
        msg['Date'] = email.utils.formatdate(localtime=True)
        # Ensure newlines are treated correctly
        body_text = body_text.replace("\\n", "\n")
        msg.set_content(body_text)
        
        if cc_recipients:
            msg['Cc'] = ", ".join(cc_recipients)

        logger.info(f"Sending email to {to_recipients}...")

        # 1. Send via SMTP
        use_tls = config.SMTP_PORT == 465
        smtp_client = aiosmtplib.SMTP(hostname=config.SMTP_HOST, port=config.SMTP_PORT, use_tls=use_tls)
        
        await smtp_client.connect()
        if not use_tls:
             await smtp_client.starttls()
        
        await smtp_client.login(config.EMAIL_USER, config.EMAIL_PASS)
        # Capture response
        errors, response_msg = await smtp_client.send_message(msg)
        await smtp_client.quit()
        
        # 2. Append to Sent via IMAP
        try:
            ssl_context = ssl.create_default_context()
            imap_client = aioimaplib.IMAP4_SSL(host=config.IMAP_HOST, port=config.IMAP_PORT, ssl_context=ssl_context)
            await imap_client.wait_hello_from_server()
            await imap_client.login(config.EMAIL_USER, config.EMAIL_PASS)
            
            # Use corrected folder list - Prioritize "Sent" to avoid space quoting issues
            sent_folder = await find_folder(imap_client, ["Sent", "Sent Mail", "Sent Items", "INBOX.Sent", "[Gmail]/Sent Mail"])
            
            # Quote folder if it has spaces
            if " " in sent_folder:
                sent_folder = f'"{sent_folder}"'
                
            msg_bytes = msg.as_bytes()
            
            # Using None for date_time to avoid type errors observed in testing
            await imap_client.append(msg_bytes, mailbox=sent_folder, flags=r'(\Seen)', date=None)
            await imap_client.logout()
            return f"✅ Email sent ({response_msg}) and saved to Sent folder."
            
        except Exception as e:
            logger.error(f"Failed to append to Sent: {e}")
            return f"✅ Email sent ({response_msg}), but failed to save copy to Sent folder."

    except Exception as e:
        logger.error(f"Send Email Error: {e}")
        return f"Error sending email: {str(e)}"


if __name__ == "__main__":
    mcp.run()
