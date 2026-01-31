import json
import re
from typing import Optional
from app.services.ai_service import safe_chat_completion

ACTION_KEYWORDS = [
    "submit", "complete", "fill", "review", "send", "share",
    "attend", "join", "schedule", "update", "approve",
    "deadline", "due", "by", "before"
]
ACTION_REGEX = re.compile(r"\b(" + "|".join(ACTION_KEYWORDS) + r")\b", re.IGNORECASE)

# 2. Time Indicators
# Matches: 5 PM, 5:30 PM, 17:00, 5pm
TIME_REGEX = re.compile(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b|\b\d{1,2}\s?(?:am|pm)\b", re.IGNORECASE)

# 3. Date Indicators
# Matches: today, tomorrow, EOD, ASAP, 12/09, 12-09, Sept 12
DATE_KEYWORDS = r"today|tomorrow|eod|asap"
DATE_NUMERIC = r"\d{1,2}[/-]\d{1,2}"
DATE_TEXTUAL = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s\d{1,2}"
DATE_REGEX = re.compile(rf"\b({DATE_KEYWORDS})\b|{DATE_NUMERIC}|{DATE_TEXTUAL}", re.IGNORECASE)


def should_extract_tasks(
    subject: str,
    body: str,
    category: Optional[str] = None,
    priority: Optional[str] = None
) -> bool:
    """
    Deterministic pre-filter to decide if an email is eligible for AI task extraction.
    
    Rules:
    - Returns False if category is Offers/Promotions/Spam.
    - Returns True if Priority is High/Medium.
    - Returns True if Action Keywords or Time/Date patterns are found.
    - Otherwise returns False.
    
    This acts as a cost-control layer before calling the expensive LLM function.
    """
    
    # 1. Negative Filters (Exclusions take precedence)
    if category in ["Offers", "Promotions", "Spam"]:
        return False
        
    # 2. Positive Filter: High Priority
    # If it's important, we check it regardless of keywords (unless excluded above)
    if priority in ["High", "Medium"]:
        return True
        
    # 3. Content Analysis
    # Combine subject and body for search (limit body to first 2000 chars for speed)
    text_to_scan = f"{subject} {body[:2000]}"
    
    if ACTION_REGEX.search(text_to_scan):
        return True
        
    if TIME_REGEX.search(text_to_scan):
        return True
        
    if DATE_REGEX.search(text_to_scan):
        return True
        
    return False


def extract_tasks_from_email(subject: str, body: str) -> dict:
    """
    Extracts actionable tasks from an email using LLM.
    
    Args:
        subject (str): Email subject.
        body (str): Email body text.

    Returns:
        dict: A dictionary containing 'has_tasks' (bool) and 'tasks' (list).
              Example:
              {
                  "has_tasks": True,
                  "tasks": [
                      {"task_text": "Submit report", "deadline": "tomorrow 5 PM"}
                  ]
              }
              
    Developer Note:
    - This function should only be called after heuristic pre-filtering to save costs.
    - Future steps will handle persistence of these tasks.
    """
    
    # Prompt engineering for strict JSON extraction
    prompt = f"""
    You are a task extraction engine. Your goal is to identify explicit actionable tasks from the following email.
    
    RULES:
    1. Extract ONLY specific actions the user (recipient) needs to take.
    2. Ignore: Promotions, Newsletters, FYI-only emails, General status updates without action required.
    3. If there are no clear actions, return "has_tasks": false.
    4. Deadlines: Extract if present (e.g., "by Friday", "tomorrow", "Jan 31st"). If none, set null.
    5. Output MUST be valid JSON only. NO markdown, NO explanations.
    
    JSON Schema:
    {{
      "has_tasks": boolean,
      "tasks": [
        {{
          "task_text": "string (concise action)",
          "deadline": "string | null (natural language is fine)"
        }}
      ]
    }}
    
    EMAIL CONTENT:
    Subject: {subject}
    Body:
    {body[:2000]}
    """
    
    try:
        # Strict low temperature for consistent JSON
        response = safe_chat_completion(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.1
        )
        
        # Clean potential markdown wrapping
        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:-3].strip()
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:-3].strip()
            
        data = json.loads(cleaned_response)
        
        # Validate critical fields
        if "has_tasks" not in data or "tasks" not in data:
            raise ValueError("Invalid JSON schema returned by AI")
            
        return data

    except Exception as e:
        print(f"Task Extraction Failed: {e}")
        # Fail safe: assume no tasks rather than crashing
        return {
            "has_tasks": False,
            "tasks": []
        }
