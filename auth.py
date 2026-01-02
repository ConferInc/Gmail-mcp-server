"""Gmail OAuth2 Authentication."""

import os
import json
import logging
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(__name__)

BASE = Path(__file__).parent
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/gmail.compose"]

# Global flow storage for the manual auth process
_current_flow = None

def _get_paths():
    creds_file = os.environ.get("GMAIL_CREDENTIALS_PATH")
    token_file = os.environ.get("GMAIL_TOKEN_PATH")
    creds_path = Path(creds_file) if creds_file else BASE / "credentials.json"
    token_path = Path(token_file) if token_file else BASE / "token.json"
    return creds_path, token_path

def get_gmail_credentials():
    """
    Returns credentials if authorized, else returns None.
    Does NOT auto-trigger browser auth anymore.
    """
    # 1. OPTION A: Load from Env Content (Cloud / Docker friendly)
    if token_content := os.environ.get("GMAIL_TOKEN_CONTENT"):
        try:
            info = json.loads(token_content)
            return Credentials.from_authorized_user_info(info, SCOPES)
        except Exception as e:
            logger.error(f"Failed to load token from GMAIL_TOKEN_CONTENT: {e}")

    # 2. OPTION B: Load from File (Local)
    creds_path, token_path = _get_paths()
    creds = None
    
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except Exception:
            logger.warning("Corrupt token file found, ignoring.")
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                if not token_path.parent.exists():
                     token_path.parent.mkdir(parents=True, exist_ok=True)
                token_path.write_text(creds.to_json())
                return creds
            except Exception as e:
                logger.warning(f"Failed to refresh token: {e}")
        
        # If we reach here, we need full re-auth
        return None
    
    return creds

def get_auth_url():
    """Generates the Google Auth URL for the user to visit."""
    global _current_flow
    creds_path, _ = _get_paths()
    
    if not creds_path.exists():
         raise FileNotFoundError(f"credentials.json not found at {creds_path}")
         
    _current_flow = InstalledAppFlow.from_client_secrets_file(
        str(creds_path), SCOPES
    )
    # redirect_uri='urn:ietf:wg:oauth:2.0:oob' is special for manual copy-paste
    _current_flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
    
    auth_url, _ = _current_flow.authorization_url(prompt='consent')
    return auth_url

def finish_auth(code):
    """Exchanges the code for a token and saves it."""
    global _current_flow
    if not _current_flow:
        # Try to re-init flow if server restarted (best effort)
        # This will fail if creds_path is missing, but get_auth_url checks that.
        get_auth_url() 
        
    try:
        _current_flow.fetch_token(code=code)
        creds = _current_flow.credentials
        
        _, token_path = _get_paths()
        if not token_path.parent.exists():
            token_path.parent.mkdir(parents=True, exist_ok=True)
            
        token_path.write_text(creds.to_json())
        logger.info("New credentials saved to token file")
        return True, "Authentication successful! You can now use the tools."
    except Exception as e:
        logger.error(f"Auth failed: {e}")
        return False, str(e)

if __name__ == "__main__":
    c = get_gmail_credentials()
    if c:
        print("✅ Authenticated")
    else:
        print("❌ Not Authenticated. Run server tools to login.")
