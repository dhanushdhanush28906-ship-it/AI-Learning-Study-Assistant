"""
Thin SQLite access layer. No ORM — plain sqlite3 with row factories,
kept simple so it's easy to reason about and swap out later.
"""
import sqlite3
import json
from contextlib import contextmanager
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import SQLITE_PATH

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def init_db():
    """Create tables if they don't already exist."""
    with get_conn() as conn:
        conn.executescript(SCHEMA_PATH.read_text())


@contextmanager
def get_conn():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# --- Students ------------------------------------------------------------
def get_or_create_student(name: str) -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT student_id FROM students WHERE name = ?", (name,)).fetchone()
        if row:
            return row["student_id"]
        cur = conn.execute("INSERT INTO students (name) VALUES (?)", (name,))
        return cur.lastrowid


# --- Documents -------------------------------------------------------------
def add_document(student_id: int, filename: str, topic: str, num_chunks: int) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO documents (student_id, filename, topic, num_chunks) VALUES (?, ?, ?, ?)",
            (student_id, filename, topic, num_chunks),
        )
        return cur.lastrowid


def list_documents(student_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM documents WHERE student_id = ? ORDER BY uploaded_at DESC", (student_id,)
        ).fetchall()


# --- Conversations (long-term memory log) -----------------------------------
def log_message(student_id: int, role: str, content: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO conversations (student_id, role, content) VALUES (?, ?, ?)",
            (student_id, role, content),
        )


def get_recent_messages(student_id: int, limit: int):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT role, content FROM conversations WHERE student_id = ? "
            "ORDER BY conversation_id DESC LIMIT ?",
            (student_id, limit),
        ).fetchall()
        return list(reversed(rows))  # chronological order


# --- Quizzes -----------------------------------------------------------------
def create_quiz(student_id: int, topic: str, difficulty: str, questions: list) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO quizzes (student_id, topic, difficulty, num_questions) VALUES (?, ?, ?, ?)",
            (student_id, topic, difficulty, len(questions)),
        )
        quiz_id = cur.lastrowid
        for q in questions:
            conn.execute(
                """INSERT INTO quiz_questions
                   (quiz_id, question_text, option_a, option_b, option_c, option_d,
                    correct_option, explanation)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (quiz_id, q["question"], q["options"]["A"], q["options"]["B"],
                 q["options"]["C"], q["options"]["D"], q["correct_option"],
                 q.get("explanation", "")),
            )
        return quiz_id


def get_quiz_questions(quiz_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM quiz_questions WHERE quiz_id = ?", (quiz_id,)
        ).fetchall()


def record_answer(question_id: int, student_answer: str, is_correct: bool):
    with get_conn() as conn:
        conn.execute(
            "UPDATE quiz_questions SET student_answer = ?, is_correct = ? WHERE question_id = ?",
            (student_answer, int(is_correct), question_id),
        )


def get_quiz_topic(quiz_id: int):
    with get_conn() as conn:
        row = conn.execute("SELECT topic FROM quizzes WHERE quiz_id = ?", (quiz_id,)).fetchone()
        return row["topic"] if row else None


# --- Progress ------------------------------------------------------------------
def update_progress(student_id: int, topic: str, score_pct: float):
    """Roll a new quiz score into the running average for a topic."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM progress WHERE student_id = ? AND topic = ?", (student_id, topic)
        ).fetchone()
        if row is None:
            avg = score_pct
            taken = 1
        else:
            taken = row["quizzes_taken"] + 1
            avg = ((row["avg_score"] * row["quizzes_taken"]) + score_pct) / taken

        needs_revision = 1 if avg < 60 else 0

        conn.execute(
            """INSERT INTO progress (student_id, topic, quizzes_taken, avg_score, last_score, needs_revision)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(student_id, topic) DO UPDATE SET
                 quizzes_taken = excluded.quizzes_taken,
                 avg_score = excluded.avg_score,
                 last_score = excluded.last_score,
                 needs_revision = excluded.needs_revision,
                 updated_at = datetime('now')""",
            (student_id, topic, taken, avg, score_pct, needs_revision),
        )


def get_progress(student_id: int):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM progress WHERE student_id = ? ORDER BY avg_score ASC", (student_id,)
        ).fetchall()


def get_weak_topics(student_id: int, threshold: float = 60.0):
    with get_conn() as conn:
        return conn.execute(
            "SELECT topic, avg_score FROM progress WHERE student_id = ? AND avg_score < ? "
            "ORDER BY avg_score ASC",
            (student_id, threshold),
        ).fetchall()


# --- Study Plans -------------------------------------------------------------
def save_study_plan(student_id: int, plan: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO study_plans (student_id, plan_json) VALUES (?, ?)",
            (student_id, json.dumps(plan)),
        )
        return cur.lastrowid


def get_latest_plan(student_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT plan_json FROM study_plans WHERE student_id = ? ORDER BY created_at DESC LIMIT 1",
            (student_id,),
        ).fetchone()
        return json.loads(row["plan_json"]) if row else None
