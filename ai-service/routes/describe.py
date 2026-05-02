import json
import re
import logging
import time
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from services.groq_client import call_groq
from services.cache import make_cache_key, get_cached, set_cached
from routes.health import record_response_time

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

@describe_bp.route("/describe", methods=["POST"])
def describe():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be JSON"}), 400

    missing = [f for f in REQUIRED_FIELDS if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    role_name   = sanitize(str(data["role_name"]))
    permissions = sanitize(str(data["permissions"]))
    department  = sanitize(str(data["department"]))

    # Check cache first
    cache_key = make_cache_key("describe", {
        "role_name": role_name,
        "permissions": permissions,
        "department": department
    })
    cached = get_cached(cache_key)
    if cached:
        cached["from_cache"] = True
        return jsonify(cached), 200

    # Call Groq and track time
    start = time.time()
    prompt   = load_prompt(role_name, permissions, department)
    messages = [{"role": "user", "content": prompt}]

    try:
        raw = call_groq(messages, temperature=0.3)
        duration = time.time() - start
        record_response_time(duration)

        result = json.loads(raw)
        result["generated_at"] = datetime.now(timezone.utc).isoformat()
        result["is_fallback"] = False
        result["from_cache"] = False

        set_cached(cache_key, result)
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