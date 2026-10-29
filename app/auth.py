#password security 
from datetime import datetime,timedelta,timezone
import jwt
from app.config import settings
from pwdlib import PasswordHash
password_hash= PasswordHash.recommended()
def hash_password(password:str)->str:
    return password_hash.hash(password)
def verify_password(plain_password:str,hashed_password:str)->bool:
    return password_hash.verify(plain_password,hashed_password)
def create_access_token(user_id:int)->str:
    now=datetime.now(timezone.utc)
    expires_at=now+timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload={
        "sub":str(user_id),
        "iat":now,
        "exp":expires_at,
    }
    return jwt.encode(
        payload,settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )