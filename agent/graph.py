"""
Agentic workflow built with LangGraph.

The graph has one router node that classifies the student's intent, then
dispatches to the matching tool node. Each tool node writes its result
into shared state; a final "respond" node turns that into natural
language back to the student. This is the RAG + Memory + Tools + Agent
pattern from the project brief.
"""
import sys
from pathlib import Path
from typing import TypedDict, Optional, Literal

sys.path.append(str(Path(__file__).resolve().parent.parent))

from langgraph.graph import StateGraph, END

from tools.llm import call_llm, call_llm_json
from rag.retriever import retrieve, format_context
from tools.quiz_tool import generate_quiz
from tools.planner_tool import generate_study_plan
from tools.progress_tool import get_progress_report
from memory import memory_manager


class AgentState(TypedDict, total=False):
    student_id: int
    user_input: str
    intent: str
    topic: Optional[str]
    rag_context: Optional[str]
    tool_result: Optional[dict]
    response: str


INTENT_ROUTER_PROMPT = """Classify the student's message into exactly one category:
- "question": asking about study material / wants an explanation
- "quiz": wants a quiz/practice questions generated
- "plan": wants a study schedule/plan
- "progress": wants to know their progress/scores/weak topics
- "chitchat": greeting or anything not covered above

Message: "{message}"

Reply with ONLY the category word, nothing else."""


def route_intent(state: AgentState) -> AgentState:
    category = call_llm(
        INTENT_ROUTER_PROMPT.format(message=state["user_input"]),
        temperature=0.0,
    ).strip().lower()
    valid = {"question", "quiz", "plan", "progress", "chitchat"}
    state["intent"] = category if category in valid else "question"
    return state


def node_question(state: AgentState) -> AgentState:
    hits = retrieve(query=state["user_input"], student_id=state["student_id"])
    context = format_context(hits)
    history = memory_manager.get_conversation_window(state["student_id"])
    long_term = memory_manager.get_long_term_summary(state["student_id"])

    history_text = "\n".join(f"{h['role']}: {h['content']}" for h in history[-6:])
    system = (
        "You are a patient study tutor. Answer using the provided source material. "
        "If the material doesn't cover the question, say so honestly instead of guessing.\n\n"
        f"Student progress context:\n{long_term}"
    )
    prompt = (
        f"Recent conversation:\n{history_text}\n\n"
        f"Source material:\n{context}\n\n"
        f"Student's question: {state['user_input']}"
    )
    state["response"] = call_llm(prompt, system=system)
    return state


def node_quiz(state: AgentState) -> AgentState:
    topic = state.get("topic") or _extract_topic(state["user_input"])
    result = generate_quiz(student_id=state["student_id"], topic=topic)
    state["tool_result"] = result
    q_lines = [f"**Quiz: {topic}** ({len(result['questions'])} questions, quiz_id={result['quiz_id']})"]
    for i, q in enumerate(result["questions"], 1):
        q_lines.append(f"\n{i}. {q['question']}")
        for opt, text in q["options"].items():
            q_lines.append(f"   {opt}) {text}")
    state["response"] = "\n".join(q_lines)
    return state


def node_plan(state: AgentState) -> AgentState:
    parsed = call_llm_json(
        f'Extract study-plan parameters from: "{state["user_input"]}". '
        'Return JSON: {"topics": ["..."], "days_available": int, "hours_per_day": float}. '
        'If a value is missing, use sensible defaults (days_available=7, hours_per_day=2).',
        temperature=0.0,
    )
    plan = generate_study_plan(
        student_id=state["student_id"],
        topics=parsed.get("topics") or [state["user_input"]],
        days_available=parsed.get("days_available", 7),
        hours_per_day=parsed.get("hours_per_day", 2),
    )
    state["tool_result"] = plan
    lines = [f"**Study Plan** (priority order: {', '.join(plan['priority_order'])})"]
    for day in plan["schedule"]:
        sessions = ", ".join(f"{s['topic']} ({s['duration_minutes']}m)" for s in day["sessions"])
        lines.append(f"- {day['date']}: {sessions}")
    state["response"] = "\n".join(lines)
    return state


def node_progress(state: AgentState) -> AgentState:
    report = get_progress_report(state["student_id"])
    state["tool_result"] = report
    if not report["topics"]:
        state["response"] = "No quiz history yet — take a quiz first and I'll start tracking progress."
        return state
    lines = [f"**Progress Report** (overall avg: {report['overall_avg']}%)"]
    for t in report["topics"]:
        flag = " ⚠️ needs revision" if t["needs_revision"] else ""
        lines.append(f"- {t['topic']}: {t['avg_score']}% avg over {t['quizzes_taken']} quiz(zes){flag}")
    state["response"] = "\n".join(lines)
    return state


def node_chitchat(state: AgentState) -> AgentState:
    state["response"] = call_llm(
        state["user_input"],
        system="You are a friendly study assistant. Keep chitchat brief and steer back to studying.",
    )
    return state


def _extract_topic(text: str) -> str:
    result = call_llm_json(
        f'Extract the study topic from this request as JSON: {{"topic": "..."}}\nRequest: "{text}"',
        temperature=0.0,
    )
    return result.get("topic", text)


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("route", route_intent)
    graph.add_node("question", node_question)
    graph.add_node("quiz", node_quiz)
    graph.add_node("plan", node_plan)
    graph.add_node("progress", node_progress)
    graph.add_node("chitchat", node_chitchat)

    graph.set_entry_point("route")
    graph.add_conditional_edges(
        "route",
        lambda s: s["intent"],
        {
            "question": "question",
            "quiz": "quiz",
            "plan": "plan",
            "progress": "progress",
            "chitchat": "chitchat",
        },
    )
    for node in ("question", "quiz", "plan", "progress", "chitchat"):
        graph.add_edge(node, END)

    return graph.compile()


_compiled_graph = None


def run_agent(student_id: int, user_input: str) -> str:
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()

    memory_manager.remember(student_id, "user", user_input)
    result = _compiled_graph.invoke({"student_id": student_id, "user_input": user_input})
    memory_manager.remember(student_id, "assistant", result["response"])
    return result["response"]
