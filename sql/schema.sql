-- Hệ thống chatbot E-learning NTU — schema SQLite (đồ án / báo cáo)
-- Chạy: sqlite3 data/chatbot.db < sql/schema.sql   (hoặc tự tạo qua db.init_db())

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id TEXT NOT NULL UNIQUE,
    first_seen TEXT DEFAULT (datetime('now')),
    last_seen TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id TEXT NOT NULL,
    user_text TEXT NOT NULL,
    primary_intent TEXT,
    confidence REAL,
    bot_text TEXT,
    is_multi_question INTEGER NOT NULL DEFAULT 0,
    sub_intents_json TEXT,
    debug_json TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_sender ON chat_messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created ON chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_intent ON chat_messages(primary_intent);
