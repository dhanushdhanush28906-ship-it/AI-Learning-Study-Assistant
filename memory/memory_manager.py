"""
Memory for the study assistant has two layers:

1. Short-term (working) memory — the last N conversation turns, kept in
   SQLite and pulled back out to give the LLM immediate context.
2. Long-term memory — progress/quiz history, which lives in the
   `progress` and `quizzes` tables and is summarized into the prompt
   when relevant (e.g. weak topics), rather than replayed turn-by-turn.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import MEMORY_WINDOW_TURNS
from database import db


def remember(student_id: int, role: str, content: str):
    """Persist a single conversational turn."""
    db.log_message(student_id, role, content)


def get_conversation_window(student_id: int) -> list[dict]:
    """Return the recent conversation as a list of {role, content} dicts."""
    rows = db.get_recent_messages(student_id, MEMORY_WINDOW_TURNS)
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def get_long_term_summary(student_id: int) -> str:
    """
    Summarize durable facts the agent should know regardless of the
    current conversation: weak topics, overall progress.
    This gets injected into the system prompt, not replayed as chat turns.
    """
    weak = db.get_weak_topics(student_id)
    progress_rows = db.get_progress(student_id)

    if not progress_rows:
        return "No quiz history yet for this student."

    lines = ["Student progress summary:"]
    for row in progress_rows:
        flag = " (NEEDS REVISION)" if row["needs_revision"] else ""
        lines.append(
            f"- {row['topic']}: avg {row['avg_score']:.0f}% over "
            f"{row['quizzes_taken']} quiz(zes){flag}"
        )
    if weak:
        topics = ", ".join(r["topic"] for r in weak)
        lines.append(f"Weakest topics needing revision: {topics}")
    return "\n".join(lines)


def build_chat_history_for_llm(student_id: int) -> list[dict]:
    """Convenience wrapper the agent graph calls each turn."""
    return get_conversation_window(student_id)
