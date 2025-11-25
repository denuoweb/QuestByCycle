from typing import Any, Callable, TypeVar

from flask.typing import ResponseReturnValue

_F = TypeVar("_F", bound=Callable[..., Any])


class LoginManager:
    login_view: str | None

    def __init__(self, app: Any | None = None) -> None: ...
    def init_app(self, app: Any) -> None: ...
    def unauthorized_handler(
        self, callback: Callable[..., ResponseReturnValue]
    ) -> Callable[..., ResponseReturnValue]: ...
    def user_loader(self, callback: Callable[[str | int | None], Any]) -> Callable[[str | int | None], Any]: ...


current_user: Any


def login_user(user: Any, remember: bool = ..., duration: Any | None = ..., force: bool = ..., fresh: bool = ...) -> bool: ...
def logout_user() -> None: ...


def login_required(func: _F) -> _F: ...
