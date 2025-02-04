from fastapi import Request, Response
from fastapi.responses import RedirectResponse

from fps.hooks import register_exception_handler
from fps.logging import get_configured_logger

logger = get_configured_logger("helloworld")


class RedirectException(Exception):
    def __init__(self, reason, redirect_to):
        self.reason = reason
        self.redirect_to = redirect_to


async def exception_handler(request: Request, exc: RedirectException) -> Response:
    logger.warning(f"'{exc.reason}' caused redirection to '{exc.redirect_to}'")
    return RedirectResponse(url=exc.redirect_to)


h = register_exception_handler(RedirectException, exception_handler)
