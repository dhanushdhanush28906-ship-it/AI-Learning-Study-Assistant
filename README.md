# 🎓 AI Learning & Study Assistant

An agentic AI study assistant built on **RAG + Memory + Tools + Agent**:
students upload their own notes/PDFs, then ask questions, generate quizzes,
get a personalized study plan, and track progress — all grounded in their
own material and running fully locally via Ollama.

## Architecture

```
Student → Streamlit UI → LangGraph Agent (intent router)
                              ├── question  → RAG retrieval (ChromaDB) + Qwen
                              ├── quiz      → RAG-grounded MCQ generation → SQLite
                              ├── plan      → progress-aware scheduler → SQLite
                              ├── progress  → SQLite progress report
                              └── chitchat  → direct LLM response

Memory: short-term = recent conversation window (SQLite `conversations`)
        long-term  = quiz history / progress summary injected into prompts
```

Quiz results feed back into `progress`, which the planner reads to weight
weak topics more heavily — this is the closed agentic loop: **quiz → progress → plan**.

## Project layout

```
ai_study_assistant/
├── app.py                 # Streamlit UI (entry point)
├── config.py               # models, paths, chunking/quiz/planner constants
├── database/
│   ├── schema.sql           # students, documents, conversations, quizzes,
│   │                         # quiz_questions, progress, study_plans
│   └── db.py                # sqlite3 access layer
├── rag/
│   ├── ingest.py             # PDF/text -> chunks -> HF embeddings -> ChromaDB
│   └── retriever.py          # similarity search scoped by student/topic
├── memory/
│   └── memory_manager.py     # short-term window + long-term progress summary
├── tools/
│   ├── llm.py                 # shared Ollama/Qwen client (+ JSON-mode helper)
│   ├── quiz_tool.py            # grounded MCQ generation + grading + progress update
│   ├── planner_tool.py         # weak-topic-weighted schedule generator
│   └── progress_tool.py        # progress report reader
└── agent/
    └── graph.py                # LangGraph: intent router + tool nodes
```

## Setup

1. **Install and start Ollama**, then pull the model:
   ```bash
   ollama pull qwen2.5:7b
   ollama serve
   ```
   (Change the model in `config.py` — `OLLAMA_MODEL` — if you want a
   different Qwen size, e.g. `qwen2.5:1.5b` for a lighter local machine.)

2. **Install Python dependencies** (Python 3.10+ recommended):
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```

The SQLite DB and ChromaDB store are created automatically under `data/`
on first run.

## Using it

1. Enter your name in the sidebar → **Start / Resume session**.
2. Upload a PDF or text file of your notes (optionally label it with a topic).
3. In the **Chat & Study** tab, ask questions — answers are grounded in
   your uploaded material via RAG.
4. In the **Take Quiz** tab, generate an MCQ quiz on a topic you've
   uploaded material for, answer it, and submit for instant grading.
5. Check the **Progress** tab for per-topic averages and weak-topic flags;
   generate a revision-focused study plan straight from there.

You can also just type into chat: *"quiz me on photosynthesis"*,
*"make me a 5-day study plan"*, or *"how am I doing?"* — the LangGraph
router classifies intent and dispatches to the right tool automatically.

## Notes / things to harden before production use

- **Auth**: student identity is just a name lookup right now — fine for a
  single-user local tool, not for multi-tenant deployment.
- **Grounding**: quiz generation explicitly instructs the model not to
  invent facts outside retrieved chunks, but for high-stakes use you'd
  want a second grounding-check pass (e.g. verify each option text
  overlaps the source chunks).
- **Concurrency**: SQLite + `ChatOllama` calls are synchronous; fine for
  single-user Streamlit, would need a task queue for multiple concurrent
  students.
- **Embedding model**: `all-MiniLM-L6-v2` is fast and small; swap to a
  larger HF model in `config.py` if retrieval quality needs improvement
  on dense technical material.
