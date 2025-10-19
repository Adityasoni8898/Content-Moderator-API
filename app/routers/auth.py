from ..utils import oauth2, security
from ..database import get_db
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import models, schemas

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

    if not security.verify_password(user_cred.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN , detail="Invalid credentials")

    access_token = oauth2.create_access_token(data={"user_id" : user.id})

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/signup",  status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
async def create_user(user: schemas.CreateUser, db: Session = Depends(get_db)):
    
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail = "Email is already registered")

    user.password = security.hash_password(user.password)

    db_user = models.User(
        email=user.email,
        hashed_password=user.password
    )
    db.add(db_user)
    db.commit()

    db.refresh(db_user) 
    return db_user