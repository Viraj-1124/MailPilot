from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.exc import IntegrityError
from app.database.models import Email, EmailAttachment, UserSummary, EmailDraft, EmailReply, Feedback, User

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, email: str):
    user = User(email=email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def save_email(db: Session, email_id, user_email, sender, subject, body, summary, priority, category, thread_id, smart_thread_id, attachments, timestamp, is_read=False):
    try:
        stmt = insert(Email).values(
            email_id=email_id,
            user_email=user_email,
            sender=sender,
            subject=subject,
            body=body,
            summary=summary,
            priority=priority,
            category=category,
            thread_id=thread_id,
            smart_thread_id=smart_thread_id,
            timestamp=timestamp,
            is_read=is_read
        ).on_conflict_do_nothing(
            index_elements=['email_id']  # UNIQUE column
        )

        db.execute(stmt)

        for att in attachments:
            att_stmt = insert(EmailAttachment).values(
                email_id=email_id,
                filename=att["filename"],
                mime_type=att["mime_type"],
                size=att["size"],
                attachment_id=att["attachment_id"]
            ).on_conflict_do_nothing(
                index_elements=['attachment_id']  # unique key
            )
            db.execute(att_stmt)

        db.commit()

    except IntegrityError:
        db.rollback()
        print(f"[UPSERT SKIPPED] Email {email_id} already exists")
    except Exception as e:
        db.rollback()
        print(f"Error saving email: {e}")

def update_email_priority(db: Session, email_id: str, new_priority: str):
    email_obj = db.query(Email).filter(Email.email_id == email_id).first()
    if email_obj:
        email_obj.priority = new_priority
        db.commit()

def get_user_summary(db: Session, user_email: str):
    return db.query(UserSummary).filter(UserSummary.user_email == user_email).first()

def save_user_summary(db: Session, user_email: str, summary_text: str):
    existing_summary = get_user_summary(db, user_email)
    if existing_summary:
        existing_summary.summary = summary_text
    else:
        new_summary = UserSummary(user_email=user_email, summary=summary_text)
        db.add(new_summary)
    db.commit()

def create_feedback(db: Session, email_id: str, priority: str, is_correct: bool):
    feedback = Feedback(email_id=email_id, priority=priority, is_correct=is_correct)
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback

def save_draft(db: Session, email_id: str, user_email: str, draft_text: str, tone: str):
    draft = db.query(EmailDraft).filter_by(email_id=email_id, user_email=user_email).first()
    if draft:
        draft.draft_text = draft_text
        draft.tone = tone
    else:
        draft = EmailDraft(
            email_id=email_id,
            user_email=user_email,
            draft_text=draft_text,
            tone=tone
        )
        db.add(draft)
    db.commit()
    
def delete_draft(db: Session, email_id: str, user_email: str):
    db.query(EmailDraft).filter(
        EmailDraft.email_id == email_id,
        EmailDraft.user_email == user_email
    ).delete()
    db.commit()

def save_reply(db: Session, email_id: str, user_email: str, reply_text: str, tone: str, is_auto: bool):
    reply_record = EmailReply(
        email_id=email_id,
        user_email=user_email,
        reply_text=reply_text,
        tone=tone,
        is_auto=is_auto
    )
    db.add(reply_record)
    db.commit()
    return reply_record