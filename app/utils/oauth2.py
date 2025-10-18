from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from .. import schemas, database, models
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from ..config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

SECRET = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expiry_minutes

def create_access_token(data: dict):
    to_encode = data.copy()
    
    expire = datetime.now(timezone.utc) + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)

def verify_access_token(token:str, credential_expection):
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
        payload_id: str = payload.get("user_id")
        if  payload_id is None:
            raise credential_expection
        token_data = schemas.TokenPayload(id = payload_id)
        return token_data
    except JWTError:
        raise credential_expection
    
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credential_exception = HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    
    token = verify_access_token(token, credential_exception)
    user = db.query(models.User).filter(models.User.id == token.id).first()
    return user