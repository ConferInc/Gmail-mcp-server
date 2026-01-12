---
description: Workflow for managing emails: Sending (with mandatory draft review) and Listing (with full content).
---

# Email Management Protocols

## 1. Sending Protocol (Strict "Draft -> Review -> Send")

This workflow MUST be followed whenever the user requests to send an email.

1.  **Draft First**: Never use `send_email` immediately. Always use `draft_email` to create a draft.
    *   Tool: `mcp_gmail-local_draft_email`
    *   Arguments: `to_recipients`, `subject`, `body_text`

2.  **Request Review**: Inform the user that the draft has been created.
    *   Display the **Subject**, **To**, and **Body** text clearly in a code block or structured format.
    *   Ask for explicit approval to send.
    *   **Constraint**: Do NOT proceed to send without explicit user verification.

3.  **Verify and Send**:
    *   **IF** the user approves: Use `mcp_gmail-local_send_email` with the *same* arguments to send the email.
    *   **IF** the user requests changes: Update the parameters and go back to Step 1 (Drafting/Updating).

## 2. Listing/Reading Protocol

This workflow MUST be followed whenever the user asks to "list emails", "show emails", "check inbox" or similar.

1.  **List Metadata**: Use `mcp_gmail-local_list_emails` to get the list of email headers/IDs.
2.  **Fetch Content**: AUTOMATICALLY use `mcp_gmail-local_read_email` for the most relevant emails (default to top 3 if unspecified) to retrieve the full body text. **Do not** stop at just items in the list; fetch the content immediately.
3.  **Format Output**: Present the results in a user-friendly, readable format:
    *   Use **Headings** for Subjects.
    *   Include **From** and **Date** clearly.
    *   Display the **Body** in a dedicated section (e.g., within a blockquote or code block if preserving whitespace is important).
    *   Use separators (e.g., `---`) between emails.
