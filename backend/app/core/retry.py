"""Retry utilities using tenacity."""
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


def retry_on_transient(max_attempts: int = 3, min_wait: float = 1.0, max_wait: float = 10.0):
    """Decorator: retry on any exception with exponential backoff."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        reraise=True,
    )


def retry_on_http_error(max_attempts: int = 3):
    """Retry on network/HTTP errors."""
    import httpx
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=2, max=16),
        retry=retry_if_exception_type((httpx.HTTPError, ConnectionError, TimeoutError)),
        reraise=True,
    )
