import copy
from types import NoneType

from orwynn.app.empty_route_error import EmptyRouteError
from orwynn.base.controller.controller import Controller
from orwynn.base.middleware import middleware
from orwynn.base.module.framework_service_module_reference_error import \
    FrameworkServiceModuleReferenceError
from orwynn.base.service.framework_service import FrameworkService
from orwynn.di.is_provider import is_provider
from orwynn.di.not_provider_error import NotProviderError
from orwynn.di.provider import Provider
from orwynn.util.validation.validation import validate, validate_route


class Module:
    """Provides metadata to organize the application structure.

    Attributes:
        route:
            All controllers defined under this module will
            operate under this route. Route cannot be "/" to be distinguishable
            from other modules.
        Providers (optional):
            List of Providers to be initialized and shared at least across this
            module.
        Controllers (optional):
            List of Controllers to be initialized for this module.
        Middleware (optional):
            List of Middleware classes applied to all module' controllers.
        imports (optional):
            List of imported modules to use their exported providers in this
            module.
        exports (optional):
            Sublist of providers that are provided by this module for other
            modules importing this module. It cannot contain provider not
            referenced in `providers` field.

    Usage:
    ```py
    # medieval_module.py

    medieval_module = Module(
        Providers=[KingService, KnightService, KingConfig],
        Controllers=[KingController, KnightController],
        Middleware=[BlessingMiddleware],
        imports=[castle_module],
        exports=[KingService, KingConfig]
    )
    ```
    """
    def __init__(
        self,
        *,
        route: str,
        Providers: list[type[Provider]] | None = None,
        Controllers: list[type[Controller]] | None = None,
        Middleware: list[type[middleware.Middleware]] | None = None,
        imports: list["Module"] | None = None,
        exports: list[type[Provider]] | None = None
    ) -> None:
        super().__init__()
        validate(route, str)
        validate(Providers, [list, NoneType])
        validate(Controllers, [list, NoneType])
        validate(Middleware, [list, NoneType])
        validate(imports, [list, NoneType])
        validate(exports, [list, NoneType])

        self._ROUTE: str = self._parse_route(route)
        self._Providers: list[type[Provider]] = self._parse_providers(
            Providers
        )
        self._Controllers: list[type[Controller]] = self._parse_controllers(
            Controllers
        )
        self._Middleware: list[type[middleware.Middleware]] = \
            self._parse_middleware(Middleware)
        self._imports: list["Module"] = self._parse_imports(imports)
        # TODO: Add check if exports present in Providers
        self._exports: list[type[Provider]] = self._parse_providers(Providers)

    def __repr__(self) -> str:
        return "<{} \"{}\" at {}>".format(
            self.__class__.__name__,
            self.ROUTE,
            hex(id(self))
        )

    @property
    def ROUTE(self) -> str:
        return self._ROUTE

    @property
    def Providers(self) -> list[type[Provider]]:
        return copy.copy(self._Providers)

    @property
    def Controllers(self) -> list[type[Controller]]:
        return copy.copy(self._Controllers)

    @property
    def Middleware(self) -> list[type[middleware.Middleware]]:
        return copy.copy(self._Middleware)

    @property
    def imports(self) -> list["Module"]:
        return copy.copy(self._imports)

    @property
    def exports(self) -> list[type[Provider]]:
        return copy.copy(self._exports)

    @staticmethod
    def _parse_route(route: str) -> str:
        if route:
            validate_route(route)
        else:
            raise EmptyRouteError()

        return route

    def _parse_providers(
        self,
        Providers: list[type[Provider]] | None
    ) -> list[type[Provider]]:
        res: list[type[Provider]]

        if Providers:
            for P in Providers:
                if not is_provider(P):
                    raise NotProviderError(FailedClass=P)
                if issubclass(P, FrameworkService):
                    raise FrameworkServiceModuleReferenceError(
                        f"framework service {P} is referenced in"
                        f" the module {self}"
                    )
            res = Providers
        else:
            res = []

        return res

    @staticmethod
    def _parse_controllers(
        Controllers: list[type[Controller]] | None
    ) -> list[type[Controller]]:
        res: list[type[Controller]]

        if Controllers:
            for Controller_ in Controllers:
                validate(Controller_, Controller)
                # Rest validation done by controller itself
            res = Controllers
        else:
            res = []

        return res

    @staticmethod
    def _parse_middleware(
        Middleware: list[type[middleware.Middleware]] | None
    ) -> list[type[middleware.Middleware]]:
        res: list[type[middleware.Middleware]]

        if Middleware:
            for Middleware_ in Middleware:
                validate(Middleware_, middleware.Middleware)
            res = Middleware
        else:
            res = []

        return res

    @staticmethod
    def _parse_imports(
        imports: list["Module"] | None
    ) -> list["Module"]:
        res: list["Module"]

        if imports:
            for import_ in imports:
                validate(import_, Module)
            res = imports
        else:
            res = []

        return res
