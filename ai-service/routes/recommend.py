import json
import re
import logging
import time
from flask import Blueprint, request, jsonify
from services.groq_client import call_groq
from services.cache import make_cache_key, get_cached, set_cached
from routes.health import record_response_time

logger = logging.getLogger(__name__)
recommend_bp = Blueprint("recommend", __name__)

REQUIRED_FIELDS = ["role_name", "permissions", "department"]
FALLBACK_RECOMMENDATIONS = [
    {"action_type": "audit",    "description": "Conduct a quarterly review of this role's permissions.", "priority": "medium"},
    {"action_type": "document", "description": "Ensure all permissions are documented with justification.", "priority": "low"},
    {"action_type": "review",   "description": "Verify the role adheres to least-privilege principles.", "priority": "high"},
]

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

    # Check cache first
    cache_key = make_cache_key("recommend", {
        "role_name": role_name,
        "permissions": permissions,
        "department": department,
        "risk_level": risk_level
    })
    cached = get_cached(cache_key)
    if cached:
        cached["from_cache"] = True
        return jsonify(cached), 200

    # Call Groq and track time
    start = time.time()
    prompt   = load_prompt(role_name, permissions, department, risk_level)
    messages = [{"role": "user", "content": prompt}]

    try:
        raw = call_groq(messages, temperature=0.4)
        duration = time.time() - start
        record_response_time(duration)

        recommendations = json.loads(raw)
        if not isinstance(recommendations, list) or len(recommendations) < 1:
            raise ValueError("Expected a JSON array")

        result = {"recommendations": recommendations[:3], "from_cache": False}
        set_cached(cache_key, result)
        return jsonify(result), 200

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"/recommend parse error: {e} | raw: {raw}")
        return jsonify({"recommendations": FALLBACK_RECOMMENDATIONS, "is_fallback": True}), 200
    except RuntimeError as e:
        logger.error(f"/recommend Groq failure: {e}")
        return jsonify({"recommendations": FALLBACK_RECOMMENDATIONS, "is_fallback": True}), 200