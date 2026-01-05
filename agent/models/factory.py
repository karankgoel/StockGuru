import os
from google.adk.models.base_llm import BaseLlm
from google.adk.models import Gemini

def get_model() -> BaseLlm:
    # Default to Gemini 2.0 Flash
    model_name = os.environ.get("LLM_MODEL", "gemini-2.0-flash")
    print(f"Using Google model: {model_name}")
    return Gemini(model=model_name)
