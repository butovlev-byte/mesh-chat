"""SQLite хранилище для сообщений и контактов."""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from threading import Lock

from config import DB_PATH


class Database:
    """Потокобезопасная база данных."""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_db()
            return cls._instance

    def _init_db(self):
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        with self.conn:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT UNIQUE NOT NULL,
                    display_name TEXT,
                    public_key TEXT NOT NULL,
                    last_seen TIMESTAMP,
                    trust_level INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT UNIQUE NOT NULL,
                    sender_id TEXT NOT NULL,
                    recipient_id TEXT,
                    content TEXT NOT NULL,
                    encrypted_payload TEXT,
                    signature TEXT,
                    hops INTEGER DEFAULT 0,
                    ttl INTEGER,
                    delivered BOOLEAN DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS mesh_nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    node_id TEXT UNIQUE NOT NULL,
                    ip_address TEXT,
                    bt_address TEXT,
                    last_seen TIMESTAMP,
                    rssi INTEGER,
                    hops_away INTEGER DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS idx_msg_sender ON messages(sender_id);
                CREATE INDEX IF NOT EXISTS idx_msg_time ON messages(timestamp);
                CREATE INDEX IF NOT EXISTS idx_nodes_seen ON mesh_nodes(last_seen);
            """)

    # === Контакты ===
    def add_contact(self, node_id: str, public_key: str, display_name: str = None):
        with self.conn:
            self.conn.execute(
                """INSERT OR REPLACE INTO contacts 
                   (node_id, display_name, public_key, last_seen)
                   VALUES (?, ?, ?, ?)""",
                (node_id, display_name or node_id[:8], public_key, datetime.now())
            )

    def get_contact(self, node_id: str) -> dict:
        cursor = self.conn.execute(
            "SELECT * FROM contacts WHERE node_id = ?", (node_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_contacts(self) -> list:
        cursor = self.conn.execute(
            "SELECT * FROM contacts ORDER BY last_seen DESC"
        )
        return [dict(row) for row in cursor.fetchall()]

    # === Сообщения ===
    def save_message(self, msg_id: str, sender_id: str, content: str,
                     recipient_id: str = None, encrypted_payload: str = None,
                     signature: str = None, hops: int = 0, ttl: int = 300):
        with self.conn:
            self.conn.execute(
                """INSERT OR IGNORE INTO messages
                   (message_id, sender_id, recipient_id, content,
                    encrypted_payload, signature, hops, ttl)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (msg_id, sender_id, recipient_id, content,
                 encrypted_payload, signature, hops, ttl)
            )

    def get_messages(self, contact_id: str = None, limit: int = 100) -> list:
        if contact_id:
            cursor = self.conn.execute(
                """SELECT * FROM messages 
                   WHERE sender_id = ? OR recipient_id = ?
                   ORDER BY timestamp DESC LIMIT ?""",
                (contact_id, contact_id, limit)
            )
        else:
            cursor = self.conn.execute(
                "SELECT * FROM messages ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
        return [dict(row) for row in cursor.fetchall()]

    def mark_delivered(self, msg_id: str):
        with self.conn:
            self.conn.execute(
                "UPDATE messages SET delivered = 1 WHERE message_id = ?",
                (msg_id,)
            )

    # === Mesh-узлы ===
    def update_node(self, node_id: str, ip_address: str = None,
                    bt_address: str = None, rssi: int = None,
                    hops_away: int = 0):
        with self.conn:
            self.conn.execute(
                """INSERT OR REPLACE INTO mesh_nodes
                   (node_id, ip_address, bt_address, last_seen, rssi, hops_away)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (node_id, ip_address, bt_address, datetime.now(), rssi, hops_away)
            )

    def get_nearby_nodes(self) -> list:
        cursor = self.conn.execute(
            "SELECT * FROM mesh_nodes ORDER BY last_seen DESC LIMIT 50"
        )
        return [dict(row) for row in cursor.fetchall()]

    def cleanup_old_nodes(self, max_age_minutes: int = 30):
        with self.conn:
            self.conn.execute(
                """DELETE FROM mesh_nodes 
                   WHERE last_seen < datetime('now', '-{} minutes')"""
                .format(max_age_minutes)
            )
