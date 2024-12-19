from fastapi import FastAPI, Depends, Query, Cookie
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from models import UserRegisterModel, Base, Users, CustomException, CountCoffeeCups
from sqlalchemy import MetaData, create_engine, select, insert, update
from sqlalchemy.orm import sessionmaker
from security import *
from fastapi.staticfiles import StaticFiles

app = FastAPI()
templates = Jinja2Templates(directory="templates")
metadata = MetaData()
engine = create_engine("sqlite:///database.db",echo=True)
sess = sessionmaker(engine)
app.mount("/static", StaticFiles(directory="static"), name="static")

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
async def register(user: UserRegisterModel = Depends(UserRegisterModel.as_form)):
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
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})



@app.post("/login", response_class=HTMLResponse)
async def login_form(user: UserRegisterModel = Depends(UserRegisterModel.as_form)):
    with sess() as session:
        jwt_token = make_jwt_token(user.username)
        res = session.execute(select(Users).where(Users.username == user.username)).scalar_one_or_none()        
        if not res:
            raise CustomException(detail="Неверное имя или пароль", status_code=404)        
        # Проверяем пароль
        if not pwd_context.verify(user.password, res.password):
            raise CustomException(detail="Неверное имя или пароль", status_code=404)
        session.commit()
        response = JSONResponse({"message": "Успешный вход"})
        response.set_cookie("jwt", jwt_token)
        return response


@app.get("/home", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/drink_coffee/", response_class=HTMLResponse)
async def count_cup(request: Request, jwt: Optional[str] = Cookie(None)):
    user = get_user_from_jwt_token(jwt)
    with sess() as session:
        user_info = session.execute(select(Users).where(user == Users.username)).scalar_one_or_none()
        res = session.execute(select(CountCoffeeCups).where(user_info.id == CountCoffeeCups.user_id)).scalar_one_or_none()
        if not res:
            session.execute(insert(CountCoffeeCups), {"user_id":user_info.id, "count_cups": 0})
            session.commit()
        session.execute(update(CountCoffeeCups).where(user_info.id == CountCoffeeCups.user_id).values(count_cups = CountCoffeeCups.count_cups + 1))
        session.commit()
        update_cups = session.execute(select(CountCoffeeCups.count_cups).where(user_info.id == CountCoffeeCups.user_id)).scalar_one()
    return templates.TemplateResponse(name="home.html", context={"request":request, "count_cups": update_cups})
