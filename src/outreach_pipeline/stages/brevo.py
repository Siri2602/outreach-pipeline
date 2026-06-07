"""
Stage 4 — Brevo
Verified contacts  ->  personalized outreach emails sent.

API Documentation:
  - Base URL: https://api.brevo.com
  - Auth: API key in 'api-key' header
  - Endpoint: POST /v3/smtp/email
  - Requires verified sender email in Brevo dashboard

This stage is the final step — it sends personalized transactional emails
to each contact with a verified email address.

Only contacts whose email was verified (Contact.is_sendable) are ever sent.
Each send is isolated so one undeliverable address doesn't stop the batch.
"""
import logging
from pathlib import Path
from typing import List

from .. import config, http_client
from ..models import Contact

logger = logging.getLogger(__name__)

BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"


def _load_template() -> str:
    """Read the outreach template from the templates directory."""
    template_path = Path(__file__).parent.parent / "templates" / "outreach.txt"
    try:
        return template_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        # Fallback template if file not found
        logger.warning("Template file not found, using fallback")
        return """Hi {first_name},

I came across {company} and thought of reaching out.

Would a quick 15-minute call next week make sense?

Best,
{sender_name}"""


def _render(template: str, contact: Contact) -> str:
    """Fill the template placeholders for a single contact."""
    return template.format(
        first_name=contact.first_name,
        full_name=contact.name,
        title=contact.title or "your team",
        company=contact.company_name or contact.company_domain,
        sender_name=config.SENDER_NAME,
    )


def send_outreach(contacts: List[Contact], *, mock: bool = False) -> int:
    """
    Send a personalized email to every sendable contact.
    
    Args:
        contacts: List of contacts (only those with is_sendable=True will be emailed)
        mock: If True, log what would be sent without actually sending
        
    Returns:
        Number of emails successfully sent
    """
    template = _load_template()
    sent = 0

    for contact in contacts:
        if not contact.is_sendable:
            continue

        body = _render(template, contact)
        subject = f"Quick idea for {contact.company_name or contact.company_domain}"

        if mock:
            logger.info(
                "Stage 4 (MOCK): would email %s <%s>",
                contact.name, contact.email
            )
            sent += 1
            continue

        try:
            # Convert plain text to HTML (simple line break conversion)
            html_body = body.replace("\n", "<br>\n")
            
            http_client.post(
                BREVO_SEND_URL,
                headers={
                    "api-key": config.BREVO_API_KEY,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json={
                    "sender": {
                        "name": config.SENDER_NAME,
                        "email": config.SENDER_EMAIL
                    },
                    "to": [{
                        "email": contact.email,
                        "name": contact.name
                    }],
                    "subject": subject,
                    "htmlContent": f"<html><body>{html_body}</body></html>",
                },
            )
            logger.info(
                "Stage 4 (Brevo): sent to %s <%s>",
                contact.name, contact.email
            )
            sent += 1
        except http_client.APIError as exc:
            # Resilience: keep sending the rest of the batch
            logger.warning(
                "Stage 4: failed to send to %s (%s)",
                contact.email, exc
            )
        except Exception as exc:
            logger.warning(
                "Stage 4: unexpected error sending to %s (%s)",
                contact.email, exc
            )

    return sent
