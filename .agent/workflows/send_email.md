---
description: Workflow for sending emails with mandatory draft and verification
---

This workflow enforces a strict audit trail for sending emails. You must NEVER call `send_email` directly without first drafting and getting user approval.

1. **Draft the Email**
   - Extract the `to_recipients`, `subject`, and `body_text` from the user's request.
   - Call the `draft_email` tool with these details.

2. **Verify with User**
   - Call the `notify_user` tool.
   - In the message, confirm that the draft has been saved.
   - Display the full content of the email (To, Subject, Body) clearly.
   - 
   - Ask: "I have created a draft. Please review it above. Do you want me to send it now?"
   - Set `BlockedOnUser` to `true`.

3. **Send (Conditional)**
   - **IF** the user replies with "Yes", "Approve", or similar:
     - Call the `send_email` tool with the verified details.
     - Confirm completion to the user.
   - **IF** the user replies with "No" or requests changes:
     - **DO NOT** send the email.
     - Make the requested edits and start from Step 1 (Drafting) again, or simply abort if requested.
