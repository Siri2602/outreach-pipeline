"""
The data contract for the whole pipeline.

Every stage speaks in terms of these two objects, which is what keeps each
stage a clean, independent unit:

    Stage 1 (Ocean.io)    -> produces  list[Company]
    Stage 2 (Prospeo)     -> produces  list[Contact]   (no email yet)
    Stage 3 (Eazyreach)   -> fills in   .email / .email_verified
    Stage 4 (Brevo)       -> sends to   contacts where .is_sendable is True
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Company:
    """A company found via lookalike search."""
    domain: str
    name: Optional[str] = None
    
    def __repr__(self) -> str:
        if self.name:
            return f"Company({self.name!r}, {self.domain!r})"
        return f"Company({self.domain!r})"


@dataclass
class Contact:
    """A decision-maker contact at a company."""
    name: str
    title: Optional[str] = None
    company_domain: str = ""
    company_name: Optional[str] = None
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    email_verified: bool = False

    @property
    def first_name(self) -> str:
        """Best-effort first name for personalizing email copy."""
        return self.name.split()[0] if self.name else "there"

    @property
    def is_sendable(self) -> bool:
        """We only ever email an address that exists AND was verified."""
        return bool(self.email) and self.email_verified
    
    def __repr__(self) -> str:
        email_status = "✓" if self.email_verified else "✗"
        return f"Contact({self.name!r}, {self.email or 'no email'} {email_status})"
