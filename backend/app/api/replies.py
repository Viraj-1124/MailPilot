from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database import crud
from app.database.models import Email, EmailReply
from app.services.ai_service import generate_smart_reply
from app.services.gmail_service import send_email_via_gmail
from app.schemas.reply import ReplyResponse, SendReplyRequest, AutoReplyRequest, DraftSaveRequest, DraftResponse, SendEmailRequest
from app.api.deps import get_current_user
from app.database.models import User

router = APIRouter()

@router.post("/generate-reply", response_model=ReplyResponse)
def generate_reply(email_id: str, tone: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    email = db.query(Email).filter(Email.email_id == email_id, Email.user_email == current_user.email).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    reply_data = generate_smart_reply(
        subject=email.subject,
        body=email.body,
        sender=email.sender,
        category=email.category,
        tone=tone
    )
    
    # Handle if reply_data is a string (error case or legacy) or dict
    if isinstance(reply_data, str):
        return {
            "email_id": email_id,
            "generated_reply": reply_data,
            "reply_subject": f"Re: {email.subject}",
            "reply_body": reply_data,
            "tone": tone
        }

    return {
        "email_id": email_id,
        "generated_reply": reply_data.get("body"),
        "reply_subject": reply_data.get("subject"),
        "reply_body": reply_data.get("body"),
        "tone": tone
    }

@router.post('/draft')
def save_draft(
    draft_req: DraftSaveRequest,
    current_user: User = Depends(get_current_user),
    db:Session = Depends(get_db)
):
    # Verify email ownership
    email = db.query(Email).filter(Email.email_id == draft_req.email_id, Email.user_email == current_user.email).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
        
    crud.save_draft(db, draft_req.email_id, current_user.email, draft_req.draft_text, draft_req.tone)
    return {"success": True}

from datetime import datetime

@router.post("/send-email")
def send_email_endpoint(
    req: SendEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = send_email_via_gmail(
            user_email=current_user.email,
            to_email=req.to_email,
            subject=req.subject,
            body=req.body
        )
        
        # Save to DB so it appears in Sent
        crud.save_email(
            db=db,
            email_id=result["id"],
            user_email=current_user.email,
            sender=current_user.email, # Explicitly set sender as current user
            subject=req.subject,
            body=req.body,
            summary="Sent message",
            priority="Medium",
            category="Personal",
            thread_id=result.get("threadId"),
            smart_thread_id=None,
            attachments=[],
            timestamp=datetime.now()
        )

        return {"success": True, "message_id": result["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-reply")
def send_reply(
    req: SendReplyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Fetch original email to get sender information
    email = db.query(Email).filter(Email.email_id == req.email_id, Email.user_email == current_user.email).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # reply goes back to original sender
    to_email = email.sender.split("<")[-1].replace(">", "").strip()

    result = send_email_via_gmail(
        user_email=email.user_email,
        to_email=to_email,
        subject=f"Re: {email.subject}",
        body=req.reply_text
    )

    crud.save_reply(
        db=db,
        email_id=req.email_id,
        user_email=email.user_email,
        reply_text=req.reply_text,
        tone="manual",
        is_auto=False
    )
    
    # Delete draft if exists
    crud.delete_draft(db, req.email_id, email.user_email)

    return {
        "success": True,
        "message_id": result["id"],
        "sent_to": to_email
    }

@router.post("/auto-reply")
def auto_reply(req: AutoReplyRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    email = db.query(Email).filter(Email.email_id == req.email_id, Email.user_email == current_user.email).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    reply_data = generate_smart_reply(
        subject=email.subject,
        body=email.body,
        sender=email.sender,
        category=email.category,
        tone=req.tone
    )
    
    # Handle dict response
    reply_body = reply_data.get("body") if isinstance(reply_data, dict) else reply_data
    reply = reply_body # Alias for compatibility with below code

    to_email = email.sender.split("<")[-1].replace(">", "").strip()

    result = send_email_via_gmail(
        user_email=email.user_email,
        to_email=to_email,
        subject=f"Re: {email.subject}",
        body=reply_body
    )

    crud.save_reply(
        db=db,
        email_id=req.email_id,
        user_email=email.user_email,
        reply_text=reply,
        tone=req.tone,
        is_auto=True
    )

    return {
        "success": True,
        "generated_reply": reply,
        "sent_to": to_email,
        "message_id": result["id"]
    }

@router.get("/all-drafts")
def get_all_drafts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Logic inlined here using DB directly or need new crud method if complex
    # Original did a join logic manually
    from app.database.models import EmailDraft
    drafts = db.query(EmailDraft).filter(EmailDraft.user_email == current_user.email).order_by(EmailDraft.updated_at.desc()).all()
    
    result = []
    for d in drafts:
        email_obj = db.query(Email).filter(Email.email_id == d.email_id).first()
        subject = email_obj.subject if email_obj else "(No Subject)"
        
        result.append({
            "email_id": d.email_id,
            "draft_text": d.draft_text,
            "tone": d.tone,
            "updated_at": d.updated_at,
            "subject": subject
        })
        
    return result

@router.get("/drafts")
def get_draft(email_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from app.database.models import EmailDraft
    draft = (db.query(EmailDraft).filter_by(email_id=email_id, user_email=current_user.email).first())

    if not draft:
        return {"draft": None}
    
    return {
        "draft_text" : draft.draft_text,
        "tone": draft.tone,
        "updated_at": draft.updated_at
    }

@router.get("/replies")
def get_replies(email_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verify ownership
    email = db.query(Email).filter(Email.email_id == email_id, Email.user_email == current_user.email).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
        
    from app.database.models import EmailReply
    replies = (
        db.query(EmailReply)
        .filter(EmailReply.email_id == email_id)
        .order_by(EmailReply.sent_at.desc())
        .all()
    )

    return [
        {
            "reply_text": r.reply_text,
            "tone": r.tone,
            "is_auto": r.is_auto,
            "sent_at": r.sent_at
        }
        for r in replies
    ]