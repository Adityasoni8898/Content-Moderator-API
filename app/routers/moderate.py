import base64
from fastapi import APIRouter, UploadFile, File, Form, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.utils import oauth2, security
from ..database import get_db
from .. import models
from ..services import moderate_services

router = APIRouter(
    prefix="/moderate", tags=["Moderate"]
)

@router.post("/text")
def moderate_text(
    background_tasks: BackgroundTasks,
    text: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    request = moderate_services.create_text_request(text, db, current_user)
    background_tasks.add_task(
        moderate_services.handle_text_moderation,
        request.id, text, db, current_user
    )
    return {"status": "processing", "request_id": request.id}


@router.post("/image")
async def moderate_image(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    content_bytes = await image.read()
    content_hash = security.hash_content(content_bytes)

    request = models.ModerationRequest(
        user_email=current_user.email,
        content_type="image",
        content_hash=content_hash,
        status="pending"
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    base64_image = base64.b64encode(content_bytes).decode("utf-8")
    image_data_uri = f"data:{image.content_type};base64,{base64_image}"

    background_tasks.add_task(
        moderate_services.handle_image_moderation,
        request.id,
        image_data_uri,
        db,
        current_user
    )

    return {"status": "processing", "request_id": request.id}
