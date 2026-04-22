# 用户模型

import uuid
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, JSON


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    name: str
    token_balance: int = Field(default=100)  # 初始100 Token
    is_active: bool = Field(default=True)


class User(UserBase, table=True):
    __tablename__ = "users"

    id: int = Field(primary_key=True, default=None)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class UserCreate(SQLModel):
    email: str
    password: str
    name: str


class UserLogin(SQLModel):
    email: str
    password: str


class UserResponse(SQLModel):
    id: int
    email: str
    name: str
    token_balance: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: str  # user_id
    exp: datetime
