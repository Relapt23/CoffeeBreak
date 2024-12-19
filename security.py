import jwt
from typing import Optional
from models import Users, CustomException
from passlib.context import CryptContext

# Хэширование пароля
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "qwerty"
ALGORITHM = "HS256"


def make_jwt_token(username):
    return jwt.encode({"sub": username}, SECRET_KEY, algorithm=ALGORITHM)


def get_user_from_jwt_token(jwt_token: str) -> Optional[str]:
    try:
        payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except:
        return CustomException(detail="Ошибка получения JWT", status_code=400)