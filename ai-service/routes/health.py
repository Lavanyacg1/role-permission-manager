from flask import Blueprint, jsonify
import time

health_bp = Blueprint("health", __name__)
START_TIME = time.time()

response_times = []

def record_response_time(duration: float):
    response_times.append(duration)
    if len(response_times) > 100:
        response_times.pop(0)

def get_avg_response_time() -> float:
    if not response_times:
        return 0.0
    return round(sum(response_times) / len(response_times), 3)

@health_bp.route("/health", methods=["GET"])
def health():
    uptime_seconds = int(time.time() - START_TIME)
    return jsonify({
        "status": "ok",
        "model": "llama-3.3-70b-versatile",
        "uptime_seconds": uptime_seconds,
        "avg_response_time_seconds": get_avg_response_time(),
        "total_requests_tracked": len(response_times)
    }), 200