from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database.database import get_db
from models.user import User
import os
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer
import uuid
import logging

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 移除OAuth2PasswordBearer因为我们使用cookie
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")  # 添加默认值
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # 添加默认值
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))  # 添加默认值

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

logger = logging.getLogger(__name__)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_token_from_cookie(request: Request) -> Optional[str]:
    authorization = request.cookies.get("access_token")
    if not authorization:
        return None
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        return token
    except:
        return None

def get_guest_user(db: Session) -> User:
    """获取或创建游客账户"""
    guest_id = str(uuid.uuid4())
    guest_user = User(
        id=guest_id,
        username=f"guest_{guest_id[:8]}",
        email=f"guest_{guest_id[:8]}@temp.com",
        is_guest=True
    )
    db.add(guest_user)
    db.commit()
    db.refresh(guest_user)
    logger.info(f"创建游客账户: {guest_user.username}")
    return guest_user

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """获取当前用户，如果未登录则返回游客账户"""
    if not token:
        return get_guest_user(db)
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# 创建一个可重用的依赖
get_current_user = get_current_user 