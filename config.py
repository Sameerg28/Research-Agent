import os

from dotenv import load_dotenv

load_dotenv()


def _int_from_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_TOKENS = _int_from_env("MAX_TOKENS", 6000)
MAX_RETRIES = _int_from_env("MAX_RETRIES", 3)
CHUNK_SIZE = _int_from_env("CHUNK_SIZE", 3000)

DEFAULT_RESEARCH_BREADTH = _int_from_env("RESEARCH_BREADTH", 3)
DEFAULT_RESEARCH_DEPTH = _int_from_env("RESEARCH_DEPTH", 2)
DEFAULT_SEARCH_LIMIT = _int_from_env("SEARCH_LIMIT", 4)
DEFAULT_FOLLOW_UP_QUESTIONS = _int_from_env("FOLLOW_UP_QUESTIONS", 3)
DEFAULT_LEARNINGS_PER_QUERY = _int_from_env("LEARNINGS_PER_QUERY", 3)
SEARCH_TIMEOUT = _int_from_env("SEARCH_TIMEOUT", 20)
REPORT_MAX_LEARNINGS = _int_from_env("REPORT_MAX_LEARNINGS", 18)
