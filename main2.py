from fastapi import FastAPI, Depends, Query, Cookie
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from models import User, Base, Users, CustomException, CountCoffeeCups
from sqlalchemy import MetaData, create_engine, select, insert, update
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from typing import Optional

app = FastAPI()
templates = Jinja2Templates(directory="templates")
metadata = MetaData()
engine = create_engine("sqlite:///database.db",echo=True)
sess = sessionmaker(engine)

# Хэширование пароля
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")




def create_tables():
    engine.echo = False
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    engine.echo = True

        
create_tables()

@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
async def register(user: User = Depends(User.as_form)):
    hashed_password = pwd_context.hash(user.password)
    with sess() as session:
        query = select(Users)
        res = session.execute(query.where(Users.username == user.username)).scalar_one_or_none()
        if not res:
            session.execute(insert(Users), {"username":user.username, "password":hashed_password})
        else:
            raise CustomException(detail="Пользователь с таким именем уже существует, попробуйте другое имя", status_code=404)        
        session.commit()

@app.get("/login", response_class=HTMLResponse)
async def register_form(request: Request):
    response = templates.TemplateResponse("login.html", {"request": request})
    response.set_cookie('kek1', 'lol1')
    return response



@app.post("/login")
async def login(user: User = Depends(User.as_form)):
    with sess() as session:
        query = select(Users)
        res = session.execute(query.where(Users.username == user.username)).scalar_one_or_none()        
        if not res:
            raise CustomException(detail="Неверное имя или пароль", status_code=404)        
        # Проверяем пароль
        if not pwd_context.verify(user.password, res.password):
            raise CustomException(detail="Неверное имя или пароль", status_code=404)
        
        return {"message": f"Добро пожаловать, {user.username}"}


@app.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/drink_coffee/" response_class=HTMLResponse)
async def count_cup(request: Request, jwt):
    with sess() as session:
        query = select(CountCoffeeCups)
        res = session.execute(query.where(id == CountCoffeeCups.user_id)).scalars().all
        for item in res:
            count = item.count_cups + 1
            session.execute(update(CountCoffeeCups).where(id == CountCoffeeCups.id), {"count_cups": count})
        session.commit()
    return templates.TemplateResponse(name="home.html", context={"request":request, "count_cups": count})

# def make_jwt_token(user: Users) -> str:
#     ...

# def get_user_from_jwt_token(jwt_token: str) -> Optional[Users]:
#     ...