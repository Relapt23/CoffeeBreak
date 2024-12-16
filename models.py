from pydantic import BaseModel
from sqlalchemy.orm import sessionmaker, Session, mapped_column, Mapped, DeclarativeBase, relationship
from fastapi import HTTPException, Form
from sqlalchemy import Table, Column, Integer, String, ForeignKey

class UserRegisterModel(BaseModel):
    username: str
    password: str

    @classmethod
    def as_form(
        cls,
        username: str = Form(...),
        password: str = Form(...),
    ):
        return cls(username=username, password=password)

class Base(DeclarativeBase):
    pass

# пользователи
class Users(Base):
    __tablename__ = "users"
    id: Mapped [int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str]
    password: Mapped[str]
    jwt_token: Mapped[str]

class CountCoffeeCups(Base):
    __tablename__ = "coffee_cups"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    count_cups: Mapped[int]

class CustomException(HTTPException):
    def __init__(self, detail: str, status_code: int = 404):
        super().__init__(status_code=status_code, detail=detail)