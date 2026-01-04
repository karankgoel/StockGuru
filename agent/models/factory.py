import os
from google.adk.models.base_llm import BaseLlm

def get_model() -> BaseLlm:
    # Default to Gemini Pro
    model_name = os.environ.get("LLM_MODEL", "gemini-2.5-flash")
    print(f"Using Google model: {model_name}")
    return model_name
