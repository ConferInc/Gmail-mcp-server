import json
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

# Resolve path to .env file relative to this script
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / '.env'
CREDENTIALS_FILE = BASE_DIR / 'credentials.json'

class EmailConfig(BaseSettings):
    """
    Configuration settings for the Email MCP Server.
    Reads from environment variables or .env file by default.
    Fallback to credentials.json if environment variables are missing.
    """
    model_config = SettingsConfigDict(env_file=str(ENV_FILE), env_file_encoding='utf-8', extra='ignore')

    # SMTP (Sending)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 465

    # IMAP (Receiving)
    IMAP_HOST: Optional[str] = None
    IMAP_PORT: int = 993

    # Credentials
    EMAIL_USER: Optional[str] = None
    EMAIL_PASS: Optional[str] = None
    
    # Deployment (Optional, for generating correct links)
    APP_URL: Optional[str] = None

    @property
    def is_configured(self) -> bool:
        """Check if essential config is present"""
        return all([self.SMTP_HOST, self.IMAP_HOST, self.EMAIL_USER, self.EMAIL_PASS])

    def load_from_file(self):
        """Attempt to load missing config from credentials.json"""
        if CREDENTIALS_FILE.exists():
            try:
                with open(CREDENTIALS_FILE, 'r') as f:
                    data = json.load(f)
                    # Only override if not already set (Env vars take precedence)
                    if not self.SMTP_HOST: self.SMTP_HOST = data.get("SMTP_HOST")
                    if not self.SMTP_PORT or self.SMTP_PORT == 465: self.SMTP_PORT = data.get("SMTP_PORT", 465)
                    if not self.IMAP_HOST: self.IMAP_HOST = data.get("IMAP_HOST")
                    if not self.IMAP_PORT or self.IMAP_PORT == 993: self.IMAP_PORT = data.get("IMAP_PORT", 993)
                    if not self.EMAIL_USER: self.EMAIL_USER = data.get("EMAIL_USER")
                    if not self.EMAIL_PASS: self.EMAIL_PASS = data.get("EMAIL_PASS")
            except Exception as e:
                print(f"Error loading credentials file: {e}")

    def save_to_file(self, smtp_host, smtp_port, imap_host, imap_port, email_user, email_pass):
        """Save configuration to credentials.json"""
        data = {
            "SMTP_HOST": smtp_host,
            "SMTP_PORT": smtp_port,
            "IMAP_HOST": imap_host,
            "IMAP_PORT": imap_port,
            "EMAIL_USER": email_user,
            "EMAIL_PASS": email_pass
        }
        with open(CREDENTIALS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Update current instance
        self.SMTP_HOST = smtp_host
        self.SMTP_PORT = smtp_port
        self.IMAP_HOST = imap_host
        self.IMAP_PORT = imap_port
        self.EMAIL_USER = email_user
        self.EMAIL_PASS = email_pass

# Instantiate config
try:
    config = EmailConfig()
    # Attempt to load from file if not fully configured via Env
    if not config.is_configured:
        config.load_from_file()
except Exception as e:
    print(f"Warning: Configuration loading failed: {e}")
    # Create an empty config so server doesn't crash on import
    # It will fail only when tools are called
    config = EmailConfig(SMTP_HOST=None, IMAP_HOST=None, EMAIL_USER=None, EMAIL_PASS=None)

