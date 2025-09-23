import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_EMBED = os.getenv("MODEL_EMBED", "text-embedding-3-small")
MODEL_CHAT = os.getenv("MODEL_CHAT", "gpt-4o-mini")

DB_PATH = os.getenv("DB_PATH", "app.db")
FAISS_PATH = os.getenv("FAISS_PATH", "index/faiss.index")

# Chunking
CHUNK_TOKENS = int(os.getenv("CHUNK_TOKENS", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
