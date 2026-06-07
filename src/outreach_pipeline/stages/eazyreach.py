"""
Stage 3 — Eazyreach
LinkedIn profile URL  ->  verified work email.

API Documentation:
  - Base URL: https://api.eazyreach.app
  - Auth: Bearer token in Authorization header  
  - Endpoint: POST /v1/resolve
  - Input: LinkedIn profile URL
  - Output: Verified work email

Each contact is resolved in its own try/except, and a contact with no
LinkedIn URL is skipped rather than treated as an error.
"""
import logging
from typing import List

from .. import config, http_client
from ..models import Contact

logger = logging.getLogger(__name__)

EAZYREACH_BASE_URL = "https://api.eazyreach.app"


def resolve_emails(contacts: List[Contact], *, mock: bool = False) -> List[Contact]:
    """
    Fill in .email and .email_verified on each contact, in place.
    
    Args:
        contacts: List of contacts with LinkedIn URLs
        mock: If True, use mock data without calling the API
        
    Returns:
        The same list of contacts with email fields populated
    """
    for index, contact in enumerate(contacts):
        if not contact.linkedin_url:
            logger.warning(
                "Stage 3: %s has no LinkedIn URL, skipping",
                contact.name
            )
            continue
            
        try:
            if mock:
                # Mark roughly one in three as unverified so the checkpoint's
                # "skipped" path is visible in a mock run
                _mock_resolve(contact, verified=(index % 3 != 2))
            else:
                _resolve(contact)
        except Exception as exc:
            # Resilience: a failed lookup shouldn't crash the whole pipeline
            logger.warning(
                "Stage 3: could not resolve %s (%s)",
                contact.name, exc
            )

    return contacts


def _resolve(contact: Contact) -> None:
    """Resolve a single contact's LinkedIn URL to an email via Eazyreach API."""
    headers = {
        "Authorization": f"Bearer {config.EAZYREACH_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    payload = {
        "linkedin_url": contact.linkedin_url,
    }
    
    try:
        resp = http_client.post(
            f"{EAZYREACH_BASE_URL}/v1/resolve",
            headers=headers,
            json=payload,
        )
        data = resp.json()
    except http_client.APIError as e:
        logger.warning("Eazyreach API error for %s: %s", contact.name, e)
        return
    except Exception as e:
        logger.warning("Failed to parse Eazyreach response for %s: %s", contact.name, e)
        return
    
    # Extract email from response
    # Eazyreach may return email in various fields
    email = (
        data.get("email") or
        data.get("work_email") or
        data.get("business_email") or
        data.get("data", {}).get("email")
    )
    
    if email:
        contact.email = email
        
        # Check verification status
        # Different APIs report this differently
        status = (
            data.get("status") or
            data.get("verification_status") or
            data.get("verified") or
            data.get("data", {}).get("status")
        )
        
        # Consider email verified if status indicates success
        if isinstance(status, bool):
            contact.email_verified = status
        elif isinstance(status, str):
            contact.email_verified = status.lower() in (
                "verified", "valid", "success", "deliverable", "true"
            )
        else:
            # If no explicit status, assume verified if we got an email
            contact.email_verified = True
            
        logger.info(
            "Stage 3 (Eazyreach): %s -> %s (verified=%s)",
            contact.name, contact.email, contact.email_verified
        )
    else:
        logger.warning(
            "Stage 3 (Eazyreach): no email found for %s",
            contact.name
        )


def _mock_resolve(contact: Contact, *, verified: bool) -> None:
    """Generate mock email data for testing."""
    # Create a realistic-looking email from the contact's name and company
    handle = contact.name.lower().replace(" ", ".")
    domain = contact.company_domain or "example.com"
    
    contact.email = f"{handle}@{domain}"
    contact.email_verified = verified
    
    logger.info(
        "Stage 3 (MOCK): %s -> %s (verified=%s)",
        contact.name, contact.email, verified
    )
