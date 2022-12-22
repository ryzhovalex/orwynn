from pytest import fixture
from orwynn.app import ErrorHandler

from orwynn.app._AppService import AppService
from orwynn.base.controller.Controller import Controller
from orwynn.base.error.Error import Error
from orwynn.base.module.Module import Module
from orwynn.base.test.HttpClient import HttpClient
from orwynn.boot._Boot import Boot
from orwynn.util.web import JSONResponse, Request, TestResponse


@fixture
def std_app(std_boot: Boot) -> AppService:
    return std_boot.app


def test_error_handler():
    class C1(Controller):
        ROUTE = "/"
        METHODS = ["get"]

        def get(self):
            raise Error("whoops!")

    class EH1(ErrorHandler):
        E = Error

        def handle(self, request: Request, error: Error):
            return JSONResponse(error.api, 400)

    boot: Boot = Boot(
        Module(route="/", Controllers=[C1]),
        ErrorHandlers=[EH1]
    )
    http: HttpClient = boot.app.http_client

    r: TestResponse = http.get("/", 400)
    print(r.json())
    assert False
