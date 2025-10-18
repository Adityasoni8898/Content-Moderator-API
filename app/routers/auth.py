from ..utils import oauth2
from ..database import get_db
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import models, schemas, utils

router = APIRouter(
    tags=['Auth']
)

@router.post("/login", response_model=schemas.TokenResponse)
def user_login(user_cred: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_cred.username).first()

    if not user:
        user = db.query(models.User).filter(models.User.user_name == user_cred.username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")

    if not utils.verify_password(user_cred.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN , detail="Invalid credentials")

    access_token = oauth2.create_access_token(data={"user_id" : user.id})

    return {"access_token": access_token, "token_type": "bearer"}