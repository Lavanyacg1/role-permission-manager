import json
import re
import logging
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from services.groq_client import call_groq

logger = logging.getLogger(__name__)
report_bp = Blueprint("report", __name__)

REQUIRED_FIELDS = ["role_name", "permissions", "department"]

def sanitize(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    injection_patterns = [
        r"ignore.{0,30}(above|previous|instruction)",
        r"forget.{0,30}(above|previous|instruction)",
        r"disregard.{0,30}(above|previous|instruction)",
        r"do not follow",
        r"new instruction",
        r"system prompt",
        r"you are now",
        r"pretend you",
        r"act as",
    ]
    for pattern in injection_patterns:
        if re.search(pattern, value, flags=re.IGNORECASE):
            return "unknown"
    return value.strip()

def load_prompt(role_name, permissions, department, risk_level, description) -> str:
    with open("prompts/report.txt", "r") as f:
        template = f.read()
    return template.format(
        role_name=role_name,
        permissions=permissions,
        department=department,
        risk_level=risk_level,
        description=description
    )

FALLBACK_REPORT = {
    "title": "Security Report — unknown",
    "summary": "Report could not be generated at this time.",
    "overview": "The AI service is temporarily unavailable.",
    "key_items": [
        "Manual review recommended",
        "Check role permissions carefully",
        "Ensure least privilege is applied"
    ],
    "recommendations": [
        {
            "action_type": "review",
            "description": "Manually review this role's permissions.",
            "priority": "high"
        }
    ],
    "is_fallback": True
}

@report_bp.route("/generate-report", methods=["POST"])
def generate_report():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be JSON"}), 400

    missing = [f for f in REQUIRED_FIELDS if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    role_name   = sanitize(str(data["role_name"]))
    permissions = sanitize(str(data["permissions"]))
    department  = sanitize(str(data["department"]))
    risk_level  = sanitize(str(data.get("risk_level", "medium")))
    description = sanitize(str(data.get("description", "No description provided")))

    prompt   = load_prompt(role_name, permissions, department, risk_level, description)
    messages = [{"role": "user", "content": prompt}]

    try:
        raw = call_groq(messages, temperature=0.3, max_tokens=500)
        result = json.loads(raw)
        result["generated_at"] = datetime.now(timezone.utc).isoformat()
        result["is_fallback"] = False
        return jsonify(result), 200
    except json.JSONDecodeError:
        logger.error(f"Groq returned non-JSON: {raw}")
        FALLBACK_REPORT["generated_at"] = datetime.now(timezone.utc).isoformat()
        return jsonify(FALLBACK_REPORT), 200
    except RuntimeError as e:
        logger.error(f"/generate-report Groq failure: {e}")
        FALLBACK_REPORT["generated_at"] = datetime.now(timezone.utc).isoformat()
        return jsonify(FALLBACK_REPORT), 200