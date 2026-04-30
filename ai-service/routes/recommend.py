import json
import re
import logging
from flask import Blueprint, request, jsonify
from services.groq_client import call_groq

logger = logging.getLogger(__name__)
recommend_bp = Blueprint("recommend", __name__)

REQUIRED_FIELDS = ["role_name", "permissions", "department"]
FALLBACK_RECOMMENDATIONS = [
    {"action_type": "audit",    "description": "Conduct a quarterly review of this role's permissions.", "priority": "medium"},
    {"action_type": "document", "description": "Ensure all permissions are documented with justification.", "priority": "low"},
    {"action_type": "review",   "description": "Verify the role adheres to least-privilege principles.", "priority": "high"},
]

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

def load_prompt(role_name, permissions, department, risk_level) -> str:
    with open("prompts/recommend.txt", "r") as f:
        template = f.read()
    return template.format(
        role_name=role_name,
        permissions=permissions,
        department=department,
        risk_level=risk_level
    )

@recommend_bp.route("/recommend", methods=["POST"])
def recommend():
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

    prompt   = load_prompt(role_name, permissions, department, risk_level)
    messages = [{"role": "user", "content": prompt}]

    try:
        raw = call_groq(messages, temperature=0.4)
        recommendations = json.loads(raw)
        if not isinstance(recommendations, list) or len(recommendations) < 1:
            raise ValueError("Expected a JSON array")
        return jsonify({"recommendations": recommendations[:3]}), 200
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"/recommend parse error: {e} | raw: {raw}")
        return jsonify({"recommendations": FALLBACK_RECOMMENDATIONS, "is_fallback": True}), 200
    except RuntimeError as e:
        logger.error(f"/recommend Groq failure: {e}")
        return jsonify({"recommendations": FALLBACK_RECOMMENDATIONS, "is_fallback": True}), 200