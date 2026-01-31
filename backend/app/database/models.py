
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base

class Feedback(Base):
    """ORM model for feedback records."""
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class Email(Base):
    """Store fetched and summarized emails."""
    __tablename__ = "emails"

    email_id = Column(String, primary_key=True, index=True)  # Gmail message ID
    user_email = Column(String, nullable=False, index=True)
    sender = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    body = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    priority = Column(String, default="Medium")
    category = Column(String, default="Uncategorized")
    thread_id = Column(String)
    smart_thread_id = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_archived = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    attachments = relationship("EmailAttachment", back_populates="email")


class EmailAttachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(String, ForeignKey("emails.email_id"))
    filename = Column(String)
    mime_type = Column(String)
    size = Column(Integer)
    attachment_id = Column(String, unique=True, index=True)

    email = relationship("Email", back_populates="attachments")


class EmailReply(Base):
    __tablename__ = "email_replies"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(String, ForeignKey("emails.email_id"), index=True)
    user_email = Column(String, index=True)
    reply_text = Column(String)
    tone = Column(String)
    is_auto = Column(Boolean, default=False)
    sent_at = Column(DateTime, server_default=func.now())


class EmailDraft(Base):
    __tablename__ = "email_drafts"

    id = Column(Integer, primary_key = True)
    email_id = Column(String, index = True)
    user_email = Column(String, index=True)
    draft_text = Column(String)
    tone = Column(String)
    updated_at = Column(DateTime, server_default=func.now(), onupdate = func.now())


class UserSummary(Base):
    __tablename__ = "user_summaries"

    user_email = Column(String, primary_key=True, index=True)
    summary = Column(String)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EmailTask(Base):
    """Store action items extracted from emails."""
    __tablename__ = "email_tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email_id = Column(String, ForeignKey("emails.email_id"), index=True)
    user_email = Column(String, index=True)
    task_text = Column(String, nullable=False)
    deadline = Column(DateTime, nullable=True)
    source = Column(String, default="ai")
    created_at = Column(DateTime, server_default=func.now())
    completed = Column(Boolean, default=False)
    calendar_event_id = Column(String, nullable=True)
