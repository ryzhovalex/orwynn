from typing import Callable
from fastapi import FastAPI
from starlette.types import Receive, Scope, Send
from orwynn.base.middleware.Middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware \
    as StarletteBaseHTTPMiddleware

from orwynn.base.service.framework_service import FrameworkService
from orwynn.base.test.TestClient import TestClient
from orwynn.util import validation
from orwynn.util.http import HTTPMethod


class AppService(FrameworkService):
    def __init__(self) -> None:
        self.__app: FastAPI = FastAPI()

        self.HTTP_METHODS_TO_REGISTERING_FUNCTIONS: \
            dict[HTTPMethod, Callable] = {
                HTTPMethod.GET: self.__app.get,
                HTTPMethod.POST: self.__app.post,
                HTTPMethod.PUT: self.__app.put,
                HTTPMethod.DELETE: self.__app.delete,
                HTTPMethod.PATCH: self.__app.patch,
                HTTPMethod.OPTIONS: self.__app.options
            }

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        await self.__app(scope, receive, send)

    @property
    def test_client(self) -> TestClient:
        return TestClient(self.__app)

    def add_middleware(self, middleware: Middleware) -> None:
        validation.validate(middleware, Middleware)
        self.__app.add_middleware(
            StarletteBaseHTTPMiddleware,
            dispatch=middleware.process
        )
