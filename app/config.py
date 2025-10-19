from pydantic_settings import BaseSettings
import os

DOTENV = os.path.join(os.path.dirname(__file__), "../.env")

class Settings(BaseSettings):
    database_hostname: str
    database_port: int
    database_name: str
    database_username: str
    database_password: str
    secret_key: str
    algorithm: str
    access_token_expiry_minutes: int
    perplexity_api_key: str
    slack_webhook_url: str
    brevo_api_key: str
    brevo_sender_email: str

    class Config:
        env_file = DOTENV

settings = Settings()