from fastapi import FastAPI, Depends, Query, Cookie
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from models import User, Base, Users, CustomException, CountCoffeeCups
from sqlalchemy import MetaData, create_engine, select, insert, update
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from typing import Optional
import jwt

app = FastAPI()
templates = Jinja2Templates(directory="templates")
metadata = MetaData()
engine = create_engine("sqlite:///database.db",echo=True)
sess = sessionmaker(engine)

# Хэширование пароля
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "qwerty"
ALGORITHM = "HS256"




def make_jwt_token(data):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def get_user_from_jwt_token(jwt_token: str) -> Optional[Users]:
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except:
        return CustomException(detail="Ошибка получения JWT", status_code=400)




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
            session.execute(insert(Users), {"username":user.username, "password":hashed_password, "JWT_token": ''})
        else:
            raise CustomException(detail="Пользователь с таким именем уже существует, попробуйте другое имя", status_code=404)        
        session.commit()

@app.get("/login", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})



@app.post("/login", response_class=HTMLResponse)
async def login(user: User = Depends(User.as_form)):
    with sess() as session:
        query = select(Users)
        res = session.execute(query.where(Users.username == user.username)).scalar_one_or_none()        
        if not res:
            raise CustomException(detail="Неверное имя или пароль", status_code=404)        
        # Проверяем пароль
        if not pwd_context.verify(user.password, res.password):
            raise CustomException(detail="Неверное имя или пароль", status_code=404)
        jwt_token = make_jwt_token({"sub": user.username})
        session.execute(update(Users).where(user.username == Users.username), {"JWT_token": jwt_token})
        response = JSONResponse({"message": "Успешный вход"})
        response.set_cookie("jwt", jwt_token)
        session.commit()
        return response


@app.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/drink_coffee/", response_class=HTMLResponse)
async def count_cup(request: Request, jwt: Optional[str] = Cookie(None)):
    user = get_user_from_jwt_token(jwt)
    print(user)
    with sess() as session:
        query = select(Users)
        user_info = session.execute(query.where(user == Users.username)).scalar_one_or_none()
        query = select(CountCoffeeCups)
        res = session.execute(query.where(user_info.id == CountCoffeeCups.user_id)).scalar_one_or_none()
        if not res:
            session.execute(insert(CountCoffeeCups), {"user_id":user_info.id, "count_cups": 0})
        res.count_cups += 1
        session.execute(update(CountCoffeeCups).where(user_info.id == CountCoffeeCups.user_id), {"count_cups": res.count_cups})
        session.commit()
    return templates.TemplateResponse(name="home.html", context={"request":request, "count_cups": res.count_cups})
