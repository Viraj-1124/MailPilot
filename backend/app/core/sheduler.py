from apscheduler.schedulers.background import BackgroundScheduler
from app.services.gmail_service import authenticate_gmail, get_last_24h_emails, get_email_details
from app.services.ai_service import summarize_email, smart_categorize_email, analyze_emails_with_ai
from app.services.thread_service import assign_smart_thread_id
from app.database.database import SessionLocal
from app.database.models import Email, EmailTask, UserPreference, SenderRule
from app.services.notification import send_notification
from app.services.priority_service import resolve_email_priority, get_auto_reply_rule
from app.services.ai_service import summarize_email, smart_categorize_email, analyze_emails_with_ai, generate_smart_reply
from app.services.gmail_service import authenticate_gmail, get_last_24h_emails, get_email_details, send_email_via_gmail
from datetime import datetime
from app.database import crud

def auto_fetch_emails():
    print("⏳ Running auto-fetch job...")
    db = SessionLocal()
    try:
        # Get list of all users
        users = db.query(Email.user_email).distinct().all()
        
        for (user_email,) in users:
            print(f"📩 Auto-fetching emails for {user_email}")
            
            # Fetch User Preferences & Rules
            user_pref = db.query(UserPreference).filter(UserPreference.user_email == user_email).first()
            sender_rules = db.query(SenderRule).filter(SenderRule.user_email == user_email).all()

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

                    # Handle Auto-Reply Rule
                    reply_rule = get_auto_reply_rule(sender, sender_rules)
                    if reply_rule:
                        print(f"🤖 Auto-reply triggered for {sender}")
                        try:
                            reply_content = generate_smart_reply(
                                subject=subject,
                                body=full_body,
                                sender=sender,
                                category=category,
                                tone="Professional"
                            )
                            # Send via Gmail
                            send_email_via_gmail(
                                user_email=user_email,
                                to_email=sender,
                                subject=reply_content.get("subject", f"Re: {subject}"),
                                body=reply_content.get("body", "Received.")
                            )
                            # Prepare log record (optional, simplified here)
                            crud.save_reply(
                                db=db,
                                email_id=msg["id"],
                                user_email=user_email,
                                reply_text=reply_content.get("body", ""),
                                tone="Professional",
                                is_auto=True
                            )
                        except Exception as ar_e:
                            print(f"Failed to auto-reply: {ar_e}")

                except Exception as e:
                    print(f"Error processing message {msg['id']}: {e}")

            # Batch AI analysis for priority and summary
            if fetched_emails_data:
                ai_data = analyze_emails_with_ai(fetched_emails_data)
                
                # Update priorities
                for email_info in fetched_emails_data:
                    match = next((p for p in ai_data.get("priorities", []) if p["subject"] == email_info["subject"]), None)
                    ai_priority = match["priority"] if match else "Medium"
                    
                    # Resolve Final Priority using Personalization
                    final_priority = resolve_email_priority(
                        sender=email_info["from"],
                        subject=email_info["subject"],
                        body=email_info["summary"], # Use summary or full body if available? Using summary for speed/context
                        ai_priority=ai_priority,
                        user_pref=user_pref,
                        sender_rules=sender_rules
                    )

                    crud.update_email_priority(db, email_info["email_id"], final_priority)

                # Save user summary
                if "overall_summary" in ai_data:
                    crud.save_user_summary(db, user_email, ai_data["overall_summary"])

        print("✅ Auto-fetch cycle completed")
    finally:
        db.close()

from app.database.models import Email, EmailTask
from app.services.notification import send_notification
from datetime import datetime

def check_reminders():
    # print("⏳ Checking reminders...") 
    # (Commented out to avoid log spam every minute)
    db = SessionLocal()
    try:
        now = datetime.now()
        due_reminders = db.query(EmailTask).filter(
            EmailTask.reminder_time <= now,
            EmailTask.reminder_sent == False,
            EmailTask.completed == False
        ).all()

        for task in due_reminders:
            print(f"⏰ Sending reminder for task: {task.id}")
            try:
                # Use updated notification service
                send_notification(
                    summary=f"Reminder: {task.task_text}",
                    title="Task Reminder"
                )
                task.reminder_sent = True
            except Exception as e:
                print(f"Failed to send reminder for {task.id}: {e}")
        
        if due_reminders:
            db.commit()

    except Exception as e:
        print(f"Error checking reminders: {e}")
    finally:
        db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(auto_fetch_emails, "interval", minutes=50)
    scheduler.add_job(check_reminders, "interval", minutes=1)
    scheduler.start()
    print("🚀 APScheduler Started (fetching 50m, reminders 1m)")