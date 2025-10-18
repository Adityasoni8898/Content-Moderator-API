import base64
import re
import json
from perplexity import Perplexity
from app import config
from ..utils import security, alerts
from .. import models

client = Perplexity(api_key=config.settings.perplexity_api_key)

def handle_text_moderation(text, db, current_user):
    content_hash = security.hash_content(text.encode())

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
        alerts.send_alert(
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

    classification = "INAPPROPRIATE" if flagged else "SAFE"

    result = models.ModerationResult(
        request_id=request.id,
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
    # Read and hash image
    content_bytes = await image.read()
    content_hash = security.hash_content(content_bytes)

    # Create moderation request entry
    request = models.ModerationRequest(
        user_email=current_user.email,
        content_type="image",
        content_hash=content_hash,
        status="pending"
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    # Convert image to data URI
    base64_image = base64.b64encode(content_bytes).decode("utf-8")
    image_data_uri = f"data:{image.content_type};base64,{base64_image}"

    try:
        # Force structured, JSON-only response
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

        # Parse structured JSON safely
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

    # Save moderation result
    result = models.ModerationResult(
        request_id=request.id,
        classification=classification,
        confidence=confidence,
        reasoning=reasoning,
        llm_response=llm_response
    )
    db.add(result)

    # Handle flagged cases (alert + notification)
    if flagged:
        alerts.send_alert(
            user_email=current_user.email,
            content_type="image",
            content_hash=content_hash,
            llm_response=llm_response
        )
        notification_log = models.NotificationLog(
            request_id=request.id,
            channel="email and slack",
            status="success"
        )
        db.add(notification_log)

    # Mark request complete
    request.status = "completed"
    db.commit()
    db.refresh(request)

    return {
        "request_id": request.id,
        "classification": classification,
        "confidence": confidence,
        "reasoning": reasoning,
        "llm_response": llm_response
    }