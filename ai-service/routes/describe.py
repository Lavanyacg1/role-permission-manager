import json
import re
import logging
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from services.groq_client import call_groq

logger = logging.getLogger(__name__)
describe_bp = Blueprint("describe", __name__)

REQUIRED_FIELDS = ["role_name", "permissions", "department"]

def load_prompt(role_name, permissions, department) -> str:
    with open("prompts/describe.txt", "r") as f:
        template = f.read()
    return template.format(
        role_name=role_name,
        permissions=permissions,
        department=department
    )

def sanitize(value: str) -> str:
    """Strip HTML tags and basic prompt injection patterns."""
    # Strip HTML tags
    value = re.sub(r"<[^>]+>", "", value)
    
    # Block full sentence injection attempts — if detected, replace entire value
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
            return "unknown"   # ← entire value replaced, nothing leaks through
    
    return value.strip()

@describe_bp.route("/describe", methods=["POST"])
def describe():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be JSON"}), 400

    # Validate required fields
    missing = [f for f in REQUIRED_FIELDS if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    # Sanitize inputs
    role_name   = sanitize(str(data["role_name"]))
    permissions = sanitize(str(data["permissions"]))
    department  = sanitize(str(data["department"]))

    prompt = load_prompt(role_name, permissions, department)
    messages = [{"role": "user", "content": prompt}]

    try:
        raw = call_groq(messages, temperature=0.3)
        result = json.loads(raw)
        result["generated_at"] = datetime.now(timezone.utc).isoformat()
        result["is_fallback"] = False
        return jsonify(result), 200
    except json.JSONDecodeError:
        logger.error(f"Groq returned non-JSON: {raw}")
        return jsonify({
            "description": "Unable to generate description at this time.",
            "risk_level": "unknown",
            "summary": "AI service returned an unexpected response.",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "is_fallback": True
        }), 200
    except RuntimeError as e:
        logger.error(f"/describe Groq failure: {e}")
        return jsonify({
            "description": "AI service temporarily unavailable.",
            "risk_level": "unknown",
            "summary": "Fallback response — Groq unavailable.",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "is_fallback": True
        }), 200