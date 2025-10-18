from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from app.utils import oauth2
from ..database import get_db
from .. import models
from ..services import moderate_services

router = APIRouter(
    prefix="/moderate", tags=["Moderate"]
)

@router.post("/text")
def moderate_text(
    text: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    return moderate_services.handle_text_moderation(text, db, current_user)


@router.post("/image")
async def moderate_image(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    return await moderate_services.handle_image_moderation(image, db, current_user)
