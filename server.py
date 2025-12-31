"""Gmail MCP Server using FastMCP."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastmcp import FastMCP
from auth import get_gmail_credentials
from gmail_client import GmailClient

mcp = FastMCP("gmail-mcp-server")
def client():
    return GmailClient(get_gmail_credentials())


@mcp.tool()
def list_emails(query: str = "", max_results: int = 10) -> dict:
    """List emails from Gmail. Use Gmail search syntax (is:unread, from:x, etc). Returns id, snippet, subject, from, date."""
    return client().list_messages(query, max_results)


@mcp.tool()
def read_email(message_id: str) -> dict:
    """Read full email content by ID. Use id from list_emails."""
    return client().get_message_detail(message_id)


@mcp.tool()
def create_draft(to: str, subject: str, body: str) -> str:
    """Create a draft email. User must review and approve this draft before it is sent using send_draft."""
    result = client().create_draft(to, subject, body)
    if result.get("success"):
        return f"Draft created with ID: {result.get('draft_id')}. Please ask the user to review and confirm to send."
    return f"Failed to create draft: {result.get('error')}"


@mcp.tool()
def send_draft(draft_id: str) -> dict:
    """Sends a draft email. Use this ONLY after the user has confirmed they want to send the draft."""
    return client().send_draft(draft_id)


@mcp.prompt()
def summarize_unread(max_emails: int = 10) -> str:
    """Summarize all unread emails in inbox."""
    return f"""Use list_emails with query "is:unread" and max_results={max_emails}.
For each email: show sender, subject, 1-line summary, and priority (🔴high/🟡medium/🟢low).
Group by priority and highlight any action items."""


@mcp.prompt()
def draft_reply(message_id: str, tone: str = "professional") -> str:
    """Draft a reply to a specific email."""
    return f"""Use read_email with message_id "{message_id}" to get the full content.
Draft a {tone} reply that addresses all points raised and answers any questions.
Show the complete draft with subject line and ask for confirmation before sending."""


@mcp.prompt()
def compose_email(to: str, purpose: str, tone: str = "professional") -> str:
    """Help compose a new email."""
    return f"""Compose a {tone} email to {to} for: {purpose}.
Include a clear subject line, proper greeting, concise body, and professional closing.
Show the complete draft and confirm with user before using create_draft tool."""


@mcp.prompt()
def search_emails(criteria: str) -> str:
    """Find emails matching specific criteria."""
    return f"""Convert this search request to Gmail query syntax: "{criteria}".
Use list_emails with the query and show results in a table: Date | From | Subject | Preview.
Offer to read any specific email if user wants more details."""


@mcp.prompt()
def daily_digest() -> str:
    """Get a daily digest of important emails."""
    return """Fetch emails using: "is:unread" and "newer_than:1d is:important".
Categorize into: 🔴 Action Required, 📬 Unread, ⭐ Important, 📋 FYI.
Present as a scannable summary with sender, subject, and 1-line preview for each."""


if __name__ == "__main__":
    mcp.run(transport="stdio")
