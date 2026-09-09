"""
Central configuration for the AI Learning & Study Assistant.
Adjust these values to match your local environment.
"""
import os
from pathlib import Path

# --- Paths -------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma_db"
SQLITE_PATH = DATA_DIR / "study_assistant.db"

for d in (DATA_DIR, UPLOAD_DIR, CHROMA_DIR):
    d.mkdir(parents=True, exist_ok=True)

# --- Ollama / LLM --------------------------------------------------------
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")   # pull with: ollama pull qwen2.5:7b
LLM_TEMPERATURE = 0.3

# --- Embeddings ----------------------------------------------------------
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

# --- RAG / Chunking --------------------------------------------------------
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
RETRIEVAL_K = 4                # how many chunks to retrieve per query
CHROMA_COLLECTION_NAME = "study_materials"

# --- Memory ----------------------------------------------------------------
MEMORY_WINDOW_TURNS = 12       # how many recent conversation turns to keep in short-term memory

# --- Quiz --------------------------------------------------------------------
DEFAULT_QUIZ_SIZE = 5
QUIZ_DIFFICULTIES = ["easy", "medium", "hard"]

# --- Study Planner -----------------------------------------------------------
DEFAULT_SESSION_MINUTES = 45
DEFAULT_BREAK_MINUTES = 10
