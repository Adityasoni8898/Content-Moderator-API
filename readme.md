# 🧠 Content Moderation Service (FastAPI + PostgreSQL)

A modern AI-powered **content moderation backend** built with **FastAPI** and **PostgreSQL**, capable of analyzing user-submitted **text or image content** for inappropriate material.  
It stores moderation results, sends **alerts via email/Slack**, and provides analytics endpoints for future use.

---

## 🚀 Features

- 🧩 **Text Moderation** — Uses a free LLM API (Perplexity/Sonar Pro or compatible) to detect inappropriate or NSFW content.  
- 🖼️ **Image Moderation** — Detects explicit or unsafe images using AI APIs (extendable).  
- 📨 **Email Alerts** — Sends alert notifications through **Brevo (Sendinblue)** when flagged content is detected.  
- 💬 **Slack Notifications** — Optional real-time alerts to a Slack channel.  
- 🧾 **Database Storage** — Logs moderation results, user info, and notifications in PostgreSQL.  
- 🔐 **JWT Authentication** — Only logged-in users can submit moderation requests.  
- 📊 **Analytics Ready** — Stores detailed moderation logs for insights and dashboards.

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-------------|
| Backend | [FastAPI] |
| Database | [PostgreSQL] |
| ORM | [SQLAlchemy]|
| Schema Validation | [Pydantic]|
| Authentication | JWT (JSON Web Tokens) |
| Notifications | Brevo API & Slack Webhooks |
| AI Model | Sonar-Pro (Perplexity API) |

---

## 🗂️ Project Structure

app/
│
├── main.py            # FastAPI entry point<br>
├── database.py        # Database setup and session management<br>
├── models.py          # SQLAlchemy models<br>
├── schemas.py         # Pydantic schemas<br>
├── oauth2.py          # JWT token and authentication logic<br>
├── utils.py           # Helper functions<br>
├── routers/
│   ├── auth.py        # User login<br>
│   ├── moderation.py  # Text & Image moderation<br>
│   └── analytics.py   # Analytics and reporting<br>
│   └── users.py       # User signup<br>
└── .env               # Environment variables<br>

## 🧑‍💻 API Overview

### 🔐 Authentication
| Endpoint | Method | Description |
|-----------|--------|-------------|
| `/signup` | POST | Create a new user account |
| `/login`  | POST | Authenticate and receive a JWT token |

### 🔐 Content Moderation
| Endpoint | Method | Description |
|-----------|--------|-------------|
| `/moderate/text` | POST | Analyze a text input for inappropriate content (Login required) |
| `/moderate/image`  | POST | Analyze an image for inappropriate or unsafe material (Login required) |


### Alerts

When a piece of content is flagged as inappropriate, the system performs the following actions automatically:
	1.	📧 Email Alert — Sends a notification via Brevo (Sendinblue) to the configured recipient.
	2.	💬 Slack Notification (optional) — Sends a message to a Slack channel via webhook.
	3.	🧾 Database Log — Creates an entry in the notification_logs table for tracking.
