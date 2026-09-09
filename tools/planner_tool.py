"""
Study planner tool.

Generates a personalized schedule that prioritizes topics the student is
weak in (per the `progress` table) over topics they've already mastered —
this is the piece that closes the loop between quiz results and future
study time.
"""
import sys
from pathlib import Path
from datetime import date, timedelta

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DEFAULT_SESSION_MINUTES, DEFAULT_BREAK_MINUTES
from database import db


def _priority_order(student_id: int, available_topics: list[str]) -> list[dict]:
    """
    Ranks topics: weakest average quiz score first, topics never quizzed
    on get a neutral mid-priority so they still get scheduled.
    """
    progress_rows = {r["topic"]: r for r in db.get_progress(student_id)}
    ranked = []
    for topic in available_topics:
        row = progress_rows.get(topic)
        avg_score = row["avg_score"] if row else 50.0  # unknown = assume needs practice
        needs_revision = bool(row["needs_revision"]) if row else False
        ranked.append({"topic": topic, "avg_score": avg_score, "needs_revision": needs_revision})
    ranked.sort(key=lambda r: r["avg_score"])
    return ranked


def generate_study_plan(
    student_id: int,
    topics: list[str],
    days_available: int,
    hours_per_day: float,
    session_minutes: int = DEFAULT_SESSION_MINUTES,
    break_minutes: int = DEFAULT_BREAK_MINUTES,
) -> dict:
    """
    Builds a day-by-day schedule across `days_available` days, allocating
    more sessions to weaker topics. Returns a plan dict and persists it.
    """
    if not topics:
        raise ValueError("No topics provided for the study plan.")

    ranked_topics = _priority_order(student_id, topics)
    minutes_per_day = int(hours_per_day * 60)
    block = session_minutes + break_minutes
    sessions_per_day = max(1, minutes_per_day // block)

    # Weighted round-robin: weaker topics (earlier in ranked_topics) get
    # picked more often by cycling with duplicated weight for revision topics.
    weighted_cycle = []
    for i, t in enumerate(ranked_topics):
        weight = 3 if t["needs_revision"] else (2 if i < len(ranked_topics) / 2 else 1)
        weighted_cycle.extend([t["topic"]] * weight)

    schedule = []
    cycle_idx = 0
    start = date.today()
    for day_offset in range(days_available):
        day_date = start + timedelta(days=day_offset + 1)
        day_sessions = []
        for _ in range(sessions_per_day):
            topic = weighted_cycle[cycle_idx % len(weighted_cycle)]
            cycle_idx += 1
            day_sessions.append({
                "topic": topic,
                "duration_minutes": session_minutes,
                "break_minutes": break_minutes,
            })
        schedule.append({"date": day_date.isoformat(), "sessions": day_sessions})

    plan = {
        "topics": topics,
        "days_available": days_available,
        "hours_per_day": hours_per_day,
        "priority_order": [t["topic"] for t in ranked_topics],
        "schedule": schedule,
    }
    plan_id = db.save_study_plan(student_id, plan)
    plan["plan_id"] = plan_id
    return plan
