import os
import json
import io
from dotenv import load_dotenv
from google.genai import errors
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-3.5-flash"


def analyze_image(image_bytes: bytes, description: str = ""):
    try:
        image = Image.open(io.BytesIO(image_bytes))

        prompt = f"""
Analyze this disaster evidence image and the user's description.

Description:
{description}

Return a disaster assessment.
Do not claim the disaster is officially confirmed.
"""

        response = client.models.generate_content(
            model=MODEL,
            contents=[image, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "OBJECT",
                    "properties": {
                        "disaster_type": {"type": "STRING"},
                        "likelihood": {"type": "STRING"},
                        "priority": {"type": "STRING"},
                        "reason": {"type": "STRING"},
                        "needs_human_verification": {"type": "BOOLEAN"},
                    },
                    "required": [
                        "disaster_type",
                        "likelihood",
                        "priority",
                        "reason",
                        "needs_human_verification",
                    ],
                },
            ),
        )

        return response.parsed

    except errors.ClientError as e:
        if e.code == 429:
            return {
                "disaster_type": "Flood",
                "likelihood": "Needs assessment",
                "priority": "Review required",
                "reason": "Gemini analysis is temporarily unavailable. CVDL analysis is available for this incident.",
                "needs_human_verification": True,
            }
        raise


def chat_with_gemini(question: str, incident: dict):
    try:
        prompt = f"""
Answer the responder's question using only this incident data:
{incident}

Question: {question}
Keep the answer short and clear.
"""
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        return response.text

    except errors.ClientError as e:
        if e.code == 429:
            return fallback_answer(question, incident)
        raise

def fallback_answer(question: str, incident: dict):
    q = question.lower()
    ai = incident.get("ai_assessment") or {}
    cv = incident.get("cvdl") or {}

    if "severity" in q or "flood" in q or "cvdl" in q:
        return (
            f"Flood severity is {cv.get('severity_level', 'N/A')}, "
            f"with {cv.get('flood_coverage_pct', 0)}% flood coverage "
            f"and a severity score of {cv.get('severity_score', 0)}/100."
        )

    if "priority" in q:
        return f"Priority is {ai.get('priority', 'N/A')}. {ai.get('reason', '')}"

    if "summarize" in q or "incident" in q:
        return (
            f"{ai.get('disaster_type', 'N/A')} — "
            f"{ai.get('priority', 'N/A')} priority. "
            f"CVDL severity: {cv.get('severity_level', 'N/A')}."
        )

    return "AI assistant is temporarily unavailable. Please review the incident assessment."