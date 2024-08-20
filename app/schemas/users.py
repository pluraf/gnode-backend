from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    username: str
    is_admin: bool


class UserCreate(UserBase):
    password: str


# For security reasons, password not added to User
class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class UserAuth(User):
    hashed_password: str
