"""
Quiz generation tool.

Grounding matters here: questions are generated strictly from retrieved
chunks of the student's own material, not from the model's parametric
knowledge, to avoid hallucinated MCQs.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import DEFAULT_QUIZ_SIZE
from rag.retriever import retrieve, format_context
from tools.llm import call_llm_json
from database import db

QUIZ_SYSTEM_PROMPT = """You are a study-quiz generator. You must create multiple-choice \
questions using ONLY the facts present in the provided source material. \
Never introduce facts that aren't in the sources. If the sources don't contain \
enough information for a good question, write a question about what IS there \
rather than inventing content."""

QUIZ_PROMPT_TEMPLATE = """Source material:
{context}

Generate {n} multiple-choice questions at {difficulty} difficulty about the topic "{topic}".

Return ONLY a JSON array, no other text, in this exact format:
[
  {{
    "question": "...",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "correct_option": "A",
    "explanation": "one sentence explaining why, referencing the source material"
  }}
]
"""


def generate_quiz(
    student_id: int,
    topic: str,
    num_questions: int = DEFAULT_QUIZ_SIZE,
    difficulty: str = "medium",
) -> dict:
    """
    Retrieves relevant material for `topic` and generates a grounded MCQ quiz.
    Persists the quiz to SQLite and returns {quiz_id, questions}.
    """
    hits = retrieve(query=topic, student_id=student_id, topic=None, k=6)
    if not hits:
        raise ValueError(
            f"No study material found for topic '{topic}'. Upload notes/PDFs on this topic first."
        )
    context = format_context(hits)

    prompt = QUIZ_PROMPT_TEMPLATE.format(
        context=context, n=num_questions, difficulty=difficulty, topic=topic
    )
    questions = call_llm_json(prompt, system=QUIZ_SYSTEM_PROMPT)

    if not isinstance(questions, list) or not questions:
        raise ValueError("Quiz generation failed to produce valid questions.")

    quiz_id = db.create_quiz(student_id, topic, difficulty, questions)
    return {"quiz_id": quiz_id, "questions": questions}


def submit_quiz_answers(quiz_id: int, student_id: int, answers: dict) -> dict:
    """
    answers: {question_id (int): "A"/"B"/"C"/"D"}
    Grades the quiz, records per-question results, and rolls the score
    into the student's topic progress (closing the agentic feedback loop).
    """
    questions = db.get_quiz_questions(quiz_id)
    if not questions:
        raise ValueError(f"Quiz {quiz_id} not found.")

    correct_count = 0
    results = []
    for q in questions:
        qid = q["question_id"]
        given = answers.get(qid) or answers.get(str(qid))
        is_correct = (given == q["correct_option"])
        db.record_answer(qid, given or "", is_correct)
        if is_correct:
            correct_count += 1
        results.append({
            "question_id": qid,
            "question": q["question_text"],
            "given_answer": given,
            "correct_answer": q["correct_option"],
            "is_correct": is_correct,
            "explanation": q["explanation"],
        })

    score_pct = round(100 * correct_count / len(questions), 1)
    topic = db.get_quiz_topic(quiz_id)
    db.update_progress(student_id, topic, score_pct)

    return {
        "quiz_id": quiz_id,
        "topic": topic,
        "score_pct": score_pct,
        "correct": correct_count,
        "total": len(questions),
        "results": results,
    }
