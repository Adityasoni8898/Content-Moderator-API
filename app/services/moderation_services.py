import base64
from fastapi import logger
from typing import Tuple, Dict, Any
from sqlalchemy.orm import Session
from app import models
from app.utils import alerts
from app.config import settings
from perplexity import Perplexity

_perplexity_client = Perplexity(api_key=settings.perplexity_api_key)

def _classify_from_response(llm_text: str) -> Tuple[bool, str, float, str]:
    lower = (llm_text or "").lower()

    safe_signals = ["appropriate", "safe", "no issues", "no inappropriate", "not inappropriate", "clean"]
    inappropriate_signals = ["inappropriate", "nsfw", "sexual", "porn", "hate", "violence", "illegal", "abuse"]

    for sig in inappropriate_signals:
        if sig in lower:
            return True, "inappropriate", 0.9, f"Detected marker '{sig}' in LLM response"

    for sig in safe_signals:
        if sig in lower:
            return False, "safe", 0.9, "LLM explicitly marked content as safe"

    return False, "safe", 0.5, "LLM response unclear; defaulting to safe"

def _persist_notification_log(db: Session, request_id: int, channel: str, status: str = "success") -> None:
    log = models.NotificationLog(
        request_id=request_id,
        channel=channel,
        status=status
    )
    db.add(log)
    db.commit()
    db.refresh(log)

def moderate_text_and_persist(db: Session, user_email: str, text: str) -> Dict[str, Any]:
    content_hash = models.__dict__.get 
    content_hash = __import__("hashlib").sha256(text.encode()).hexdigest()

    request = models.ModerationRequest(
        user_email=user_email,
        content_type="text",
        content_hash=content_hash,
        status="pending"
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    try:
        completion = _perplexity_client.chat.completions.create(
            model="sonar-pro",
            messages=[{"role": "user", "content": f"Moderate this text for inappropriate content: {text}"}]
        )
        llm_response = completion.choices[0].message.content
    except Exception as e:
        logger.exception("Perplexity API error: %s", e)
        llm_response = f"Error calling Perplexity API: {str(e)}"

    flagged, classification, confidence, reasoning = _classify_from_response(llm_response)

    result = models.ModerationResult(
        request_id=request.id,
        classification=classification,
        confidence=str(confidence),
        reasoning=reasoning,
        llm_response=llm_response
    )
    db.add(result)

    # update request status
    request.status = "completed"
    db.commit()
    db.refresh(result)
    db.refresh(request)

    # alerts if necessary
    if flagged:
        try:
            alerts.send_alert(
                user_email=user_email,
                content_type="text",
                content_hash=content_hash,
                llm_response=llm_response
            )
        except Exception:
            logger.exception("Failed to send alerts after flagged moderation")

        try:
            _persist_notification_log(db, request.id, channel="email and slack", status="success")
        except Exception:
            logger.exception("Failed to persist notification log")

    return {
        "request_id": request.id,
        "classification": classification,
        "confidence": confidence,
        "reasoning": reasoning,
        "llm_response": llm_response
    }

def moderate_image_and_persist(db: Session, user_email: str, content_bytes: bytes, content_type_header: str) -> Dict[str, Any]:
    """
    Workflow for moderating images. Accepts raw bytes and a content type (like "image/jpeg").
    """
    # compute hash
    import hashlib
    content_hash = hashlib.sha256(content_bytes).hexdigest()

    # create request
    request = models.ModerationRequest(
        user_email=user_email,
        content_type="image",
        content_hash=content_hash,
        status="pending"
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    # prepare data uri
    try:
        b64 = base64.b64encode(content_bytes).decode("utf-8")
        image_data_uri = f"data:{content_type_header};base64,{b64}"
    except Exception:
        image_data_uri = None

    # call LLM
    try:
        messages_payload = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Moderate this image for inappropriate content."}
                ]
            }
        ]
        if image_data_uri:
            messages_payload[0]["content"].append({"type": "image_url", "image_url": {"url": image_data_uri}})

        completion = _perplexity_client.chat.completions.create(
            model="sonar-pro",
            messages=messages_payload
        )
        llm_response = completion.choices[0].message.content
    except Exception as e:
        logger.exception("Perplexity API error for image: %s", e)
        llm_response = f"Error calling Perplexity API: {str(e)}"

    flagged, classification, confidence, reasoning = _classify_from_response(llm_response)

    # persist result
    result = models.ModerationResult(
        request_id=request.id,
        classification=classification,
        confidence=str(confidence),
        reasoning=reasoning,
        llm_response=llm_response
    )
    db.add(result)

    # alerts if necessary
    if flagged:
        try:
            alerts.send_alert(
                user_email=user_email,
                content_type="image",
                content_hash=content_hash,
                llm_response=llm_response
            )
        except Exception:
            logger.exception("Failed to send alerts after flagged image")

        try:
            _persist_notification_log(db, request.id, channel="email and slack", status="success")
        except Exception:
            logger.exception("Failed to persist notification log")

    # update request status and commit
    request.status = "completed"
    db.commit()
    db.refresh(result)
    db.refresh(request)

    return {
        "request_id": request.id,
        "classification": classification,
        "confidence": confidence,
        "reasoning": reasoning,
        "llm_response": llm_response
    }