from genericpath import isfile
import os
from pathlib import Path
import re

import dotenv

from orwynn.app.AppService import AppService
from orwynn.base.controller.Controller import Controller
from orwynn.base.database.DatabaseKind import DatabaseKind
from orwynn.base.database.UnknownDatabaseKindError import \
    UnknownDatabaseKindError
from orwynn.base.error.malfunction_error import MalfunctionError
from orwynn.base.indication.default_api_indication import \
    default_api_indication
from orwynn.base.indication.Indication import Indication
from orwynn.base.module.Module import Module
from orwynn.base.worker.Worker import Worker
from orwynn.boot.AppRC import AppRC
from orwynn.boot.ApprcSearchError import AppRCSearchError
from orwynn.boot.BootDataProxy import BootDataProxy
from orwynn.boot.BootMode import BootMode
from orwynn.boot.UnknownSourceError import UnknownSourceError
from orwynn.boot.UnsupportedBootModeError import UnsupportedBootModeError
from orwynn.di.DI import DI
from orwynn.mongo.Mongo import Mongo
from orwynn.mongo.MongoConfig import MongoConfig
from orwynn.util.file.NotDirError import NotDirError
from orwynn.util.file.yml import load_yml
from orwynn.util.http.http import HTTPMethod
from orwynn.util.validation import validate


class Boot(Worker):
    """Worker responsible of booting an application.

    General usage is to construct this class in the main.py with required
    parameters and then access Boot.app for your needs.

    Attributes:
        root_module:
            Root module of the app.
        dotenv_path (optional):
            Path to .env file. Defaults to ".env".
        api_indication (optional):
            Indication object used as a convention for outcoming API
            structures. Defaults to predefined by framework's indication
            convention.
        databases (optional):
            List of database kinds enabled.

    Environs:
        Orwynn_Mode:
            Boot mode for application. Defaults to DEV.
        Orwynn_RootDir:
            Root directory for application. Defaults to os.getcwd()
        Orwynn_AppRCDir:
            Directory where application configs is located. Defaults to root
            directory.

    Usage:
    ```py
    # main.py
    from orwynn import Boot, AppModeEnum, AppService, MongoService

    # Import root module from your location
    from .myproject.root_module import root_module

    app = Boot(
        mode=AppModeEnum.DEV,
        root_module=root_module
    ).app
    ```
    """
    def __init__(
        self,
        root_module: Module,
        *,
        dotenv_path: Path | None = None,
        api_indication: Indication | None = None,
        databases: list[DatabaseKind] | None = None
    ) -> None:
        super().__init__()
        if dotenv_path is None:
            dotenv_path = Path(".env")
        validate(dotenv_path, Path)
        validate(root_module, Module)
        if not api_indication:
            api_indication = default_api_indication
        validate(api_indication, Indication)

        dotenv.load_dotenv(dotenv_path, override=True)

        self.__mode: BootMode = self.__parse_mode()
        self.__root_dir: Path = self.__parse_root_dir()
        self.__api_indication: Indication = api_indication
        self.__app_rc: AppRC = self.__parse_app_rc(
            self.__root_dir,
            self.__mode
        )

        BootDataProxy(
            root_dir=self.__root_dir,
            mode=self.__mode,
            api_indication=self.__api_indication,
            app_rc=self.__app_rc
        )

        if databases is None:
            databases = []
        else:
            validate(databases, list)

        # FIXME:
        #   Add AppService to be always initialized - THIS IS VERY BAD approach
        #   and is breaking many principles, so fix it ASAP.
        #
        #   Case is, that if no acceptor/module in the app requires AppService,
        #   it won't be included at all.
        root_module._Providers.append(AppService)

        self._di: DI = DI(root_module)

        self.__register_routes(self._di.modules, self._di.controllers)

    @property
    def app(self) -> AppService:
        return self._di.app_service

    @property
    def api_indication(self) -> Indication:
        return self.__api_indication

    def __register_routes(
        self, modules: list[Module], controllers: list[Controller]
    ) -> None:
        for m in modules:
            for C in m.Controllers:
                self.__register_controller_class_for_module(m, C, controllers)

    def __register_controller_class_for_module(
        self,
        m: Module,
        C: type[Controller],
        controllers: list[Controller]
    ) -> None:
        is_controller_found: bool = False
        for c in controllers:
            if type(c) is C:
                is_controller_found = True
                self.__register_controller_for_module(c, m)
        if not is_controller_found:
            raise MalfunctionError(
                f"no initialized controller found for class {C},"
                f" but it was declared in imported module {m},"
                " so DI should have been initialized it"
            )

    def __register_controller_for_module(
        self,
        c: Controller,
        m: Module
    ) -> None:
        # At least one method found
        is_method_found: bool = False
        for http_method in HTTPMethod:
            # Don't register unused methods
            if http_method in c.methods:
                is_method_found = True
                if c.ROUTE is None:
                    raise MalfunctionError(
                        f"route of controller {c.__class__} is None"
                        " but check should have been performed at"
                        " class instance initialization"
                    )

                joined_route: str
                if m.ROUTE == "/":
                    joined_route = c.ROUTE
                else:
                    joined_route = m.ROUTE + c.ROUTE

                self.app.register_route_fn(
                    # We can concatenate routes such way since routes
                    # are validated to not contain following slash
                    route=joined_route,
                    fn=c.get_fn_by_http_method(http_method),
                    method=http_method
                )

        if not is_method_found:
            raise MalfunctionError(
                f"no http methods found for controller {c.__class__},"
                " this shouldn't have passed validation at Controller.__init__"
            )

    def __parse_mode(self) -> BootMode:
        mode_env: str | None = os.getenv("Orwynn_Mode")

        if not mode_env:
            return BootMode.DEV
        else:
            return self._parse_mode_from_str(mode_env)

    def __parse_root_dir(self) -> Path:
        root_dir: Path
        root_dir_env: str | None = os.getenv("Orwynn_RootDir")

        if not root_dir_env:
            root_dir = Path(os.getcwd())
        else:
            root_dir = Path(root_dir_env)

        if not root_dir.is_dir():
            raise NotDirError(
                f"{root_dir} is not a directory"
            )

        return root_dir

    def __parse_app_rc(self, root_dir: Path, mode: BootMode) -> AppRC:
        rc_env: str | None = os.getenv(
            "Orwynn_AppRCDir",
            None
        )

        if rc_env is None:
            return {}
        elif Path(rc_env).exists():
            rc_dir: Path = Path(rc_env)
            if not rc_dir.is_dir():
                raise NotDirError(
                    f"{rc_dir} is not a directory"
                )
            return self.__load_appropriate_app_rc(rc_dir, mode)
        elif (
            rc_env.startswith("http://")
            or rc_env.startswith("https://")
        ):
            raise NotImplementedError("URL sources are not yet implemented")
        else:
            raise UnknownSourceError(
                f"unknown source {rc_env}"
            )

    def __load_appropriate_app_rc(self, rc_dir: Path, mode: BootMode) -> AppRC:
        for f in rc_dir.iterdir():
            prelast_suffix, last_suffix = f.suffixes[len(f.suffixes)-2:]
            if (
                re.match(r"^apprc\..+\..+$", f.name.lower())
                and prelast_suffix.lower() == "." + mode.value.lower()
                and last_suffix.lower() in [".yml", ".yaml"]
            ):
                return load_yml(rc_dir)

        raise AppRCSearchError(
            f"cannot find apprc in directory {rc_dir}"
        )

    @staticmethod
    def _parse_mode_from_str(mode: str) -> BootMode:
        match mode:
            case "test":
                return BootMode.TEST
            case  "dev":
                return BootMode.DEV
            case  "prod":
                return BootMode.PROD
            case _:
                raise UnsupportedBootModeError("unsupported mode {mode}")

    def __enable_databases(self, database_kinds: list[DatabaseKind]) -> None:
        for kind in database_kinds:
            match kind:
                case DatabaseKind.MONGO:
                    Mongo(
                        config=MongoConfig.load()
                    )
                case DatabaseKind.POSTRGRESQL:
                    raise NotImplementedError(
                        "postgresql database currently not supported"
                    )
                case _:
                    raise UnknownDatabaseKindError(
                        f"unknown database kind {kind}"
                    )
