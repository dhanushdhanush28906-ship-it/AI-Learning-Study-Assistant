"""
Retrieval layer for RAG: given a query, pull the most relevant chunks
for a given student (and optionally a specific topic) out of ChromaDB.
"""
import sys
from pathlib import Path
from typing import Optional

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import RETRIEVAL_K
from rag.ingest import get_collection, get_embeddings


def retrieve(query: str, student_id: int, topic: Optional[str] = None, k: int = RETRIEVAL_K):
    """
    Returns a list of dicts: {text, source, topic, score}
    Scoped to the given student's own uploaded materials (and optionally one topic).
    """
    collection = get_collection()
    embeddings_model = get_embeddings()
    query_vector = embeddings_model.embed_query(query)

    where_filter = {"student_id": str(student_id)}
    if topic:
        where_filter = {"$and": [where_filter, {"topic": topic}]}

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=k,
        where=where_filter,
    )

    if not results["documents"] or not results["documents"][0]:
        return []

    hits = []
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results.get("distances", [[None] * len(docs)])[0]
    for doc, meta, dist in zip(docs, metas, distances):
        hits.append({
            "text": doc,
            "source": meta.get("source"),
            "topic": meta.get("topic"),
            "score": dist,
        })
    return hits


def format_context(hits: list) -> str:
    """Turn retrieved chunks into a citation-friendly context block for the LLM prompt."""
    if not hits:
        return "No relevant material found in the student's uploaded documents."
    blocks = []
    for i, h in enumerate(hits, 1):
        blocks.append(f"[Source {i}: {h['source']} | Topic: {h['topic']}]\n{h['text']}")
    return "\n\n".join(blocks)
