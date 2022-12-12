"""Standard app structure made up for testing.
"""
from orwynn.app.app_service import AppService
from orwynn.base.module.module import Module
from orwynn.di.objects.provider import Provider

from .number import NumberService, number_module
from .text import TextConfig, TextService, text_module

root_module = Module(
    route="/",
    imports=[text_module, number_module]
)


class Assertion:
    COLLECTED_MODULES: list[Module] = [
        root_module,
        text_module,
        number_module
    ]
    COLLECTED_PROVIDERS: list[type[Provider]] = [
        AppService,
        TextService,
        TextConfig,
        NumberService
    ]
