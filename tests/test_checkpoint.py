"""Tests for the safety checkpoint."""
import pytest
from unittest.mock import patch
from outreach_pipeline.checkpoint import confirm_before_send, format_summary
from outreach_pipeline.models import Contact


def make_contacts():
    """Create sample contacts for testing."""
    return [
        Contact(
            name="John Doe",
            title="CEO",
            company_domain="example.com",
            company_name="Example Corp",
            email="john@example.com",
            email_verified=True,
        ),
        Contact(
            name="Jane Smith",
            title="VP Engineering",
            company_domain="another.com",
            company_name="Another Inc",
            email="jane@another.com",
            email_verified=True,
        ),
        Contact(
            name="Bob Wilson",
            title="CTO",
            company_domain="third.com",
            company_name="Third Co",
            email=None,  # No email - will be skipped
            email_verified=False,
        ),
    ]


class TestFormatSummary:
    def test_summary_includes_counts(self):
        contacts = make_contacts()
        summary = format_summary(contacts)
        
        assert "2" in summary  # 2 companies
        assert "3" in summary  # 3 total contacts
    
    def test_summary_includes_sendable_contacts(self):
        contacts = make_contacts()
        summary = format_summary(contacts)
        
        assert "John Doe" in summary
        assert "Jane Smith" in summary
        assert "john@example.com" in summary
    
    def test_summary_with_no_sendable(self):
        contacts = [
            Contact(name="Bob", email=None, email_verified=False),
        ]
        summary = format_summary(contacts)
        assert "No recipients" in summary


class TestConfirmBeforeSend:
    def test_dry_run_returns_false(self):
        contacts = make_contacts()
        result = confirm_before_send(contacts, dry_run=True)
        assert result is False
    
    def test_no_sendable_returns_false(self):
        contacts = [
            Contact(name="Bob", email=None, email_verified=False),
        ]
        result = confirm_before_send(contacts)
        assert result is False
    
    def test_auto_yes_returns_true(self):
        contacts = make_contacts()
        result = confirm_before_send(contacts, auto_yes=True)
        assert result is True
    
    def test_user_confirms_yes(self):
        contacts = make_contacts()
        with patch("builtins.input", return_value="yes"):
            result = confirm_before_send(contacts)
        assert result is True
    
    def test_user_declines(self):
        contacts = make_contacts()
        with patch("builtins.input", return_value="no"):
            result = confirm_before_send(contacts)
        assert result is False
    
    def test_user_empty_input(self):
        contacts = make_contacts()
        with patch("builtins.input", return_value=""):
            result = confirm_before_send(contacts)
        assert result is False
