import json
import os
import pandas as pd

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-3.6-flash"

CLASSIFY_PROMPT = (
      "Look at this image. Is it primarily a data table (rows and columns of "
    "structured data, like numbers, categories, or statistics)? "
    "Respond with ONLY the word 'yes' or 'no', nothing else."
)

EXCTRACT_PROMPT = (
    "Extract the data table in this image as JSON. Return ONLY a JSON object "
    "with this exact structure, nothing else, no markdown code fences: "
    '{"columns": ["col1", "col2"], "rows": [[val1, val2], [val1, val2]]}. '
    "Keep numbers as numbers (not strings) when possible."
)

def _get_client() -> genai.client:
    if not GEMINI_API_KEY:
        raise ValueError(
            "GEMINI_API_KEY not found. Add it to a .env file in the project folder"
        )
    return genai.Client(api_key=GEMINI_API_KEY)

def is_table_image(image_bytes: bytes) -> bool:
    client = _get_client()
    response = client.models.generate_content(
        model = MODEL_NAME,
        contents=[
            CLASSIFY_PROMPT,
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
        ],
    )
    answer = response.text.strip().lower()
    return answer.startswith("y")

def extract_table_from_image(image_bytes: bytes) -> pd.DataFrame:
    client = _get_client()
    response = client.models.generate_content(
        model = MODEL_NAME,
        contents=[
            EXCTRACT_PROMPT,
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),

        ],
    )

    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    data = json.loads(raw)
    return pd.DataFrame(data["rows"], columns=data["columns"])

if __name__ == "__main__":
    with open("test_table_image.png", "rb") as f:
        image_bytes = f.read()

    print("Is table?", is_table_image(image_bytes))
    df = extract_table_from_image(image_bytes)
    print(df)