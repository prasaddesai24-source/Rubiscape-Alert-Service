"""
Natural Language Rule Parser — converts plain English prompts into structured alert rules
using Google Gemini API. Example: "Alert if latency > 300ms" → {metric, operator, threshold, severity}
"""

import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


def parse_rule_from_text(prompt: str) -> dict:
    """
    Parse a plain-English rule description into a structured rule dict.

    Args:
        prompt: Human-readable rule description (e.g. "Alert me if error_rate exceeds 5%")

    Returns:
        Dict with keys: metric, operator, threshold, severity

    Raises:
        ValueError: if parsing fails or API key not set.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured. Add it to your .env file.")

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        extraction_prompt = (
            "You are an API that extracts monitoring rule parameters from natural language.\n"
            "Given the user's description, extract exactly these fields:\n"
            "- metric: the metric name (snake_case, e.g. latency, error_rate, gpu_memory, cpu_usage, disk_usage, throughput)\n"
            "- operator: one of >, <, >=, <=, ==\n"
            "- threshold: numeric value (float)\n"
            "- severity: one of LOW, MEDIUM, HIGH, CRITICAL\n\n"
            "Return ONLY a valid JSON object with these 4 keys. No explanation, no markdown.\n\n"
            f"User input: \"{prompt}\"\n\n"
            "JSON:"
        )

        response = model.generate_content(extraction_prompt)
        raw = response.text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        rule_data = json.loads(raw)

        # Validate required fields
        required = {"metric", "operator", "threshold", "severity"}
        if not required.issubset(rule_data.keys()):
            raise ValueError(f"Missing required fields in parsed rule: {rule_data}")

        # Ensure types
        rule_data["threshold"] = float(rule_data["threshold"])
        rule_data["severity"] = str(rule_data["severity"]).upper()

        logger.info(f"[NL Parser] ✅ Parsed rule from text: {rule_data}")
        return rule_data

    except json.JSONDecodeError as e:
        logger.error(f"[NL Parser] JSON decode error: {e}")
        raise ValueError(f"Could not parse Gemini response as JSON. Try rephrasing your prompt.")
    except Exception as e:
        logger.error(f"[NL Parser] Error: {e}")
        raise ValueError(f"Rule parsing failed: {str(e)}")
