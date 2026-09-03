import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = "gemini-3.5-flash"


def analyze_image(image_path, description=""):
    image = Image.open(image_path)

    prompt = f"""
You are a disaster assessment AI assistant.

Analyze the submitted image and the user's description.

User description:
{description}

Return a disaster assessment.

Do not claim that the disaster is officially confirmed.
The result is an AI assessment and must be verified by a human responder.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=[image, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "disaster_type": {
                        "type": "STRING"
                    },
                    "likelihood": {
                        "type": "STRING"
                    },
                    "priority": {
                        "type": "STRING"
                    },
                    "reason": {
                        "type": "STRING"
                    },
                    "needs_human_verification": {
                        "type": "BOOLEAN"
                    }
                },
                "required": [
                    "disaster_type",
                    "likelihood",
                    "priority",
                    "reason",
                    "needs_human_verification"
                ]
            }
        )
    )

    return response.parsed


def transcribe_audio(audio_path):
    audio = client.files.upload(file=audio_path)

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            audio,
            "Transcribe this audio exactly. Return only the spoken text."
        ]
    )

    return response.text