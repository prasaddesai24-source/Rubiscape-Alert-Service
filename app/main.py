"""
Enterprise AI Workflow Notification & Alerting Service
──────────────────────────────────────────────────────

Main application entry point — fully enhanced with:
- JWT Authentication
- Rate Limiting (slowapi)
- WebSocket real-time alerts
- AI Anomaly Detection
- AI Runbook Generation (Gemini)
- Natural Language Rule Creation
- Slack + Webhook Notifications
- Alert Lifecycle Management
"""

import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.database import engine, Base

# ── Import all models so Base.metadata knows about them ───────
from app.models.rule import Rule        # noqa: F401
from app.models.event import Event      # noqa: F401
from app.models.alert import Alert      # noqa: F401
from app.models.user import User        # noqa: F401

# ── Import route modules ─────────────────────────────────────
from app.routes import rule_routes, event_routes, alert_routes, dashboard_routes
from app.routes import auth_routes, ws_routes

# ── Rate Limiter ─────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ── Logging Configuration ────────────────────────────────────
def configure_logging():
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


configure_logging()
logger = logging.getLogger(__name__)


# ── Application Lifespan ─────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ready ✅")
    logger.info("Rubiscape Alert Service v2.0 is running 🚀")
    logger.info("New features: JWT Auth | WebSockets | AI Anomaly Detection | LLM Runbooks | NL Rules")
    yield
    logger.info("Shutting down Rubiscape Alert Service...")


# ── FastAPI Application ──────────────────────────────────────
app = FastAPI(
    title="Rubiscape Alert Service",
    description=(
        "Enterprise AI Workflow Notification & Alerting Service — v2.0\n\n"
        "**New Features:**\n"
        "- 🔐 JWT Authentication & RBAC\n"
        "- ⚡ Real-time WebSocket Alerts (`/ws/alerts`)\n"
        "- 🤖 AI Anomaly Detection (IsolationForest)\n"
        "- 📋 AI Runbook Generation (Google Gemini)\n"
        "- 💬 Natural Language Rule Creation (`POST /rules/from-text`)\n"
        "- 📣 Slack & Webhook Notifications\n"
        "- 🔄 Alert Lifecycle Management (Acknowledge / Resolve / Suppress)"
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Rate Limiting Middleware ─────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Static Files ─────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

# ── Register Routers ─────────────────────────────────────────
app.include_router(auth_routes.router)
app.include_router(rule_routes.router)
app.include_router(event_routes.router)
app.include_router(alert_routes.router)
app.include_router(dashboard_routes.router)
app.include_router(ws_routes.router)


# ── Root Endpoint ────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    """Health check and service info."""
    return {
        "service": "Rubiscape Alert Service",
        "version": "2.0.0",
        "status": "healthy",
        "features": [
            "JWT Auth", "Rate Limiting", "WebSockets",
            "AI Anomaly Detection", "LLM Runbooks", "NL Rule Creation",
            "Slack Notifications", "Alert Lifecycle Management"
        ],
        "docs": "/docs",
        "dashboard": "/dashboard",
        "websocket": "/ws/alerts",
    }
