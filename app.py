"""
AI Learning & Study Assistant — Streamlit interface.

Run with:  streamlit run app.py
Requires:  a running Ollama instance with the model in config.OLLAMA_MODEL pulled.
"""
import streamlit as st
from pathlib import Path

from config import OLLAMA_MODEL
from database import db
from rag.ingest import ingest_file, save_upload
from tools.quiz_tool import submit_quiz_answers
from tools.progress_tool import get_progress_report
from agent.graph import run_agent

st.set_page_config(page_title="AI Study Assistant", page_icon="📚", layout="wide")
db.init_db()

# --- Session / student identity --------------------------------------------
if "student_id" not in st.session_state:
    st.session_state.student_id = None
if "chat_log" not in st.session_state:
    st.session_state.chat_log = []
if "active_quiz" not in st.session_state:
    st.session_state.active_quiz = None

with st.sidebar:
    st.title("📚 Study Assistant")
    st.caption(f"Model: {OLLAMA_MODEL} (via Ollama)")

    name = st.text_input("Your name", key="student_name")
    if st.button("Start / Resume session") and name.strip():
        st.session_state.student_id = db.get_or_create_student(name.strip())
        st.session_state.chat_log = []

    if st.session_state.student_id:
        st.divider()
        st.subheader("📄 Upload study material")
        uploaded = st.file_uploader("PDF or text file", type=["pdf", "txt"])
        topic_hint = st.text_input("Topic label (optional)")
        if uploaded and st.button("Ingest document"):
            with st.spinner("Reading and embedding document..."):
                path = save_upload(uploaded.getvalue(), uploaded.name)
                num_chunks = ingest_file(path, st.session_state.student_id, topic=topic_hint or None)
                db.add_document(st.session_state.student_id, uploaded.name, topic_hint, num_chunks)
            st.success(f"Ingested {uploaded.name} — {num_chunks} chunks stored.")

        docs = db.list_documents(st.session_state.student_id)
        if docs:
            st.caption("Uploaded materials:")
            for d in docs:
                st.text(f"• {d['filename']} ({d['num_chunks']} chunks)")

if not st.session_state.student_id:
    st.info("Enter your name in the sidebar and click **Start / Resume session** to begin.")
    st.stop()

tab_chat, tab_quiz, tab_progress = st.tabs(["💬 Chat & Study", "📝 Take Quiz", "📊 Progress"])

# --- Chat tab ----------------------------------------------------------------
with tab_chat:
    st.caption("Ask questions about your material, or ask for a quiz / study plan / progress report.")
    for turn in st.session_state.chat_log:
        with st.chat_message(turn["role"]):
            st.markdown(turn["content"])

    user_msg = st.chat_input("Ask a question, request a quiz, or ask for a study plan...")
    if user_msg:
        st.session_state.chat_log.append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.markdown(user_msg)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = run_agent(st.session_state.student_id, user_msg)
            st.markdown(reply)
        st.session_state.chat_log.append({"role": "assistant", "content": reply})

# --- Quiz tab ------------------------------------------------------------------
with tab_quiz:
    st.subheader("Generate a quiz")
    col1, col2, col3 = st.columns(3)
    with col1:
        quiz_topic = st.text_input("Topic", key="quiz_topic")
    with col2:
        quiz_n = st.number_input("Number of questions", min_value=2, max_value=15, value=5)
    with col3:
        quiz_diff = st.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)

    if st.button("Generate quiz") and quiz_topic.strip():
        from tools.quiz_tool import generate_quiz
        with st.spinner("Generating quiz from your material..."):
            try:
                result = generate_quiz(st.session_state.student_id, quiz_topic.strip(), quiz_n, quiz_diff)
                st.session_state.active_quiz = result
            except ValueError as e:
                st.error(str(e))

    if st.session_state.active_quiz:
        quiz = st.session_state.active_quiz
        st.divider()
        st.subheader(f"Quiz: {quiz_topic}")
        answers = {}
        for i, q in enumerate(quiz["questions"]):
            st.markdown(f"**{i+1}. {q['question']}**")
            choice = st.radio(
                "Choose one:",
                options=list(q["options"].keys()),
                format_func=lambda k, opts=q["options"]: f"{k}) {opts[k]}",
                key=f"q_{quiz['quiz_id']}_{i}",
                label_visibility="collapsed",
            )
            answers[i] = choice

        if st.button("Submit quiz"):
            db_questions = db.get_quiz_questions(quiz["quiz_id"])
            answer_map = {row["question_id"]: answers[i] for i, row in enumerate(db_questions)}
            outcome = submit_quiz_answers(quiz["quiz_id"], st.session_state.student_id, answer_map)
            st.success(f"Score: {outcome['score_pct']}% ({outcome['correct']}/{outcome['total']})")
            for r in outcome["results"]:
                icon = "✅" if r["is_correct"] else "❌"
                st.markdown(f"{icon} **{r['question']}**  \nYour answer: {r['given_answer']} | "
                            f"Correct: {r['correct_answer']}  \n_{r['explanation']}_")
            st.session_state.active_quiz = None

# --- Progress tab --------------------------------------------------------------
with tab_progress:
    st.subheader("Progress overview")
    report = get_progress_report(st.session_state.student_id)
    if not report["topics"]:
        st.info("No quizzes taken yet.")
    else:
        st.metric("Overall average", f"{report['overall_avg']}%")
        for t in report["topics"]:
            label = f"{t['topic']} — {t['avg_score']}% ({t['quizzes_taken']} quizzes)"
            if t["needs_revision"]:
                label += " ⚠️ needs revision"
            st.progress(min(t["avg_score"] / 100, 1.0), text=label)

        if report["weak_topics"]:
            st.warning("Weak topics: " + ", ".join(report["weak_topics"]))
            if st.button("Generate a revision plan for weak topics"):
                reply = run_agent(
                    st.session_state.student_id,
                    f"Create a study plan focused on: {', '.join(report['weak_topics'])}",
                )
                st.markdown(reply)
