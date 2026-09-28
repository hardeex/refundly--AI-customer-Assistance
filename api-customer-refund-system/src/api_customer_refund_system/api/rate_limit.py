"""Rate limiting for the API. The refund-request endpoint is the one that calls
out to Anthropic, making it both the most expensive and the most abuse-prone
route in the system, so it gets its own tighter limit keyed by caller rather
than by IP (a tenant hitting us through a shared proxy shouldn't share a limit
with every other tenant behind that proxy).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request


def _caller_key(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    return authorization if authorization else get_remote_address(request)


limiter = Limiter(key_func=_caller_key)
