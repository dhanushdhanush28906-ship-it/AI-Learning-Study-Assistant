"""
Ingestion pipeline: PDF/notes -> chunks -> embeddings -> ChromaDB.
"""
import sys
from pathlib import Path
from typing import Optional

sys.path.append(str(Path(__file__).resolve().parent.parent))

from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
import chromadb

from config import (
    CHROMA_DIR, CHROMA_COLLECTION_NAME, EMBEDDING_MODEL_NAME,
    CHUNK_SIZE, CHUNK_OVERLAP, UPLOAD_DIR,
)

_embeddings = None
_chroma_client = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    return _embeddings


def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _chroma_client


def get_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)


def extract_text_from_pdf(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


def chunk_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(text)


def ingest_file(
    file_path: Path,
    student_id: int,
    topic: Optional[str] = None,
) -> int:
    """
    Reads a PDF (or plain text) file, splits it into chunks, embeds them,
    and stores them in ChromaDB with student/topic metadata for filtered retrieval.
    Returns the number of chunks stored.
    """
    file_path = Path(file_path)
    topic = topic or file_path.stem

    if file_path.suffix.lower() == ".pdf":
        text = extract_text_from_pdf(file_path)
    else:
        text = file_path.read_text(errors="ignore")

    if not text.strip():
        raise ValueError(f"No extractable text found in {file_path.name}")

    chunks = chunk_text(text)
    embeddings_model = get_embeddings()
    vectors = embeddings_model.embed_documents(chunks)

    collection = get_collection()
    ids = [f"{student_id}_{file_path.stem}_{i}" for i in range(len(chunks))]
    metadatas = [
        {"student_id": str(student_id), "topic": topic, "source": file_path.name, "chunk_index": i}
        for i in range(len(chunks))
    ]

    collection.add(ids=ids, embeddings=vectors, documents=chunks, metadatas=metadatas)
    return len(chunks)


def save_upload(uploaded_bytes: bytes, filename: str) -> Path:
    """Persist an uploaded file to disk (used by the Streamlit uploader)."""
    dest = UPLOAD_DIR / filename
    dest.write_bytes(uploaded_bytes)
    return dest
