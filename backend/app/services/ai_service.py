import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from app.core.config import settings
from app.services.notification import send_notification
load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY")
)

# Helper for safe API calls
def safe_chat_completion(model, messages, max_tokens=1000, temperature=0.7):
    """Wraps OpenAI API calls with error handling for OpenRouter/Credits."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        error_msg = str(e).lower()
        if "402" in error_msg or "payment" in error_msg or "credit" in error_msg:
             print("AI Request Failed: Insufficient Credits/Quota.")
             raise Exception("AI_QUOTA_EXCEEDED")
        elif "429" in error_msg:
             print("AI Request Failed: Rate Limited.")
             raise Exception("AI_RATE_LIMIT")
        elif "401" in error_msg:
             print("AI Request Failed: Invalid API Key.")
             raise Exception("AI_AUTH_ERROR")
        else:
             print(f"AI Request Failed: {e}")
             raise e

def summarize_email(subject, body):
    """Generate a concise summary using AI, falling back to truncation on failure."""
    if not body:
        return subject
        
    prompt = f"Summarize this email in 1 concise sentence (max 20 words):\n\nSubject: {subject}\nBody: {body[:1500]}"
    
    try:
        # Use openai/gpt-4o-mini for OpenRouter
        summary = safe_chat_completion(
            model="openai/gpt-4o-mini", 
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.3
        )
        return summary
    except Exception:
        # Fallback to truncation if AI fails (e.g. quota exceeded)
        words = body.split()
        summary = " ".join(words[:40])
        return summary + "..." if len(words) > 40 else summary

def analyze_emails_with_ai(emails):
    """Analyze and prioritize emails using GPT."""
    if not emails:
        return {"overall_summary": "No emails to analyze.", "priorities": []}

    email_text = "\n".join([
        f"From: {e['from']}\nSubject: {e['subject']}\nSummary: {e['summary']}"
        for e in emails[:30] # Limit context window
    ])

    prompt = f"""
    You are an intelligent email assistant. You MUST return a VALID JSON ONLY.

    Based on these emails, produce:
    1. An detailed overall summary.
    2. Priority for each email: High / Medium / Low.

    Return JSON in this EXACT format:
    {{
      "overall_summary": "summary text",
      "priorities": [
        {{"subject": "subject text", "priority": "High"}},
        ...
      ]
    }}

    Emails:
    {email_text}
    """

    try:
        raw_output = safe_chat_completion(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200,
            temperature=0.2
        )
        
        # Clean up code blocks if present
        if raw_output.startswith("```json"):
            raw_output = raw_output[7:-3].strip()
        elif raw_output.startswith("```"):
            raw_output = raw_output[3:-3].strip()
            
        analysis=json.loads(raw_output)
        high_priority_exists = any(
            p.get("priority", "").lower() == "high"
            for p in analysis.get("priorities", [])
        )

        if  high_priority_exists:
           

            summary = analysis.get("overall_summary", "Urgent email detected.")
            send_notification(summary)
            print(f"High Priority Alert: {summary}")
            # send_notification(summary) # Placeholder for future implementation
        return json.loads(raw_output)
    except Exception as e:
        err_str = str(e)
        if "AI_QUOTA_EXCEEDED" in err_str:
            return {"overall_summary": "⚠️ AI Service Unavailable (Quota Exceeded). Showing raw emails.", "priorities": []}
        return {"overall_summary": "Could not generate summary due to temporary AI service error.", "priorities": []}

        
def categorize_email_with_ai(subject, body, sender=None):
    """Advanced intelligent categorization using GPT."""

    prompt = f"""
    Analyze the email and assign the MOST appropriate category.
    
    You MUST choose from these categories ONLY:
    - Work
    - College
    - Personal
    - Bank/Finance
    - Offers/Promotions
    - Travel/Tickets
    - Bills/Payments
    - Security Alert
    - Subscriptions/Newsletters
    - Events/Conferences
    - Important/Deadline
    - LinkedIn
    - Spam

    Email details:
    Sender: {sender}
    Subject: {subject}
    Body: {body[:1000]}

    Return JSON in this exact format:
    {{
        "category": "CategoryName"
    }}
    """

    try:
        raw_output = safe_chat_completion(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0
        )
        
        if raw_output.startswith("```json"):
            raw_output = raw_output[7:-3].strip()
        elif raw_output.startswith("```"):
            raw_output = raw_output[3:-3].strip()

        data = json.loads(raw_output)
        return data.get("category", "Personal")
    except:
        return "Personal"

def generate_smart_reply(subject, body, sender, category, tone):
    prompt = f"""
    You are an intelligent email assistant. Write a reply to this email.

    Sender: {sender}
    Subject: {subject}
    Category: {category}

    Email Body:
    {body[:2000]}

    Tone required: {tone}

    Instructions:
    1. Return VALID JSON ONLY.
    2. Do NOT add placeholders like [Your Name], [Your Contact Info], etc. Leave the signature plain or just the name if known, otherwise end with "Best regards,".
    3. The JSON must have two fields: "subject" (suggested reply subject, e.g. Re: ...) and "body" (the email content).

    Example JSON:
    {{
        "subject": "Re: Meeting",
        "body": "Hi there,\\n\\nI would love to attend.\\n\\nBest,\\n"
    }}
    """

    try:
        content = safe_chat_completion(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.4
        )
        
        # Clean markdown
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        return json.loads(content)
    except Exception as e:
        err_str = str(e)
        fallback_msg = "Could not generate reply."
        if "AI_QUOTA_EXCEEDED" in err_str:
             fallback_msg = "⚠️ AI Quota Exceeded. Please check billing or try again later."
        
        return {"subject": f"Re: {subject}", "body": fallback_msg}

def infer_category_from_sender(sender):
    if not sender: return None
    sender = sender.lower()

    if "vit.edu" in sender:
        return "College"
    if "bank" in sender or "hdfc" in sender or "sbi" in sender:
        return "Bank/Finance"
    if "no-reply" in sender or "newsletter" in sender:
        return "Subscriptions/Newsletters"
    if "security" in sender:
        return "Security Alert"
    
    return None

def smart_categorize_email(subject, body, sender):
    # 1️⃣ Domain-based quick classification
    sender_based = infer_category_from_sender(sender)
    if sender_based:
        return sender_based

    # 2️⃣ AI-based classification
    ai_category = categorize_email_with_ai(subject, body, sender)

    return ai_category