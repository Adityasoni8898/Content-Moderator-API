from .database import Base
from sqlalchemy import TIMESTAMP, Column, ForeignKey, Integer, String, text

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False) 

class ModerationRequest(Base):
    __tablename__ = "moderation_requests"
    id = Column(Integer, primary_key=True, nullable=False)
    user_email = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    content_hash = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)

class ModerationResult(Base):
    __tablename__ = "moderation_results"
    request_id = Column(Integer, ForeignKey("moderation_requests.id", ondelete="CASCADE"), primary_key=True)
    classification = Column(String, nullable=False)
    confidence = Column(String)
    reasoning = Column(String)
    llm_response = Column(String)

class NotificationLog(Base):
    __tablename__ = "notification_logs"
    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey("moderation_requests.id", ondelete="CASCADE"))
    channel = Column(String)
    status = Column(String)
    sent_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)