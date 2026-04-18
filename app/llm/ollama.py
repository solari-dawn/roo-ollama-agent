from langchain_community.llms import Ollama
from app.config import OLLAMA_BASE_URL, TEMPERATURE

def get_llm(model):
    return Ollama(
        model=model,
        base_url=OLLAMA_BASE_URL,
        temperature=TEMPERATURE
    )