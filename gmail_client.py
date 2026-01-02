"""Gmail API Client."""

import base64
import re
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GmailClient:
    def __init__(self, creds):
        self.svc = build("gmail", "v1", credentials=creds, cache_discovery=False)
    
    def list_messages(self, query="", max_results=10):
        if not isinstance(max_results, int) or max_results < 1:
            return {"success": False, "error": "max_results must be a positive integer"}
            
        try:
            msgs = self.svc.users().messages().list(
                userId="me", q=query, maxResults=min(100, max(1, max_results))
            ).execute().get("messages", [])
            
            results = []
            for m in msgs:
                d = self.svc.users().messages().get(
                    userId="me", id=m["id"], format="metadata",
                    metadataHeaders=["Subject", "From", "Date"]
                ).execute()
                h = {x["name"]: x["value"] for x in d.get("payload", {}).get("headers", [])}
                results.append({
                    "id": m["id"], "snippet": d.get("snippet", "")[:200],
                    "subject": h.get("Subject", ""), "from": h.get("From", ""), "date": h.get("Date", "")
                })
            return {"success": True, "messages": results, "total": len(results)}
        except HttpError as e:
            return self._err(e)
    
    def get_message_detail(self, msg_id):
        if not msg_id or not isinstance(msg_id, str):
            return {"success": False, "error": "Invalid message_id"}
            
        try:
            m = self.svc.users().messages().get(userId="me", id=msg_id, format="full").execute()
            h = {x["name"]: x["value"] for x in m.get("payload", {}).get("headers", [])}
            return {"success": True, "message": {
                "id": msg_id, "thread_id": m.get("threadId", ""),
                "subject": h.get("Subject", ""), "from": h.get("From", ""),
                "to": h.get("To", ""), "date": h.get("Date", ""),
                "body": self._body(m.get("payload", {})), "labels": m.get("labelIds", [])
            }}
        except HttpError as e:
            return self._err(e)
    

    
    def create_draft(self, to, subject, body):
        if not self._validate_email(to):
            return {"success": False, "error": f"Invalid email format: {to}"}
        try:
            msg = MIMEText(body)
            msg["to"], msg["subject"] = to, subject
            b = {"raw": base64.urlsafe_b64encode(msg.as_bytes()).decode()}
            d = self.svc.users().drafts().create(userId="me", body={"message": b}).execute()
            return {"success": True, "draft_id": d.get("id", ""), "message_id": d.get("message", {}).get("id", "")}
        except HttpError as e:
            return self._err(e)

    def send_draft(self, draft_id):
        try:
            r = self.svc.users().drafts().send(userId="me", body={"id": draft_id}).execute()
            return {"success": True, "message_id": r.get("id", ""), "thread_id": r.get("threadId", "")}
        except HttpError as e:
            return self._err(e)

    def send_message(self, to, subject, body):
        if not self._validate_email(to):
            return {"success": False, "error": f"Invalid email format: {to}"}
        try:
            msg = MIMEText(body)
            msg["to"], msg["subject"] = to, subject
            r = self.svc.users().messages().send(
                userId="me", body={"raw": base64.urlsafe_b64encode(msg.as_bytes()).decode()}
            ).execute()
            return {"success": True, "message_id": r.get("id", ""), "thread_id": r.get("threadId", "")}
        except HttpError as e:
            return self._err(e)

    def _validate_email(self, email):
        # Basic regex for email validation
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None
    
    def _body(self, p):
        if d := p.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(d).decode("utf-8", errors="replace")
        for part in p.get("parts", []):
            if part.get("mimeType") == "text/plain" and (d := part.get("body", {}).get("data")):
                return base64.urlsafe_b64decode(d).decode("utf-8", errors="replace")
            if b := self._body(part): return b
        return ""
    

    def _err(self, e):
        s = e.resp.status
        # Detailed error mapping
        errors = {
            400: "Bad Request - Invalid query or parameters",
            401: "Token expired or invalid auth - Try re-authenticating",
            403: "Permission denied - Check scopes or quota exceeded",
            404: "Resource not found - Email/Draft may have been deleted",
            429: "Rate limited - Too many requests",
            500: "Gmail API Server Error"
        }
        err_msg = errors.get(s, f"Gmail API error ({s})")
        
        import logging
        logging.getLogger(__name__).error(f"Gmail API Failure: {err_msg} details={e}")
        return {"success": False, "error": err_msg}
