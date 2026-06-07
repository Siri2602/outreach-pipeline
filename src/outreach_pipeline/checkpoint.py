"""
The safety checkpoint.

Before a single email is sent, print a clear summary of exactly who will be
contacted and require an explicit confirmation. This is the one human gate in
an otherwise fully automated pipeline.
"""
import logging
from typing import List

from .models import Contact

logger = logging.getLogger(__name__)


def format_summary(contacts: List[Contact]) -> str:
    """Generate a formatted summary string for the contacts."""
    sendable = [c for c in contacts if c.is_sendable]
    skipped = len(contacts) - len(sendable)
    companies = sorted({c.company_domain for c in sendable})
    
    lines = [
        "",
        "=" * 70,
        "  OUTREACH SUMMARY  —  review before anything is sent",
        "=" * 70,
        f"  Companies found:                {len(companies)}",
        f"  Total contacts discovered:      {len(contacts)}",
        f"  Sendable (verified email):      {len(sendable)}",
        f"  Skipped (missing/unverified):   {skipped}",
        "-" * 70,
    ]
    
    if sendable:
        lines.append("  Recipients:")
        for c in sendable:
            title = (c.title or "-")[:28]
            lines.append(f"    • {c.name:<24} {title:<28} {c.email}")
    else:
        lines.append("  No recipients with verified emails.")
    
    lines.append("=" * 70)
    return "\n".join(lines)


def confirm_before_send(
    contacts: List[Contact],
    *,
    dry_run: bool = False,
    auto_yes: bool = False
) -> bool:
    """
    Show the outreach summary and return True only if it's safe to send.

    Returns False (do not send) when there's nothing sendable, on a dry run,
    or when the user declines the prompt. ``auto_yes`` skips the prompt for
    non-interactive runs.
    """
    sendable = [c for c in contacts if c.is_sendable]
    
    # Print the summary
    print(format_summary(contacts))
    
    # Nothing to send
    if not sendable:
        print("  Nothing sendable. Exiting without sending.\n")
        return False

    # Dry run — show what would happen but don't send
    if dry_run:
        print("  DRY RUN — no emails will be sent.\n")
        return False

    # Auto-confirm for non-interactive runs
    if auto_yes:
        print("  --yes supplied; proceeding to send.\n")
        return True

    # Interactive confirmation
    try:
        answer = input(f"\n  Send {len(sendable)} email(s)? Type 'yes' to confirm: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n  Cancelled by user.\n")
        return False
    
    confirmed = answer == "yes"
    if not confirmed:
        print("  Not confirmed. Nothing was sent.\n")
    else:
        print()  # blank line before sending output
    
    return confirmed
