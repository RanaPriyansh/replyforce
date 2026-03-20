"""
ReplyForce v0.1 — SQLite Models
Simple ORM-free approach using sqlite3 directly.
"""

import sqlite3
from datetime import datetime
from typing import Optional
import os

DB_PATH = os.getenv("REPLYFORCE_DB", "replyforce.db")


def get_db() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location_id TEXT NOT NULL UNIQUE,
            address TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            location_id TEXT NOT NULL,
            reviewer_name TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            review_text TEXT NOT NULL,
            response_text TEXT,
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'sent', 'rejected')),
            google_review_id TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            responded_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_reviews_status ON reviews(status);
        CREATE INDEX IF NOT EXISTS idx_reviews_location ON reviews(location_id);
    """)
    conn.commit()
    conn.close()


def insert_business(name: str, location_id: str, address: str = "") -> int:
    """Insert a business, return its id."""
    conn = get_db()
    cur = conn.execute(
        "INSERT OR IGNORE INTO businesses (name, location_id, address) VALUES (?, ?, ?)",
        (name, location_id, address)
    )
    conn.commit()
    biz_id = cur.lastrowid
    conn.close()
    return biz_id


def insert_review(business_name: str, location_id: str, reviewer_name: str,
                  rating: int, review_text: str, google_review_id: str = None) -> int:
    """Insert a review, return its id."""
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO reviews (business_name, location_id, reviewer_name,
           rating, review_text, google_review_id)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (business_name, location_id, reviewer_name, rating, review_text, google_review_id)
    )
    conn.commit()
    review_id = cur.lastrowid
    conn.close()
    return review_id


def update_response(review_id: int, response_text: str):
    """Update the drafted response for a review."""
    conn = get_db()
    conn.execute(
        "UPDATE reviews SET response_text = ? WHERE id = ?",
        (response_text, review_id)
    )
    conn.commit()
    conn.close()


def update_status(review_id: int, status: str):
    """Update review status (approved/rejected/sent)."""
    conn = get_db()
    ts = datetime.utcnow().isoformat() if status in ("approved", "sent") else None
    conn.execute(
        "UPDATE reviews SET status = ?, responded_at = COALESCE(?, responded_at) WHERE id = ?",
        (status, ts, review_id)
    )
    conn.commit()
    conn.close()


def get_pending_reviews() -> list[dict]:
    """Get all pending reviews."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM reviews WHERE status = 'pending' ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_reviews(limit: int = 100) -> list[dict]:
    """Get all reviews, newest first."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM reviews ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_review_stats() -> dict:
    """Get aggregate stats."""
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM reviews WHERE status='pending'").fetchone()[0]
    approved = conn.execute("SELECT COUNT(*) FROM reviews WHERE status='approved'").fetchone()[0]
    sent = conn.execute("SELECT COUNT(*) FROM reviews WHERE status='sent'").fetchone()[0]
    avg_rating = conn.execute("SELECT AVG(rating) FROM reviews").fetchone()[0]
    conn.close()
    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "sent": sent,
        "avg_rating": round(avg_rating, 1) if avg_rating else 0
    }
