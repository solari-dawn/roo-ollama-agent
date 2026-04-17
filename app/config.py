
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
PLANNER_MODEL = os.getenv("PLANNER_MODEL")
EXECUTOR_MODEL = os.getenv("EXECUTOR_MODEL")
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.1))
MAX_STEPS = int(os.getenv("MAX_STEPS", 5))
