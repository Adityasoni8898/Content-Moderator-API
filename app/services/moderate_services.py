import base64
from perplexity import Perplexity
from app import config, utils
from .. import models

client = Perplexity(api_key=config.settings.perplexity_api_key)

def handle_text_moderation(text, db, current_user):
    content_hash = utils.hash_content(text.encode())

    request = models.ModerationRequest(
        user_email=current_user.email,
        content_type="text",
        content_hash=content_hash,
        status="pending"
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    try:
        completion = client.chat.completions.create(
            model="sonar-pro",
            messages=[{"role": "user", "content": f"Moderate this text for inappropriate content: {text}"}]
        )
        llm_response = completion.choices[0].message.content.lower()

        if any(word in llm_response for word in ["appropriate", "safe", "no issues", "not contain inappropriate"]):
            flagged = False
            classification = "safe"
            reasoning = "No issues detected"
            confidence = 0.9
        elif "inappropriate" in llm_response or "nsfw" in llm_response:
            flagged = True
            classification = "inappropriate"
            reasoning = "Detected inappropriate content"
            confidence = 0.9
        else:
            flagged = False
            classification = "safe"
            reasoning = "LLM response unclear, defaulting to safe"
            confidence = 0.5
    except Exception as e:
        llm_response = f"Error calling Perplexity API: {str(e)}"
        flagged = False
        classification = "safe"
        reasoning = "LLM moderation failed"
        confidence = 0.0

    result = models.ModerationResult(
        request_id=request.id,
        classification=classification,
        confidence=str(confidence),
        reasoning=reasoning,
        llm_response=llm_response
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    request.status = "completed"
    db.commit()
    db.refresh(request)

    if flagged:
        utils.send_alert(
            user_email=current_user.email,
            content_type="text",
            content_hash=content_hash,
            llm_response=llm_response
        )
        status = "success"
        notification_log = models.NotificationLog(
            request_id=request.id,
            channel="email and slack",
            status=status
        )
        db.add(notification_log)
        db.commit()
        db.refresh(notification_log)

    return {
        "request_id": request.id,
        "classification": classification,
        "confidence": confidence,
        "reasoning": reasoning
    }


async def handle_image_moderation(image, db, current_user):
    content_bytes = await image.file.read()
    content_hash = utils.hash_content(content_bytes)

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

    try:
        completion = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Moderate this image for inappropriate content."},
                        {"type": "image_url", "image_url": {"url": image_data_uri}}
                    ]
                }
            ]
        )
        llm_response = completion.choices[0].message.content
        flagged = "inappropriate" in llm_response.lower()
    except Exception as e:
        llm_response = str(e)
        flagged = False

    classification = "inappropriate" if flagged else "safe"

    result = models.ModerationResult(
        request_id=request.id,
        classification=classification,
        confidence="0.9",
        reasoning="Detected inappropriate content" if flagged else "No issues detected",
        llm_response=llm_response
    )
    db.add(result)

    if flagged:
        utils.send_alert(
            user_email=current_user.email,
            content_type="image",
            content_hash=content_hash,
            llm_response=llm_response
        )
        status = "success"
        notification_log = models.NotificationLog(
            request_id=request.id,
            channel="email and slack",
            status=status
        )
        db.add(notification_log)
        db.commit()
        db.refresh(notification_log)

    request.status = "completed"
    db.commit()
    db.refresh(request)

    return {
        "request_id": request.id,
        "classification": classification,
        "confidence": "0.9",
        "llm_response": llm_response
    }