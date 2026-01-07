import json
import logging

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

# Resolve path to .env file relative to this script
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / '.env'
CREDENTIALS_FILE = BASE_DIR / 'credentials.json'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        try:
            with open(CREDENTIALS_FILE, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.warning("Credentials file not found, starting fresh")
            data = {}
        except json.JSONDecodeError:
            logger.error("Invalid credentials file format")
            raise

        # Only override if not already set (Env vars take precedence)
        if not self.SMTP_HOST: self.SMTP_HOST = data.get("SMTP_HOST")
        if not self.SMTP_PORT or self.SMTP_PORT == 465: self.SMTP_PORT = data.get("SMTP_PORT", 465)
        if not self.IMAP_HOST: self.IMAP_HOST = data.get("IMAP_HOST")
        if not self.IMAP_PORT or self.IMAP_PORT == 993: self.IMAP_PORT = data.get("IMAP_PORT", 993)
        if not self.EMAIL_USER: self.EMAIL_USER = data.get("EMAIL_USER")
        if not self.EMAIL_PASS: self.EMAIL_PASS = data.get("EMAIL_PASS")

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
        CREDENTIALS_FILE.chmod(0o600)
        
        # Update current instance
        self.SMTP_HOST = smtp_host
        self.SMTP_PORT = smtp_port
        self.IMAP_HOST = imap_host
        self.IMAP_PORT = imap_port
        self.EMAIL_USER = email_user
        self.EMAIL_PASS = email_pass

# Instantiate config
config = EmailConfig()

# Attempt to load from file if not fully configured via Env
if not config.is_configured:
    try:
        config.load_from_file()
    except Exception as e:
        # If it's a critical error like JSONDecodeError, it might have been raised.
        # We allow it to bubble up to prevent partial/corrupt configuration.
        logger.error(f"Configuration loading failed: {e}")
        raise

