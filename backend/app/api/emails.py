from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.database import crud
from app.database.models import Email, EmailAttachment, UserSummary
from app.schemas.email import EmailListResponse, EmailDetail, SmartThread, ThreadGroup
from app.services.gmail_service import authenticate_gmail, get_last_24h_emails, get_email_details
from app.services.ai_service import summarize_email, analyze_emails_with_ai, smart_categorize_email
from app.services.thread_service import assign_smart_thread_id
from app.core.config import settings
import os
from app.api.deps import get_current_user
from app.database.models import User

router = APIRouter()

@router.get("/fetch-emails")
def fetch_emails(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Fetch last 24h Gmail emails and summarize"""
    user_email = current_user.email
    token_path = f"{settings.TOKENS_DIR}/{user_email}.json"
    if not os.path.exists(token_path):
        return {"error": f"No token found for {user_email}. Please re-login."}

    try:
        service = authenticate_gmail(user_email)
    except Exception as e:
        return {"error": "Authentication failed. Please re-login.", "details": str(e)}
    
    messages = get_last_24h_emails(service)
    if not messages:
        return {"overall_summary": "No new emails in last 24 hours", "emails": []}

    emails = []
    new_emails_count = 0
    
    # Process all fetched messages (or limit to reasonable batch size like 50)
    for msg in messages[:50]:
        # Optimization: Check if email already exists in DB
        existing_email = db.query(Email).filter(Email.email_id == msg["id"], Email.user_email == user_email).first()
        if existing_email:
            continue

        new_emails_count += 1
        sender, subject, preview, full_body, thread_id, attachments, timestamp, is_read = get_email_details(
        service, msg["id"])
        
        # Safe summary generation (handles quota errors internally in ai_service)
        summary = summarize_email(subject, full_body)
        
        category = smart_categorize_email(subject, full_body, sender)
        smart_thread_id = assign_smart_thread_id(db, user_email, subject)

        emails.append({
            "email_id": msg["id"],
            "from": sender,
            "subject": subject,
            "summary": summary,
            "is_read": is_read
        })

        crud.save_email(
            db=db,
            email_id=msg["id"],
            user_email=user_email,
            sender=sender,
            subject=subject,
            body=full_body,
            summary=summary,
            priority="Medium", 
            category=category,
            thread_id=thread_id,
            smart_thread_id=smart_thread_id,
            attachments=attachments,
            timestamp=timestamp,
            is_read=is_read
        )
    
    # Only run analysis if we actually fetched new emails
    if emails:
        ai_data = analyze_emails_with_ai(emails)

        for email in emails:
            match = next((p for p in ai_data.get("priorities", []) if p["subject"] == email["subject"]), None)
            final_priority = match["priority"] if match else "Medium"
            email["priority"] = final_priority
            crud.update_email_priority(db, email["email_id"], final_priority)

        # Save overall summary to DB
        if "overall_summary" in ai_data:
            crud.save_user_summary(db, user_email, ai_data["overall_summary"])

    return {
        "overall_summary": "Sync complete.",
        "new_emails_count": new_emails_count,
        "emails": emails
    }



@router.get("/emails", response_model=EmailListResponse)
def get_emails_from_db(
    priority: str = Query("All", description="Filter by priority"),
    folder: str = Query("inbox", description="Folder: inbox or sent"), # Added folder param
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Fetch emails directly from DB (fast load)"""
    query = db.query(Email).filter(Email.user_email == current_user.email)

    if folder == "sent":
        # Sent emails: sender contains user email (rudimentary check) or exact match
        query = query.filter(Email.sender.ilike(f"%{current_user.email}%"))
        # Exclude deleted if we want trash separate, but usually sent shows all sent unless deleted
        query = query.filter(Email.is_deleted == False) 
    elif folder == "archive":
        query = query.filter(
            Email.is_archived == True, 
            Email.is_deleted == False,
            ~Email.sender.ilike(f"%{current_user.email}%") # Usually archive is for inbox items
        )
    elif folder == "trash":
        query = query.filter(Email.is_deleted == True)
    else:
        # Inbox emails: sender does NOT contain user email, not archived, not deleted
        query = query.filter(
            ~Email.sender.ilike(f"%{current_user.email}%"),
            Email.is_archived == False,
            Email.is_deleted == False
        )

    if priority and priority != "All":
        query = query.filter(Email.priority == priority)

    emails = (
        query
        .order_by(Email.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for email in emails:
        result.append({
            "email_id": email.email_id,
            "from_": email.sender, # Map 'sender' to 'from_'
            "subject": email.subject,
            "summary": email.summary,
            "priority": email.priority,
            "timestamp": email.timestamp,
            "is_read": email.is_read
        })

    user_summary = crud.get_user_summary(db, current_user.email)
    summary_text = user_summary.summary if user_summary else "No summary available."

    return {
        "overall_summary": summary_text, 
        "emails": result
    }

@router.get("/email/{email_id}", response_model=EmailDetail)
def get_full_email(email_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    email = db.query(Email).filter(Email.email_id == email_id, Email.user_email == current_user.email).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    return {
        "email_id": email.email_id,
        "from_": email.sender,
        "subject": email.subject,
        "body": email.body,
        "body": email.body,
        "timestamp": email.timestamp,
        "is_archived": email.is_archived,
        "is_deleted": email.is_deleted,
        "attachments": [
            {
                "filename": a.filename,
                "size": a.size,
                "mime_type": a.mime_type,
                "attachment_id": a.attachment_id
            } for a in email.attachments
        ]
    }

@router.get("/smart-threads")
def get_smart_threads(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    emails = db.query(Email).filter(Email.user_email == current_user.email).all()

    grouped = {}
    for email in emails:
        if email.smart_thread_id not in grouped:
            grouped[email.smart_thread_id] = []
        grouped[email.smart_thread_id].append({
            "email_id": email.email_id,
            "subject": email.subject,
            "summary": email.summary,
            "priority": email.priority,
            "category": email.category,
            "timestamp": email.timestamp
        })

    thread_list = [
        {"smart_thread_id": tid, "emails": msgs}
        for tid, msgs in grouped.items()
    ]

    return {"smart_threads": thread_list}

@router.get("/threads")
def get_threads(
    mode: str = "subject",     # default threading
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    emails = db.query(Email).filter(Email.user_email == current_user.email).all()
    if not emails:
        return {"threads": []}

    grouped = {}

    for email in emails:
        if mode == "subject":
            # In original code, it called assign_smart_thread_id again?
            # Actually no, it called assign_smart_thread_id in the original route.
            # But we already have smart_thread_id stored in DB.
            # Ideally we should use the stored one.
            key = email.smart_thread_id or "Unthreaded"
        elif mode == "category":
            key = email.category or "Uncategorized"
        elif mode == "priority":
            key = email.priority or "Medium"
        elif mode == "sender":
            key = email.sender.split("<")[0].strip()   # clean sender name
        elif mode == "date":
            key = email.timestamp.date()
        else:
            key = "Other"

        if key not in grouped:
            grouped[key] = []

        grouped[key].append({
            "email_id": email.email_id,
            "sender": email.sender,
            "subject": email.subject,
            "summary": email.summary,
            "priority": email.priority,
            "category": email.category,
            "thread_id": email.thread_id,
            "timestamp": email.timestamp
        })

    thread_list = [
        {"group_key": str(key), "emails": msgs}
        for key, msgs in grouped.items()
    ]

    return {"threads": thread_list}

@router.get("/attachments")
def list_attachments(email_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verify email belongs to user first to prevent IDOR
    email = db.query(Email).filter(Email.email_id == email_id, Email.user_email == current_user.email).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
        
    attachments = db.query(EmailAttachment).filter(EmailAttachment.email_id == email_id).all()
    
    return [
        {
            "filename": att.filename,
            "mime_type": att.mime_type,
            "size": att.size,
            "attachment_id": att.attachment_id
        }
        for att in attachments
    ]

@router.get("/search")
def search_emails(
    q: str = Query(..., description="Search text"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search emails by subject, sender, body, or summary"""

    query_str = f"%{q.lower()}%"

    results = db.query(Email).filter(
        Email.user_email == current_user.email,
        (
            Email.subject.ilike(query_str) |
            Email.sender.ilike(query_str) |
            Email.body.ilike(query_str) |
            Email.summary.ilike(query_str) |
            Email.priority.ilike(query_str)
        )
    ).all()

    return [
        {
            "email_id": e.email_id,
            "sender": e.sender,
            "subject": e.subject,
            "summary": e.summary,
            "priority": e.priority,
            "timestamp": e.timestamp
        }
        for e in results
    ]

from datetime import datetime

@router.post("/email/{email_id}/archive")
def archive_email(email_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    email = db.query(Email).filter(Email.email_id == email_id, Email.user_email == current_user.email).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    email.is_archived = True
    email.archived_at = datetime.now()
    email.is_deleted = False # Ensure not deleted if archived
    db.commit()
    return {"success": True, "message": "Email archived"}

@router.post("/email/{email_id}/unarchive")
def unarchive_email(email_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    email = db.query(Email).filter(Email.email_id == email_id, Email.user_email == current_user.email).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    email.is_archived = False
    email.archived_at = None
    db.commit()
    return {"success": True, "message": "Email unarchived"}

@router.post("/email/{email_id}/delete")
def delete_email(email_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    email = db.query(Email).filter(Email.email_id == email_id, Email.user_email == current_user.email).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    email.is_deleted = True
    email.deleted_at = datetime.now()
    db.commit()
    return {"success": True, "message": "Email deleted"}

@router.post("/email/{email_id}/restore")
def restore_email(email_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    email = db.query(Email).filter(Email.email_id == email_id, Email.user_email == current_user.email).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    email.is_deleted = False
    email.deleted_at = None
    db.commit()
    return {"success": True, "message": "Email restored"}

@router.post("/email/{email_id}/read")
def mark_email_read(email_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    email = db.query(Email).filter(Email.email_id == email_id, Email.user_email == current_user.email).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    email.is_read = True
    db.commit()
    return {"success": True, "message": "Email marked as read"}

@router.post("/email/{email_id}/quick-summary")
def quick_summary(email_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate a very short 1-2 sentence summary on demand."""
    email = db.query(Email).filter(Email.email_id == email_id, Email.user_email == current_user.email).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Use existing summary if it's already short? No, user wants a specific quick glance probably.
    # But to save cost, we can check if we already have a 'short_summary' stored? 
    # For now, we'll generate it on fly but keep it cheap.
    
    try:
        from app.services.ai_service import safe_chat_completion
        prompt = f"Summarize this email in 1 very short, actionable sentence (max 15 words). No filler.\n\nSubject: {email.subject}\nBody: {email.body[:1000]}"
        
        summary = safe_chat_completion(
            model="arcee-ai/trinity-large-preview:free",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=40,
            temperature=0.3
        )
        return {"summary": summary}
    except Exception as e:
        print(f"Quick summary failed: {e}")
        return {"summary": "Could not generate summary."}