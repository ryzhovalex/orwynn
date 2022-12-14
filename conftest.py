"""Main framework-only testing suite.
"""
import contextlib
import os

from pytest import fixture

from orwynn.app.App import App
from orwynn.app.app_test import std_app
from orwynn.boot.Boot import Boot
from orwynn.boot.boot_test import run_std, std_boot, std_mongo_boot
from orwynn.boot.BootMode import BootMode
from orwynn.controller.endpoint.endpoint_test import run_endpoint
from orwynn.di.collecting.collect_modules_test import std_modules
from orwynn.di.collecting.collect_provider_dependencies_test import (
    std_provider_dependencies_map,
)
from orwynn.di.di_test import std_di_container
from orwynn.module.Module import Module
from orwynn.mongo.Mongo import Mongo
from orwynn.proxy.boot_data_proxy_test import std_boot_data_proxy
from orwynn.test.Client import Client
from orwynn.test.EmbeddedTestClient import EmbeddedTestClient
from orwynn.web.http_test import std_http
from orwynn.worker.Worker import Worker
from tests.structs import (
    circular_module_struct,
    long_circular_module_struct,
    self_importing_module_struct,
    std_struct,
)


@fixture(autouse=True)
def run_around_tests():
    yield

    # Suppress: Mongo is not initialized, skip
    with contextlib.suppress(TypeError):
        Mongo.ie().drop_database()
    __discardWorkers()

def __discardWorkers(W: type[Worker] = Worker):
    for NestedW in W.__subclasses__():
        __discardWorkers(NestedW)
    W.discard(should_validate=False)
    os.environ["Orwynn_Mode"] = ""
    os.environ["Orwynn_RootDir"] = ""
    os.environ["Orwynn_AppRcDir"] = ""
