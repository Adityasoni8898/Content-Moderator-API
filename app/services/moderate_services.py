import base64
import re
import json
from perplexity import Perplexity
from app import config
from ..utils import security, alerts
from .. import models

client = Perplexity(api_key=config.settings.perplexity_api_key)

def create_text_request(text, db, user):
    request = models.ModerationRequest(
        user_email=user.email,
        content_type="text",
        content_hash=security.hash_content(text.encode()),
        status="pending"
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


async def create_image_request(image, db, user):
    content_bytes = await image.read()
    request = models.ModerationRequest(
        user_email=user.email,
        content_type="image",
        content_hash=security.hash_content(content_bytes),
        status="pending"
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def handle_text_moderation(request_id, text, db, current_user):

    try:
        system_prompt = """You are a strict content moderation model.
        Classify the following text into one of the categories:
        - SAFE: No sexual, violent, hateful, or inappropriate content.
        - INAPPROPRIATE: Contains or implies NSFW, sexual, hateful, or violent content.

        Respond in strict JSON only:
        {
        "classification": "SAFE" | "INAPPROPRIATE",
        "reasoning": "short reason",
        "confidence": float between 0 and 1
        }
        """
        completion = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0
        )

        llm_response = completion.choices[0].message.content.strip()

        json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            classification = result.get("classification", "SAFE").upper()
            reasoning = result.get("reasoning", "No reasoning provided")
            confidence = float(result.get("confidence", 0.9))
        else:
            classification = "SAFE"
            reasoning = "LLM returned unstructured response"
            confidence = 0.5

        flagged = classification == "INAPPROPRIATE"

    except Exception as e:
        flagged = False
        classification = "SAFE"
        reasoning = f"Moderation failed: {e}"
        confidence = 0.0


    request = db.query(models.ModerationRequest).get(request_id)
    content_hash = request.content_hash

    result = models.ModerationResult(
        request_id=request_id,
        classification=classification,
        confidence=confidence,
        reasoning=reasoning,
        llm_response=llm_response
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    request.status = "completed"
    db.commit()

    if flagged:
        alerts.send_alert(
            user_email=current_user.email,
            content_type="text",
            content_hash=content_hash,
            llm_response=llm_response
        )
        notification_log = models.NotificationLog(
            request_id=request_id,
            channel="email and slack",
            status="success"
        )
        db.add(notification_log)
        db.commit()

    return {
        "request_id": request_id,
        "classification": classification,
        "confidence": confidence,
        "reasoning": reasoning
    }


async def handle_image_moderation(request_id, image_data_uri, db, current_user):
    try:
        system_prompt = """You are a strict image moderation model.
        Classify the given image into one of these categories:
        - SAFE: No nudity, sexual, violent, hateful, or NSFW content.
        - INAPPROPRIATE: Contains or implies any NSFW, sexual, violent, or hateful elements.

        Respond in strict JSON only:
        {
        "classification": "SAFE" | "INAPPROPRIATE",
        "reasoning": "short explanation",
        "confidence": float between 0 and 1
        }
        """
        completion = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this image for inappropriate or NSFW content."},
                        {"type": "image_url", "image_url": {"url": image_data_uri}}
                    ]
                }
            ],
            temperature=0
        )
        llm_response = completion.choices[0].message.content.strip()

        json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            classification = result.get("classification", "SAFE").upper()
            reasoning = result.get("reasoning", "No reasoning provided")
            confidence = float(result.get("confidence", 0.9))
        else:
            classification = "SAFE"
            reasoning = "Unstructured LLM response"
            confidence = 0.5

        flagged = classification == "INAPPROPRIATE"

    except Exception as e:
        llm_response = f"Error during moderation: {str(e)}"
        classification = "SAFE"
        reasoning = "Moderation failed, defaulting to safe"
        confidence = 0.0
        flagged = False

    request = db.query(models.ModerationRequest).get(request_id)
    content_hash = request.content_hash

    result = models.ModerationResult(
        request_id=request_id,
        classification=classification,
        confidence=confidence,
        reasoning=reasoning,
        llm_response=llm_response
    )
    db.add(result)

    if flagged:
        alerts.send_alert(
            user_email=current_user.email,
            content_type="image",
            content_hash=content_hash,
            llm_response=llm_response
        )
        notification_log = models.NotificationLog(
            request_id=request_id,
            channel="email and slack",
            status="success"
        )
        db.add(notification_log)

    request.status = "completed"
    db.commit()

    return {
        "request_id": request_id,
        "classification": classification,
        "confidence": confidence,
        "reasoning": reasoning,
        "llm_response": llm_response
    }