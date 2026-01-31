from apscheduler.schedulers.background import BackgroundScheduler
from app.services.gmail_service import authenticate_gmail, get_last_24h_emails, get_email_details
from app.services.ai_service import summarize_email, smart_categorize_email, analyze_emails_with_ai
from app.services.thread_service import assign_smart_thread_id
from app.database.database import SessionLocal
from app.database.models import Email
from app.database import crud

def auto_fetch_emails():
    print("⏳ Running auto-fetch job...")
    db = SessionLocal()
    try:
        # Get list of all users
        users = db.query(Email.user_email).distinct().all()
        
        for (user_email,) in users:
            print(f"📩 Auto-fetching emails for {user_email}")
            try:
                service = authenticate_gmail(user_email)
            except Exception as e:
                print(f"❌ Failed to authenticate {user_email}: {e}")
                continue

            messages = get_last_24h_emails(service)
            if not messages:
                continue

            fetched_emails_data = []

            for msg in messages:
                try:
                    sender, subject, preview, full_body, thread_id, attachments, timestamp = get_email_details(service, msg["id"])
                    summary = summarize_email(subject, full_body)
                    category = smart_categorize_email(subject, full_body, sender)
                    smart_thread_id = assign_smart_thread_id(db, user_email, subject)

                    # We save immediately with default priority, then update later with batch AI
                    crud.save_email(
                        db=db,
                        email_id=msg["id"],
                        user_email=user_email,
                        sender=sender,
                        subject=subject,
                        body=full_body,
                        summary=summary,
                        priority="Medium", # Default
                        category=category,
                        thread_id=thread_id,
                        smart_thread_id=smart_thread_id,
                        attachments=attachments,
                        timestamp=timestamp
                    )
                    
                    fetched_emails_data.append({
                        "email_id": msg["id"],
                        "from": sender,
                        "subject": subject,
                        "summary": summary
                    })
                except Exception as e:
                    print(f"Error processing message {msg['id']}: {e}")

            # Batch AI analysis for priority and summary
            if fetched_emails_data:
                ai_data = analyze_emails_with_ai(fetched_emails_data)
                
                # Update priorities
                for email_info in fetched_emails_data:
                    match = next((p for p in ai_data.get("priorities", []) if p["subject"] == email_info["subject"]), None)
                    if match:
                        final_priority = match["priority"]
                        crud.update_email_priority(db, email_info["email_id"], final_priority)

                # Save user summary
                if "overall_summary" in ai_data:
                    crud.save_user_summary(db, user_email, ai_data["overall_summary"])

        print("✅ Auto-fetch cycle completed")
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(auto_fetch_emails, "interval", minutes=50)
    scheduler.start()
    print("🚀 APScheduler Started (fetching every 5 min)")