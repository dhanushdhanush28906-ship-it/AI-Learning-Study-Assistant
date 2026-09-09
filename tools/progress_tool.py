"""
Progress tracking tool: read-side reporting over quiz history.
Writing progress happens in quiz_tool.submit_quiz_answers (the actual
feedback-loop update); this module is for querying/summarizing it.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from database import db


def get_progress_report(student_id: int) -> dict:
    rows = db.get_progress(student_id)
    weak = db.get_weak_topics(student_id)

    topics = [
        {
            "topic": r["topic"],
            "quizzes_taken": r["quizzes_taken"],
            "avg_score": round(r["avg_score"], 1),
            "last_score": r["last_score"],
            "needs_revision": bool(r["needs_revision"]),
        }
        for r in rows
    ]
    return {
        "topics": topics,
        "weak_topics": [w["topic"] for w in weak],
        "overall_avg": round(sum(t["avg_score"] for t in topics) / len(topics), 1) if topics else None,
    }
