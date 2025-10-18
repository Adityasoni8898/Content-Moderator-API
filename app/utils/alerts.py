from fastapi import logger
import requests

from app import config

SLACK_WEBHOOK_URL = config.settings.slack_webhook_url
BREVO_API_KEY = config.settings.brevo_api_key
BREVO_SENDER_EMAIL = config.settings.brevo_sender_email


def send_slack_alert(message: str):
    if not SLACK_WEBHOOK_URL:
        return
    payload = {"text": message}
    try:
        requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        logger.exception("Slack alert failed")


def send_mail_alert(to_email: str, subject: str, body: str):
    if not BREVO_API_KEY:
        return
    url = "https://api.brevo.com/v3/smtp/email"
    payload = {
        "sender": {"email": BREVO_SENDER_EMAIL},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": body
    }
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json"
    }
    try:
        requests.post(url, json=payload, headers=headers, timeout=5)
    except Exception as e:
        print(f"Email alert failed: {e}")


def send_alert(user_email: str, content_type: str, content_hash: str, llm_response: str):
    message = f"A new {content_type} was flagged as inappropriate. AI Analysis: {llm_response}"

    # Slack
    send_slack_alert(message)

    # Email
    send_mail_alert(
        to_email=user_email,
        subject=f"Inappropriate content detected ({content_type})",
        body=f"<p>{message}</p>"
    )