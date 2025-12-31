"""Gmail OAuth2 Authentication."""

from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

BASE = Path(__file__).parent
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/gmail.compose"]


def get_gmail_credentials():
    token_path, creds_path = BASE / "token.json", BASE / "credentials.json"
    creds = None
    
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                raise FileNotFoundError(f"credentials.json not found at {creds_path}")
            creds = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES).run_local_server(port=0)
        token_path.write_text(creds.to_json())
    
    return creds


if __name__ == "__main__":
    try:
        get_gmail_credentials()
        print("\n✅ Authentication successful! Token saved to token.json")
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
