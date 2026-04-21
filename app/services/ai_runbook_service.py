"""
AI Runbook Service — generates step-by-step remediation guides using Google Gemini.
Called for HIGH and CRITICAL alerts in a background thread.
"""

import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


def generate_runbook(service_name: str, metric: str, value: float, severity: str) -> str:
    """
    Call Google Gemini API to generate a remediation runbook for an alert.

    Args:
        service_name: Name of the affected AI service.
        metric: The metric that triggered the alert.
        value: The observed metric value.
        severity: Alert severity level.

    Returns:
        Runbook text string, or None if generation fails or API key not set.
    """
    if not settings.GEMINI_API_KEY:
        logger.info("[Runbook] GEMINI_API_KEY not set — skipping runbook generation.")
        return None

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = (
            f"You are a senior DevOps and AI systems engineer.\n"
            f"An AI service named '{service_name}' has triggered a {severity} alert.\n"
            f"The metric '{metric}' was observed at value {value}.\n\n"
            f"Provide a concise remediation runbook with exactly 5 numbered steps.\n"
            f"Each step must be a specific, actionable technical instruction.\n"
            f"Do not include any introduction or conclusion — only the 5 steps.\n"
            f"Format: 1. [Action]"
        )

        response = model.generate_content(prompt)
        runbook_text = response.text.strip()

        logger.info(f"[Runbook] ✅ Generated runbook for alert on '{service_name}' ({severity})")
        return runbook_text

    except Exception as e:
        logger.error(f"[Runbook] ❌ Gemini API call failed: {e}")
        return None
