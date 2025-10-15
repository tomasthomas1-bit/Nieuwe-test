from pydantic import BaseModel, Field, conint

class UserPublic(BaseModel):
    id: int
    username: str
    name: str | None = None
    age: conint(ge=18, le=99) | None = None
    bio: str | None = None

class UserUpdate(BaseModel):
    name: str | None = None
    age: conint(ge=18, le=99) | None = None
    bio: str | None = None
``
