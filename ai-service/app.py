import os
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()
# ── Pre-load AI model at startup ──────────────────────────
from services.embeddings import load_model
load_model()

# ── Seed ChromaDB at startup ──────────────────────────────
from services.chromadb_service import seed_knowledge
seed_knowledge()

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["30 per minute"],
    storage_uri=os.getenv("REDIS_URL", "memory://")
)

# ── Security Headers ──────────────────────────────────────
@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

# ── Error Handlers ────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return {"error": "Resource not found"}, 404

@app.errorhandler(405)
def method_not_allowed(e):
    return {"error": "Method not allowed"}, 405

@app.errorhandler(429)
def rate_limit_exceeded(e):
    return {"error": "Rate limit exceeded. Try again later."}, 429

@app.errorhandler(500)
def internal_error(e):
    return {"error": "Internal server error"}, 500

# ── Blueprints ────────────────────────────────────────────
from routes.describe import describe_bp
from routes.recommend import recommend_bp
from routes.health import health_bp
from routes.report import report_bp

app.register_blueprint(describe_bp)
app.register_blueprint(recommend_bp)
app.register_blueprint(health_bp)
app.register_blueprint(report_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
    