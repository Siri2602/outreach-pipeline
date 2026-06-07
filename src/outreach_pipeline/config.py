"""
Configuration: API keys come from the environment (.env), never hardcoded.
Also holds demo-friendly default limits so a live run stays fast and cheap.
"""
import os

from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# --- API keys (set these in .env; see .env.example) ---
OCEAN_API_KEY = os.getenv("OCEAN_API_KEY", "")
PROSPEO_API_KEY = os.getenv("PROSPEO_API_KEY", "")
EAZYREACH_API_KEY = os.getenv("EAZYREACH_API_KEY", "")
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")

# --- Sender identity for outreach (must be a verified sender in Brevo) ---
SENDER_NAME = os.getenv("SENDER_NAME", "Your Name")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "you@yourdomain.com")

# --- Volume limits: keep a live demo quick and credit-light ---
MAX_COMPANIES = int(os.getenv("MAX_COMPANIES", "5"))
MAX_CONTACTS_PER_COMPANY = int(os.getenv("MAX_CONTACTS_PER_COMPANY", "2"))


def validate() -> list[str]:
    """Return the list of required API keys that are missing."""
    required = {
        "OCEAN_API_KEY": OCEAN_API_KEY,
        "PROSPEO_API_KEY": PROSPEO_API_KEY,
        "EAZYREACH_API_KEY": EAZYREACH_API_KEY,
        "BREVO_API_KEY": BREVO_API_KEY,
    }
    return [key for key, value in required.items() if not value]


def get_summary() -> dict:
    """Return a summary of current configuration (for debugging)."""
    return {
        "ocean_key_set": bool(OCEAN_API_KEY),
        "prospeo_key_set": bool(PROSPEO_API_KEY),
        "eazyreach_key_set": bool(EAZYREACH_API_KEY),
        "brevo_key_set": bool(BREVO_API_KEY),
        "sender_name": SENDER_NAME,
        "sender_email": SENDER_EMAIL,
        "max_companies": MAX_COMPANIES,
        "max_contacts_per_company": MAX_CONTACTS_PER_COMPANY,
    }
