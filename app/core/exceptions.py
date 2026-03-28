from fastapi import HTTPException, status


class RapidAPIError(HTTPException):
    """Raised when the upstream RapidAPI returns an error."""

    def __init__(self, source: str, status_code: int, detail: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"[{source}] Upstream API error ({status_code}): {detail}",
        )
        self.source = source
        self.upstream_status = status_code


class RateLimitExceeded(HTTPException):
    """Raised when RapidAPI rate limit is hit (429)."""

    def __init__(self, source: str, retry_after: int | None = None):
        detail = f"[{source}] Rate limit exceeded."
        if retry_after:
            detail += f" Retry after {retry_after}s."
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
        )


class InvalidFilterCombination(HTTPException):
    """Raised when incompatible filters are used together."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )
