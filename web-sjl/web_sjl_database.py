"""SQLite 数据库操作"""
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "storage" / "app.db"


def get_db():
    """获取数据库连接"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            audio_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            voice_id TEXT DEFAULT 'zh-female',
            rate INTEGER DEFAULT 100
        )
    """)
    conn.commit()
    conn.close()


def add_history(type, title, content=None, audio_path=None):
    """添加历史记录"""
    conn = get_db()
    conn.execute(
        "INSERT INTO history (type, title, content, audio_path) VALUES (?, ?, ?, ?)",
        (type, title, content, audio_path)
    )
    conn.commit()
    conn.close()


def get_history(limit=100):
    """获取历史记录"""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM history ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_history(history_id):
    """删除历史记录"""
    conn = get_db()
    conn.execute("DELETE FROM history WHERE id = ?", (history_id,))
    conn.commit()
    conn.close()


def clear_history():
    """清空历史记录"""
    conn = get_db()
    conn.execute("DELETE FROM history")
    conn.commit()
    conn.close()


def get_settings():
    """获取设置"""
    conn = get_db()
    row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"voice_id": "zh-female", "rate": 100}


def update_settings(voice_id=None, rate=None):
    """更新设置"""
    conn = get_db()
    current = get_settings()
    new_voice = voice_id if voice_id else current["voice_id"]
    new_rate = rate if rate else current["rate"]
    conn.execute(
        "INSERT OR REPLACE INTO settings (id, voice_id, rate) VALUES (1, ?, ?)",
        (new_voice, new_rate)
    )
    conn.commit()
    conn.close()


init_db()
