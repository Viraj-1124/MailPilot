# 📧 EmailPilot — AI-Powered Personalized Email Assistant

## 🔴 Problem Statement 

Modern inboxes overwhelm users with irrelevant emails, causing missed important messages and constant distractions.
Traditional email clients apply uniform rules, failing to adapt to individual user roles, priorities, and intent.
Users need **personalized email intelligence**, not just filters.

---

## 👥 Users & Context

EmailPilot adapts to **who the user is** and **what they care about**.

| User Type     | Primary Concerns                   |
| ------------- | ---------------------------------- |
| Students      | Assignments, internships, exams    |
| Professionals | Meetings, work communication       |
| Influencers   | Brand collaborations, sponsorships |
| General Users | Finance, bills, important alerts   |

Each user has **different definitions of “important”**, which traditional inboxes ignore.

---

## 💡 Solution Overview

EmailPilot is a **personal AI assistant for your inbox** that understands intent, prioritizes intelligently, and takes action.

### Core Flow (Logical Diagram)

```
Gmail Inbox
   ↓
Email Fetch (Gmail API)
   ↓
AI Engine
   ├─ Summarization
   ├─ Priority Classification
   ├─ Category Detection
   └─ Task Extraction
   ↓
Personalization Engine
   ├─ User Role
   ├─ Interests
   ├─ Custom Rules
   ↓
Actions
   ├─ Notify (High Priority Only)
   ├─ Add to Calendar
   └─ Schedule Reminders
```

### 🔥 Key Differentiator

> **Users receive notifications ONLY for High-Priority emails.**
> No noise. No distractions. Only what matters.

---

## ⚙ Setup & Run

### Prerequisites

* Python 3.10+
* Node.js 18+
* Google Cloud Project with:

  * Gmail API enabled
  * Google Calendar API enabled
* OAuth 2.0 credentials

### Backend Setup

```bash
git clone https://github.com/your-username/emailpilot.git
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env`:

```env
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
JWT_SECRET=
OPENAI_API_KEY=
```

Run backend:

```bash
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## 🧠 Models & Data

### Data Sources

* Gmail API (user-authorized emails)
* Google Calendar API (task scheduling)

### AI Models

* LLMs via OpenAI / OpenRouter

  * Email summarization
  * Priority detection
  * Task extraction

### Data Storage

* SQLite (development)
* SQLAlchemy ORM
* Duplicate-safe email storage

### Licensing of Data

* Emails accessed **only with explicit user consent**
* No training on user data
* OAuth scope isolation enforced

---

## 🧪 Evaluation & Guardrails

### Hallucination Mitigation

* AI outputs constrained by:

  * Pre-defined categories
  * Priority labels (High / Medium / Low)
* No free-form critical actions without user confirmation

### Bias Mitigation

* Priority decisions influenced by:

  * Explicit user role
  * User-defined rules
* No hidden behavioral inference

### Security Guardrails

* OAuth 2.0 scope isolation
* JWT-protected APIs
* Per-user data isolation
* Token encryption & refresh handling

---

## ⚠ Known Limitations & Risks

* AI priority classification may occasionally mis-rank edge cases
* SQLite not suitable for production scale
* Requires Gmail access (not email-provider agnostic yet)
* Initial personalization depends on correct user role selection

---

## 🎥 Product Demo

📺 **Demo Video:**  
👉 *[https://youtu.be/ohUiPc37_w0?si=d-SuKDf52JG6O1PY]*

📊 **Presentation / Pitch Deck:**  
👉 *[https://gamma.app/docs/EmailPilot-Smart-Email-Priority-Classifier-Notifier-mhrbbtdnemg5yvs?mode=present#card-3zqihcwri7yfl7i]*

---

## 👨💻 Team

### 🚀 Core Contributors

**Rushikesh Shinde**
B.Tech CSE (AIML), VIT Pune
Backend • AI Integration • System Design
📧 Email: *rushikeshs200624@gmail.com*

**Guruprasad Melinkeri**
B.Tech CSE (AIML), VIT Pune
Backend • ML • API Engineering
📧 Email: *guruprasad.melinkeri.tech@gmail.com*

---

## 📄 License

### MIT License

```
MIT License

Copyright (c) 2026 EmailPilot

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

### ✨ Tagline

> **EmailPilot — Doomscroll reels, not emails. Read only what matters to you.**
