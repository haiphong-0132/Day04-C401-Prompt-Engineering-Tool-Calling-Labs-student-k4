"""SQLite storage for redacted Research Agent transcripts."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


def initialize_database(path: Path) -> None:
    """Create the local transcript table when it does not exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                transcript_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT,
                version TEXT NOT NULL,
                artifact_version TEXT NOT NULL,
                turn_count INTEGER NOT NULL,
                transcript_json TEXT NOT NULL
            )
            """
        )


def save_conversation(path: Path, transcript: dict[str, Any]) -> None:
    """Insert or update one complete, already-redacted transcript."""
    initialize_database(path)
    payload = json.dumps(transcript, ensure_ascii=False, default=str)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            INSERT INTO conversations (
                transcript_id, created_at, updated_at, provider, model, version,
                artifact_version, turn_count, transcript_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(transcript_id) DO UPDATE SET
                updated_at = excluded.updated_at,
                provider = excluded.provider,
                model = excluded.model,
                version = excluded.version,
                artifact_version = excluded.artifact_version,
                turn_count = excluded.turn_count,
                transcript_json = excluded.transcript_json
            """,
            (
                transcript["transcript_id"],
                transcript["created_at"],
                transcript["updated_at"],
                transcript["provider"],
                transcript.get("model"),
                transcript["version"],
                transcript["artifact_version"],
                len(transcript.get("turns", [])),
                payload,
            ),
        )


def list_conversations(path: Path, limit: int = 10) -> list[dict[str, Any]]:
    """Return recent history without returning the full transcript JSON."""
    initialize_database(path)
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT transcript_id, created_at, updated_at, provider, model, version,
                   artifact_version, turn_count
            FROM conversations
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def load_conversation(path: Path, transcript_id: str) -> dict[str, Any] | None:
    """Load a complete transcript for a user-selected download."""
    initialize_database(path)
    with sqlite3.connect(path) as connection:
        row = connection.execute(
            "SELECT transcript_json FROM conversations WHERE transcript_id = ?",
            (transcript_id,),
        ).fetchone()
    return json.loads(row[0]) if row else None
