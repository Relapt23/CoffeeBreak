from fastapi import FastAPI, Depends, Cookie, Form, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from models import UserRegisterModel, Base, Users, CustomException
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
    with sess() as session:
        session.execute(insert(Users), {"username":"roma", "password":"$2b$12$.trlRGxiKQPMPml7Ao5o5u4HMWguv63Mfmfzn/9qp5TnrQ/81won2", "overview": None, "friends":[], "count_cups":0})
        session.execute(insert(Users), {"username":"tema", "password":"$2b$12$.trlRGxiKQPMPml7Ao5o5u4HMWguv63Mfmfzn/9qp5TnrQ/81won2", "overview": None, "friends":[], "count_cups":0})
        session.commit()

        
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
            session.execute(insert(Users), {"username": user.username, "password": hashed_password, "overview": None, "friends": [], "count_cups": 0})
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
        session.execute(update(Users).where(user == Users.username).values(count_cups = Users.count_cups + 1))
        session.commit()
        user_info = session.execute(select(Users).where(user == Users.username)).scalar_one_or_none()
    return templates.TemplateResponse(name="home.html", context={"request":request, "count_cups": user_info.count_cups})


@app.get("/about_me" , response_class=HTMLResponse)
async def my_profile( request: Request, jwt: Optional[str] = Cookie(None)):
    user = get_user_from_jwt_token(jwt)
    info_about_me = {}
    with sess() as session:
        info = session.execute(select(Users).where(user == Users.username)).scalar_one_or_none()
        info_about_me = {"username": info.username, "overview": info.overview, "friends": info.friends, "count_cups": info.count_cups}
        session.commit()
    return templates.TemplateResponse(name = "my_profile.html", context={"request": request, "info": info_about_me})


@app.post("/about_me/add_friends/", response_class=HTMLResponse)
async def add_friend(request: Request, friend_username: str = Form(...), jwt: Optional[str] = Cookie(None)):
    user = get_user_from_jwt_token(jwt)
    with sess() as session:
        res = session.execute(select(Users).where(Users.username == friend_username)).scalar_one_or_none()
        if res != None:
            if friend_username not in res.friends and friend_username != user:
                res.friends.append(friend_username)
                session.execute(update(Users).where(Users.username == user).values(friends = res.friends))
                session.commit()
    return RedirectResponse(url="/about_me", status_code=status.HTTP_303_SEE_OTHER)

