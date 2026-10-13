-- StoryTailor schema.
-- Data minimization: no student names, birthdates, emails, or photos are stored.
-- Students are identified only by a random pseudonym; the teacher keeps the
-- pseudonym-to-name roster offline, outside this system.

CREATE TABLE IF NOT EXISTS teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    display_name TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS classrooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    grade INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS students (
    id TEXT PRIMARY KEY,
    classroom_id INTEGER NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
    access_code_hash TEXT NOT NULL UNIQUE,
    grade INTEGER NOT NULL,
    target_level INTEGER NOT NULL,
    interests TEXT NOT NULL DEFAULT '[]',
    avoid_topics TEXT NOT NULL DEFAULT '[]',
    consent_status TEXT NOT NULL DEFAULT 'school_authorized'
        CHECK (consent_status IN ('school_authorized', 'pending', 'withdrawn')),
    created_at TEXT NOT NULL,
    last_active_at TEXT
);

CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    topic TEXT NOT NULL,
    learning_goal TEXT,
    target_level INTEGER NOT NULL,
    measured_level INTEGER NOT NULL,
    text TEXT NOT NULL,
    sources TEXT NOT NULL DEFAULT '[]',
    attempts INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
    student_id TEXT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    author_role TEXT NOT NULL CHECK (author_role IN ('student', 'teacher')),
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    difficulty TEXT CHECK (difficulty IN ('too_easy', 'just_right', 'too_hard')),
    flag TEXT CHECK (flag IN ('inappropriate', 'inaccurate', 'off_topic')),
    comment TEXT,
    created_at TEXT NOT NULL
);

-- Who touched which student record, and why. Retained independently of
-- student content so deletions themselves remain auditable.
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    student_id TEXT,
    detail TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_stories_student ON stories(student_id);
CREATE INDEX IF NOT EXISTS idx_feedback_student ON feedback(student_id);
CREATE INDEX IF NOT EXISTS idx_audit_student ON audit_log(student_id);

-- Books a student has read from the classroom library. Feeds recommendations
-- (already-read books are excluded) and the teacher summary.
CREATE TABLE IF NOT EXISTS reading_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    book_id TEXT NOT NULL,
    minutes INTEGER CHECK (minutes BETWEEN 1 AND 240),
    completed INTEGER NOT NULL DEFAULT 1,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_reading_log_student ON reading_log(student_id);
