"""
Pipeline orchestration: chain the four stages from a single seed domain.

No human touches the data between stages. The only gate is the safety
checkpoint immediately before Stage 4 sends.
"""
import logging
from typing import List, Optional

from .models import Contact
from .checkpoint import confirm_before_send
from .stages import ocean, prospeo, eazyreach, brevo

logger = logging.getLogger(__name__)


def dedupe(contacts: List[Contact]) -> List[Contact]:
    """
    Drop duplicate people that appear across multiple companies.
    
    Duplicates are identified by email > LinkedIn URL > name (in that order
    of preference). This prevents the same person from receiving multiple
    emails if they appear in results for multiple companies.
    """
    seen = set()
    unique: List[Contact] = []
    
    for c in contacts:
        # Use email as primary key if available, then LinkedIn URL, then name
        key = (c.email or c.linkedin_url or c.name or "").strip().lower()
        if not key:
            continue
        if key in seen:
            logger.debug("Deduped duplicate contact: %s", key)
            continue
        seen.add(key)
        unique.append(c)
    
    return unique


def run(
    domain: str,
    *,
    mock: bool = False,
    dry_run: bool = False,
    auto_yes: bool = False,
    max_companies: Optional[int] = None,
    max_contacts: Optional[int] = None
) -> int:
    """
    Run the full pipeline for one seed domain.
    
    Args:
        domain: The seed company domain (e.g., "stripe.com")
        mock: Use sample data instead of real API calls
        dry_run: Run every stage except the actual send
        auto_yes: Skip the confirmation prompt
        max_companies: Override the lookalike-company limit
        max_contacts: Override contacts-per-company limit
        
    Returns:
        Number of emails actually sent (0 on dry run, abort, or nothing sendable)
    """
    mode_label = "[MOCK MODE]" if mock else ""
    logger.info("=" * 60)
    logger.info("Seed domain: %s  %s", domain, mode_label)
    logger.info("=" * 60)

    # ─────────────────────────────────────────────────────────────────────
    # Stage 1 — Lookalike Companies (Ocean.io)
    # ─────────────────────────────────────────────────────────────────────
    logger.info("STAGE 1: Finding lookalike companies...")
    companies = ocean.find_lookalike_companies(
        domain,
        limit=max_companies,
        mock=mock
    )
    
    if not companies:
        logger.warning("No lookalike companies found. Stopping.")
        return 0
    logger.info("Stage 1 complete: %d companies found", len(companies))

    # ─────────────────────────────────────────────────────────────────────
    # Stage 2 — Decision-Makers (Prospeo)
    # ─────────────────────────────────────────────────────────────────────
    logger.info("STAGE 2: Finding decision-makers...")
    contacts = prospeo.find_decision_makers(
        companies,
        max_per_company=max_contacts,
        mock=mock
    )
    
    if not contacts:
        logger.warning("No decision-makers found. Stopping.")
        return 0
    logger.info("Stage 2 complete: %d contacts found", len(contacts))

    # ─────────────────────────────────────────────────────────────────────
    # Stage 3 — Verified Emails (Eazyreach)
    # ─────────────────────────────────────────────────────────────────────
    logger.info("STAGE 3: Resolving email addresses...")
    contacts = eazyreach.resolve_emails(contacts, mock=mock)
    
    # De-duplicate contacts that may appear across multiple companies
    contacts = dedupe(contacts)
    
    sendable = [c for c in contacts if c.is_sendable]
    logger.info(
        "Stage 3 complete: %d/%d contacts have verified emails",
        len(sendable), len(contacts)
    )

    # ─────────────────────────────────────────────────────────────────────
    # Safety Checkpoint — The one human gate
    # ─────────────────────────────────────────────────────────────────────
    if not confirm_before_send(contacts, dry_run=dry_run, auto_yes=auto_yes):
        logger.info("Stopped before sending.")
        return 0

    # ─────────────────────────────────────────────────────────────────────
    # Stage 4 — Send Outreach (Brevo)
    # ─────────────────────────────────────────────────────────────────────
    logger.info("STAGE 4: Sending outreach emails...")
    sent = brevo.send_outreach(contacts, mock=mock)
    
    logger.info("=" * 60)
    logger.info("Pipeline complete: %d emails sent", sent)
    logger.info("=" * 60)
    
    return sent
