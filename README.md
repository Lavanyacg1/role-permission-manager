# Role & Permission Manager

Flask-based AI microservice powered by Groq (LLaMA-3.3-70b).
Provides role description, security recommendations, and report generation.

---

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.11 | Language |
| Flask 3.x | Web framework |
| Groq API (LLaMA-3.3-70b) | AI model |
| Redis 7 | Response caching (15 min TTL) |
| flask-limiter | Rate limiting (30 req/min) |

---

## Prerequisites

- Python 3.11
- Redis 7 (optional — app works without it)
- Groq API key from https://console.groq.com

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone <repository-url>
cd Role_and_Permission_Manager/ai-service
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create .env file
```bash
copy .env.example .env
```

Open `.env` and fill in your values:
```env
GROQ_API_KEY=gsk_your_key_here
REDIS_URL=redis://localhost:6379
```

### 5. Run the service
```bash
python app.py
```

Service runs on: `http://localhost:5000`

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| GROQ_API_KEY | Yes | Groq API key from console.groq.com |
| REDIS_URL | No | Redis connection URL |

---

## API Reference

### GET /health
Check service status and performance metrics.

**Request:**
```
GET http://localhost:5000/health
```

**Response:**
```json
{
    "status": "ok",
    "model": "llama-3.3-70b-versatile",
    "uptime_seconds": 120,
    "avg_response_time_seconds": 1.4,
    "total_requests_tracked": 5
}
```

---

### POST /describe
Generate an AI description of a role and its risk level.

**Request Body:**
```json
{
    "role_name": "Admin",
    "permissions": "read, write, delete",
    "department": "IT"
}
```

**Response:**
```json
{
    "description": "The Admin role grants full access...",
    "risk_level": "high",
    "summary": "Full access admin role for IT.",
    "generated_at": "2026-05-03T07:00:00+00:00",
    "is_fallback": false,
    "from_cache": false
}
```

---

### POST /recommend
Get 3 security recommendations for a role.

**Request Body:**
```json
{
    "role_name": "Admin",
    "permissions": "read, write, delete",
    "department": "IT",
    "risk_level": "high"
}
```

**Response:**
```json
{
    "recommendations": [
        {
            "action_type": "enforce",
            "description": "Require MFA for all Admin users.",
            "priority": "high"
        },
        {
            "action_type": "audit",
            "description": "Review admin access quarterly.",
            "priority": "high"
        },
        {
            "action_type": "reduce",
            "description": "Apply least privilege principles.",
            "priority": "medium"
        }
    ],
    "from_cache": false
}
```

---

### POST /generate-report
Generate a full security report for a role.

**Request Body:**
```json
{
    "role_name": "Admin",
    "permissions": "read, write, delete",
    "department": "IT",
    "risk_level": "high",
    "description": "Full system admin access"
}
```

**Response:**
```json
{
    "title": "Security Report — Admin",
    "summary": "The Admin role carries high risk...",
    "overview": "This role provides unrestricted access...",
    "key_items": [
        "Has delete permissions which are irreversible",
        "Can manage other user accounts",
        "Requires MFA enforcement"
    ],
    "recommendations": [
        {
            "action_type": "enforce",
            "description": "Require MFA for all Admin users.",
            "priority": "high"
        }
    ],
    "generated_at": "2026-05-03T07:00:00+00:00",
    "is_fallback": false,
    "from_cache": false
}
```

---

## Security Features

- Input sanitization — blocks prompt injection attacks
- Rate limiting — 30 requests per minute per IP
- Security headers — X-Frame-Options, CSP, HSTS and more
- Fallback responses — never returns HTTP 500

---

## Caching

All AI responses are cached in Redis with a 15 minute TTL.
If Redis is unavailable the app continues working without cache.

---

## Fallback Behaviour

If Groq API is unavailable all endpoints return a safe fallback
response with `is_fallback: true` instead of crashing.