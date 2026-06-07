"""Tests for the data models."""
import pytest
from outreach_pipeline.models import Company, Contact


class TestCompany:
    def test_company_with_name(self):
        c = Company(domain="example.com", name="Example Corp")
        assert c.domain == "example.com"
        assert c.name == "Example Corp"
    
    def test_company_without_name(self):
        c = Company(domain="example.com")
        assert c.domain == "example.com"
        assert c.name is None
    
    def test_company_repr_with_name(self):
        c = Company(domain="example.com", name="Example Corp")
        assert "Example Corp" in repr(c)
        assert "example.com" in repr(c)
    
    def test_company_repr_without_name(self):
        c = Company(domain="example.com")
        assert "example.com" in repr(c)


class TestContact:
    def test_contact_basic(self):
        c = Contact(
            name="John Doe",
            title="CEO",
            company_domain="example.com",
            company_name="Example Corp",
            linkedin_url="https://linkedin.com/in/johndoe",
            email="john@example.com",
            email_verified=True,
        )
        assert c.name == "John Doe"
        assert c.title == "CEO"
        assert c.email == "john@example.com"
        assert c.email_verified is True
    
    def test_first_name_extraction(self):
        c = Contact(name="John Doe")
        assert c.first_name == "John"
        
        c2 = Contact(name="Madonna")
        assert c2.first_name == "Madonna"
        
        c3 = Contact(name="")
        assert c3.first_name == "there"
    
    def test_is_sendable_verified(self):
        c = Contact(name="John", email="john@example.com", email_verified=True)
        assert c.is_sendable is True
    
    def test_is_sendable_unverified(self):
        c = Contact(name="John", email="john@example.com", email_verified=False)
        assert c.is_sendable is False
    
    def test_is_sendable_no_email(self):
        c = Contact(name="John", email_verified=True)
        assert c.is_sendable is False
    
    def test_is_sendable_empty_email(self):
        c = Contact(name="John", email="", email_verified=True)
        assert c.is_sendable is False
