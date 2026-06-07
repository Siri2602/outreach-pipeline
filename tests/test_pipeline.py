"""Tests for the pipeline orchestration."""
import pytest
from unittest.mock import patch, MagicMock
from outreach_pipeline.pipeline import dedupe, run
from outreach_pipeline.models import Company, Contact


class TestDedupe:
    def test_dedupe_by_email(self):
        contacts = [
            Contact(name="John Doe", email="john@example.com"),
            Contact(name="John D.", email="john@example.com"),  # Duplicate
        ]
        result = dedupe(contacts)
        assert len(result) == 1
        assert result[0].name == "John Doe"
    
    def test_dedupe_by_linkedin(self):
        contacts = [
            Contact(name="John Doe", linkedin_url="https://linkedin.com/in/john"),
            Contact(name="John D.", linkedin_url="https://linkedin.com/in/john"),  # Duplicate
        ]
        result = dedupe(contacts)
        assert len(result) == 1
    
    def test_dedupe_by_name(self):
        contacts = [
            Contact(name="John Doe"),
            Contact(name="John Doe"),  # Duplicate
        ]
        result = dedupe(contacts)
        assert len(result) == 1
    
    def test_dedupe_case_insensitive(self):
        contacts = [
            Contact(name="John Doe", email="JOHN@example.com"),
            Contact(name="John D.", email="john@example.com"),  # Same email, different case
        ]
        result = dedupe(contacts)
        assert len(result) == 1
    
    def test_dedupe_preserves_order(self):
        contacts = [
            Contact(name="Alice", email="alice@example.com"),
            Contact(name="Bob", email="bob@example.com"),
            Contact(name="Charlie", email="charlie@example.com"),
        ]
        result = dedupe(contacts)
        assert len(result) == 3
        assert result[0].name == "Alice"
        assert result[1].name == "Bob"
        assert result[2].name == "Charlie"
    
    def test_dedupe_empty_list(self):
        result = dedupe([])
        assert result == []


class TestPipelineRun:
    def test_mock_run_dry_run(self):
        """Test that mock + dry-run executes all stages without sending."""
        with patch("outreach_pipeline.pipeline.brevo.send_outreach") as mock_send:
            mock_send.return_value = 0
            result = run("example.com", mock=True, dry_run=True)
        
        # Dry run should return 0 sent
        assert result == 0
        # send_outreach should not be called on dry run
        mock_send.assert_not_called()
    
    def test_mock_run_with_auto_yes(self):
        """Test mock run with auto-yes skips confirmation."""
        result = run("example.com", mock=True, auto_yes=True)
        # In mock mode with auto_yes, emails should be "sent"
        assert result > 0
    
    def test_pipeline_handles_no_companies(self):
        """Test that pipeline stops gracefully when no companies found."""
        with patch("outreach_pipeline.pipeline.ocean.find_lookalike_companies") as mock_ocean:
            mock_ocean.return_value = []
            result = run("example.com", mock=False, auto_yes=True)
        
        assert result == 0
    
    def test_pipeline_handles_no_contacts(self):
        """Test that pipeline stops gracefully when no contacts found."""
        with patch("outreach_pipeline.pipeline.ocean.find_lookalike_companies") as mock_ocean:
            with patch("outreach_pipeline.pipeline.prospeo.find_decision_makers") as mock_prospeo:
                mock_ocean.return_value = [Company(domain="test.com", name="Test")]
                mock_prospeo.return_value = []
                result = run("example.com", mock=False, auto_yes=True)
        
        assert result == 0
