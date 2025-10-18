from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.utils import oauth2
from app.database import get_db
from app import models

router = APIRouter(
    tags=["Analytics"]
)

@router.get("/summary")
def analytics_summary(
    user: str = Query(..., description="Email of the user to get analytics for"),
    current_user: models.User = Depends(oauth2.get_current_user),
    db: Session = Depends(get_db)
):
    user_exists = db.query(models.User).filter(models.User.email == user).first()
    if not user_exists:
        raise HTTPException(status_code=404, detail="User not found")

    total_requests = db.query(func.count(models.ModerationRequest.id))\
                       .filter(models.ModerationRequest.user_email == user)\
                       .scalar()
    
    total_results = db.query(func.count(models.ModerationResult.request_id))\
                      .join(models.ModerationRequest, models.ModerationResult.request_id == models.ModerationRequest.id)\
                      .filter(models.ModerationRequest.user_email == user)\
                      .scalar()

    safe_count = db.query(func.count(models.ModerationResult.request_id))\
                   .join(models.ModerationRequest, models.ModerationResult.request_id == models.ModerationRequest.id)\
                   .filter(models.ModerationRequest.user_email == user, models.ModerationResult.classification == "SAFE")\
                   .scalar()

    inappropriate_count = db.query(func.count(models.ModerationResult.request_id))\
                            .join(models.ModerationRequest, models.ModerationResult.request_id == models.ModerationRequest.id)\
                            .filter(models.ModerationRequest.user_email == user, models.ModerationResult.classification == "INAPPROPRIATE")\
                            .scalar()

    return {
        "total_requests": total_requests,
        "total_results": total_results,
        "safe_count": safe_count,
        "inappropriate_count": inappropriate_count
    }