"""
One shared HTTP helper used by every stage.

Centralizing requests here is what makes the pipeline resilient: rate limits
(HTTP 429) and transient server errors (5xx) are retried with exponential
backoff in a single place, so no individual stage has to think about it.
"""
import time
import logging
from typing import Optional, Any

import requests

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Raised when a request fails after exhausting all retries, or on a 4xx."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_text: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


def request(
    method: str,
    url: str,
    *,
    headers: Optional[dict] = None,
    params: Optional[dict] = None,
    json: Optional[Any] = None,
    max_retries: int = 4,
    backoff_base: float = 1.6,
    timeout: int = 30
) -> requests.Response:
    """
    Make an HTTP request, retrying on 429 and 5xx with exponential backoff.

    Honors the ``Retry-After`` header when the server sends one. Raises
    :class:`APIError` on a non-retryable client error (4xx other than 429) or
    after the retry budget is used up.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            resp = requests.request(
                method, url,
                headers=headers,
                params=params,
                json=json,
                timeout=timeout
            )
        except requests.RequestException as exc:
            if attempt > max_retries:
                raise APIError(
                    f"{method} {url} failed after {max_retries} retries: {exc}"
                )
            wait = backoff_base ** attempt
            logger.warning(
                "Network error (%s). Retry %d/%d in %.1fs",
                exc, attempt, max_retries, wait
            )
            time.sleep(wait)
            continue

        # Retry on rate limit or server error
        if resp.status_code == 429 or resp.status_code >= 500:
            if attempt > max_retries:
                raise APIError(
                    f"{method} {url} -> {resp.status_code} after {max_retries} retries",
                    status_code=resp.status_code,
                    response_text=resp.text[:500]
                )
            # Honor Retry-After header if present
            retry_after = resp.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                wait = float(retry_after)
            else:
                wait = backoff_base ** attempt
            logger.warning(
                "HTTP %d on %s. Retry %d/%d in %.1fs",
                resp.status_code, url, attempt, max_retries, wait
            )
            time.sleep(wait)
            continue

        # Non-retryable client error
        if resp.status_code >= 400:
            raise APIError(
                f"{method} {url} -> {resp.status_code}: {resp.text[:300]}",
                status_code=resp.status_code,
                response_text=resp.text[:500]
            )

        return resp


def get(url: str, **kwargs) -> requests.Response:
    """Make a GET request with retry logic."""
    return request("GET", url, **kwargs)


def post(url: str, **kwargs) -> requests.Response:
    """Make a POST request with retry logic."""
    return request("POST", url, **kwargs)
