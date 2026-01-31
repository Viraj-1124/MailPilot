import sys
import os
import json

# Add backend to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from app.database.models import UserPreference, SenderRule
from app.services.priority_service import resolve_email_priority, get_auto_reply_rule

def test_logic():
    print("Testing Priority Resolution Logic...")

    # Mock Data
    pref = UserPreference(
        user_email="test@example.com",
        interests=json.dumps(["Python", "Startup", "Meeting"]),
        primary_role="Engineer"
    )

    rule1 = SenderRule(sender_email="boss@company.com", force_priority="High", auto_reply=False)
    rule2 = SenderRule(sender_email="newsletter@spam.com", force_priority="Low", auto_reply=True)
    
    rules = [rule1, rule2]

    # Case 1: Sender Rule Override
    p1 = resolve_email_priority("boss@company.com", "Hello", "Body", "Low", pref, rules)
    print(f"Case 1 (Force High): {p1} [{'PASS' if p1 == 'High' else 'FAIL'}]")

    # Case 2: Interest Boost (Low -> Medium)
    p2 = resolve_email_priority("stranger@example.com", "Python Meetup", "Lets talk code", "Low", pref, rules)
    print(f"Case 2 (Boost Low->Medium): {p2} [{'PASS' if p2 == 'Medium' else 'FAIL'}]")
    
    # Case 3: Interest Boost (Medium -> High)
    p3 = resolve_email_priority("stranger@example.com", "Urgent Startup idea", "Lets talk business", "Medium", pref, rules)
    print(f"Case 3 (Boost Medium->High): {p3} [{'PASS' if p3 == 'High' else 'FAIL'}]")

    # Case 4: No Match (Fallback)
    p4 = resolve_email_priority("random@example.com", "Lunch?", "Pizza time", "Low", pref, rules)
    print(f"Case 4 (Fallback Low): {p4} [{'PASS' if p4 == 'Low' else 'FAIL'}]")

    # Case 5: Auto Reply Rule
    ar = get_auto_reply_rule("newsletter@spam.com", rules)
    print(f"Case 5 (Auto Reply): {ar.auto_reply if ar else 'None'} [{'PASS' if ar and ar.auto_reply else 'FAIL'}]")

    print("\nLogic Verification Complete.")

if __name__ == "__main__":
    test_logic()
