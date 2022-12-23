from typing import Iterable

from orwynn import (Boot, Controller, Model, Module, Service, crypto,
                    validation, endpoint, EndpointSpec)
from orwynn.mongo import MongoMapping


class UserCreate(Model):
    username: str
    ppassword: str


class User(MongoMapping):
    username: str
    hpassword: str


class Users(Model):
    users: list[User]


class UserService(Service):
    def __init__(self) -> None:
        super().__init__()

    def create(self, user: UserCreate) -> User:
        return User.create(
            username=user.username,
            hpassword=crypto.hash_password(user.ppassword)
        )

    def find(self, id: str) -> User:
        validation.validate(id, str)
        return User.find_one(id=id)

    def find_all(self) -> Iterable[User]:
        return User.find_all()


class UsersIdController(Controller):
    ROUTE = "/users/{id}"
    METHODS = ["get"]

    def __init__(self, sv: UserService) -> None:
        super().__init__()
        self.sv = sv

    @endpoint(EndpointSpec(
        ResponseModel=User
    ))
    def get(self, id: str) -> User:
        return self.sv.find(id)


class UsersController(Controller):
    ROUTE = "/users"
    METHODS = ["get", "post"]

    def __init__(self, sv: UserService) -> None:
        super().__init__()
        self.sv = sv

    @endpoint(EndpointSpec(
        ResponseModel=Users
    ))
    def get(self) -> Users:
        return Users(
            users=list(self.sv.find_all())
        )

    @endpoint(EndpointSpec(
        ResponseModel=User
    ))
    def post(self, user: UserCreate) -> User:
        return self.sv.create(user)


rm = Module(
    route="/",
    Providers=[UserService],
    Controllers=[UsersController, UsersIdController]
)


app = Boot(rm).app