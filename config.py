"""Settings read from the environment. Nothing secret lives in the code."""
import os

from dotenv import load_dotenv

load_dotenv()


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set. Copy .env.example to .env and fill it in.")
    return value


SLACK_WORKSPACE_URL = os.getenv("SLACK_WORKSPACE_URL", "your-workspace.slack.com")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "slack-rag-assistant")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "mxbai-embed-large")
