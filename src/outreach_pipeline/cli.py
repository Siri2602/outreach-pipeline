"""
Command-line entry point.

Usage:
    outreach stripe.com --mock --dry-run        # see the whole flow, safely
    outreach stripe.com --dry-run               # real lookups, no send
    outreach stripe.com                          # real run, asks to confirm
    outreach --help

Equivalent to: python -m outreach_pipeline ...
"""
import sys
import logging
import argparse

from . import config, __version__
from .pipeline import run


def setup_logging(verbose: bool) -> None:
    """Configure logging format and level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-7s  %(message)s",
        datefmt="%H:%M:%S",
    )


def parse_args(argv=None) -> argparse.Namespace:
    """Parse command-line arguments."""
    p = argparse.ArgumentParser(
        prog="outreach",
        description="Automated cold-outreach pipeline: seed domain → lookalikes → decision-makers → emails sent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  outreach stripe.com --mock --dry-run   # Test with sample data, no sends
  outreach stripe.com --dry-run          # Real lookups, no sends
  outreach stripe.com                     # Real run with confirmation
  outreach stripe.com --yes              # Real run, skip confirmation
        """
    )
    
    p.add_argument(
        "domain",
        help="Seed company domain, e.g., stripe.com"
    )
    p.add_argument(
        "--mock",
        action="store_true",
        help="Use sample data instead of real API calls (no credits consumed)"
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Run every stage except the actual send"
    )
    p.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip the confirmation prompt (non-interactive)"
    )
    p.add_argument(
        "--max-companies",
        type=int,
        metavar="N",
        help=f"Override lookalike-company limit (default: {config.MAX_COMPANIES})"
    )
    p.add_argument(
        "--max-contacts",
        type=int,
        metavar="N",
        help=f"Override contacts-per-company limit (default: {config.MAX_CONTACTS_PER_COMPANY})"
    )
    p.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (debug) logging"
    )
    p.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    return p.parse_args(argv)


def main(argv=None) -> int:
    """Main entry point."""
    args = parse_args(argv)
    setup_logging(args.verbose)
    
    logger = logging.getLogger("pipeline")
    
    # Real runs need API keys; mock runs do not
    if not args.mock:
        missing = config.validate()
        if missing:
            logger.error(
                "Missing API keys in .env: %s\n"
                "Add them (see .env.example) or run with --mock for testing.",
                ", ".join(missing)
            )
            return 1
    
    try:
        sent = run(
            args.domain,
            mock=args.mock,
            dry_run=args.dry_run,
            auto_yes=args.yes,
            max_companies=args.max_companies,
            max_contacts=args.max_contacts,
        )
        
        # Return 0 on success (even if nothing was sent due to dry-run)
        return 0
        
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user.")
        return 130
    except Exception as exc:
        logger.error("Pipeline failed: %s", exc)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
