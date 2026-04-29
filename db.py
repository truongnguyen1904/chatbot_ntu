"""
SQLite: lưu phiên chat + intent để báo cáo đồ án / thống kê.
Đường dẫn DB: biến môi trường CHATBOT_DB hoặc data/chatbot.db
"""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / "data" / "chatbot.db"


def db_path() -> Path:
    p = os.environ.get("CHATBOT_DB")
    return Path(p) if p else DEFAULT_DB


def get_conn() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    conn.executescript(
        """
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

        CREATE INDEX IF NOT EXISTS idx_chat_messages_sender
            ON chat_messages(sender_id);
        CREATE INDEX IF NOT EXISTS idx_chat_messages_created
            ON chat_messages(created_at);
        CREATE INDEX IF NOT EXISTS idx_chat_messages_intent
            ON chat_messages(primary_intent);
        """
    )
    conn.commit()
    conn.close()


def upsert_session(sender_id: str) -> None:
    conn = get_conn()
    row = conn.execute(
        "SELECT id FROM chat_sessions WHERE sender_id = ?",
        (sender_id,),
    ).fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO chat_sessions (sender_id) VALUES (?)",
            (sender_id,),
        )
    else:
        conn.execute(
            "UPDATE chat_sessions SET last_seen = datetime('now') WHERE sender_id = ?",
            (sender_id,),
        )
    conn.commit()
    conn.close()


def log_message(
    sender_id: str,
    user_text: str,
    primary_intent: Optional[str],
    confidence: Optional[float],
    bot_text: str,
    is_multi: bool,
    sub_intents: Optional[List[Dict[str, Any]]] = None,
    debug: Optional[Dict[str, Any]] = None,
) -> None:
    try:
        upsert_session(sender_id)
        conn = get_conn()
        conn.execute(
            """
            INSERT INTO chat_messages (
                sender_id, user_text, primary_intent, confidence, bot_text,
                is_multi_question, sub_intents_json, debug_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sender_id,
                user_text,
                primary_intent,
                confidence,
                bot_text,
                1 if is_multi else 0,
                json.dumps(sub_intents or [], ensure_ascii=False),
                json.dumps(debug or {}, ensure_ascii=False, default=str),
            ),
        )
        conn.commit()
        conn.close()
    except sqlite3.Error:
        pass


_init_done = False


def ensure_db() -> None:
    global _init_done
    if not _init_done:
        init_db()
        _init_done = True
