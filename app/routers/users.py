from ..database import get_db
from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from .. import models, schemas, utils

router = APIRouter(
    prefix="/users",
    tags=['User']
)

@router.post("/",  status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
async def create_user(user: schemas.CreateUser, db: Session = Depends(get_db)):
    
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()

    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail = "Email is already registered")

    user.password = utils.hash_password(user.password)

    db_user = models.User(
        email=user.email,
        hashed_password=user.password
    )
    db.add(db_user)
    db.commit()

    db.refresh(db_user) 
    return db_user

