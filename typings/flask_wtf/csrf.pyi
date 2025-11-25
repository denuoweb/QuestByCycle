from typing import Any

from flask import Flask


class CSRFProtect:
    def __init__(self, app: Flask | None = None) -> None: ...
    def init_app(self, app: Flask) -> None: ...
    def exempt(self, view: Any) -> Any: ...


class CSRFError(Exception):
    description: str


def validate_csrf(
    data: Any,
    secret_key: str | None = None,
    time_limit: int | None = None,
    token_key: str | None = None,
) -> None: ...
