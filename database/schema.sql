-- AI Learning & Study Assistant — SQLite schema

CREATE TABLE IF NOT EXISTS students (
    student_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS documents (
    document_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      INTEGER NOT NULL,
    filename        TEXT NOT NULL,
    topic           TEXT,
    num_chunks      INTEGER DEFAULT 0,
    uploaded_at     TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

CREATE TABLE IF NOT EXISTS conversations (
    conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      INTEGER NOT NULL,
    role            TEXT NOT NULL CHECK(role IN ('user','assistant')),
    content         TEXT NOT NULL,
    created_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

CREATE TABLE IF NOT EXISTS quizzes (
    quiz_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      INTEGER NOT NULL,
    topic           TEXT,
    difficulty      TEXT,
    num_questions   INTEGER,
    created_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

CREATE TABLE IF NOT EXISTS quiz_questions (
    question_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id         INTEGER NOT NULL,
    question_text   TEXT NOT NULL,
    option_a        TEXT NOT NULL,
    option_b        TEXT NOT NULL,
    option_c        TEXT NOT NULL,
    option_d        TEXT NOT NULL,
    correct_option  TEXT NOT NULL CHECK(correct_option IN ('A','B','C','D')),
    explanation     TEXT,
    student_answer  TEXT,
    is_correct      INTEGER,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id)
);

CREATE TABLE IF NOT EXISTS progress (
    progress_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      INTEGER NOT NULL,
    topic           TEXT NOT NULL,
    quizzes_taken   INTEGER DEFAULT 0,
    avg_score       REAL DEFAULT 0.0,
    last_score      REAL,
    needs_revision  INTEGER DEFAULT 0,
    updated_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    UNIQUE(student_id, topic)
);

CREATE TABLE IF NOT EXISTS study_plans (
    plan_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      INTEGER NOT NULL,
    plan_json       TEXT NOT NULL,   -- serialized schedule (topics, sessions, dates)
    created_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);
