"""
Stage 1 — Ocean.io
Seed company domain  ->  list of lookalike companies.

API Documentation:
  - Base URL: https://api.ocean.io
  - Auth: Bearer token in Authorization header
  - Endpoint: POST /v1/companies/similar
  - Rate limits: Varies by plan

This stage takes a single seed domain and returns companies with similar
firmographics, size, and market positioning.
"""
import logging
from typing import List, Optional

from .. import config, http_client
from ..models import Company

logger = logging.getLogger(__name__)

OCEAN_BASE_URL = "https://api.ocean.io"


def find_lookalike_companies(
    seed_domain: str,
    *,
    limit: Optional[int] = None,
    mock: bool = False
) -> List[Company]:
    """
    Expand one seed domain into a list of similar companies.
    
    Args:
        seed_domain: The domain of a company to find lookalikes for (e.g., "stripe.com")
        limit: Maximum number of companies to return (defaults to MAX_COMPANIES)
        mock: If True, return sample data without calling the API
        
    Returns:
        List of Company objects with domain and name
    """
    limit = limit or config.MAX_COMPANIES
    
    if mock:
        return _mock(seed_domain, limit)

    logger.info("Stage 1 (Ocean.io): finding companies similar to %s", seed_domain)
    
    headers = {
        "Authorization": f"Bearer {config.OCEAN_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    
    # Ocean.io similar companies endpoint
    # The API accepts a company object with domain and returns ranked lookalikes
    payload = {
        "company": {
            "domain": seed_domain,
        },
        "limit": limit,
    }
    
    try:
        resp = http_client.post(
            f"{OCEAN_BASE_URL}/v1/companies/similar",
            headers=headers,
            json=payload,
        )
        data = resp.json()
    except http_client.APIError as e:
        logger.error("Ocean.io API error: %s", e)
        raise
    except Exception as e:
        logger.error("Failed to parse Ocean.io response: %s", e)
        raise http_client.APIError(f"Invalid response from Ocean.io: {e}")
    
    companies: List[Company] = []
    
    # Parse the response - Ocean.io returns results in a 'data' or 'companies' array
    # The exact structure may vary, so we try common patterns
    results = data.get("data") or data.get("companies") or data.get("results") or []
    
    if isinstance(results, dict):
        # Sometimes results are nested
        results = results.get("companies") or results.get("items") or []
    
    for item in results:
        if isinstance(item, dict):
            domain = item.get("domain") or item.get("website") or item.get("url", "")
            # Clean up domain - remove protocol and path
            domain = domain.replace("https://", "").replace("http://", "").split("/")[0]
            
            if not domain:
                continue
                
            name = item.get("name") or item.get("company_name") or item.get("companyName")
            companies.append(Company(domain=domain, name=name))
    
    logger.info("Stage 1 complete: found %d lookalike companies", len(companies))
    return companies[:limit]


def _mock(seed_domain: str, limit: int) -> List[Company]:
    """Return sample data for testing without API calls."""
    samples = [
        Company(domain="acme-analytics.com", name="Acme Analytics"),
        Company(domain="northwind-labs.io", name="Northwind Labs"),
        Company(domain="globex-data.com", name="Globex Data"),
        Company(domain="initech-ai.com", name="Initech AI"),
        Company(domain="umbrella-soft.io", name="Umbrella Soft"),
        Company(domain="hooli-tech.com", name="Hooli Tech"),
        Company(domain="piedpiper-systems.io", name="Pied Piper Systems"),
        Company(domain="aviato-corp.com", name="Aviato Corp"),
    ]
    out = samples[:limit]
    logger.info(
        "Stage 1 (MOCK): returning %d sample companies for seed %s",
        len(out), seed_domain
    )
    return out
