import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from pydantic.types import conint

class UserBase(BaseModel):
    email: EmailStr
    password : str

class CreateUser(UserBase):
    pass

class UserResponse(BaseModel):
    id : int
    email: EmailStr
    created_at : datetime.datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    user_name: str
    password : str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    id : Optional[int] = None
