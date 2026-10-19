"""Shared encoding and additive migration for task metadata in SQLite."""
import json

from gtasks.models.task import Task


def ensure_details_column(db, table: str) -> None:
    if "details" not in {row[1] for row in db.execute(f"PRAGMA table_info({table})")}:
        db.execute(f"ALTER TABLE {table} ADD COLUMN details TEXT NOT NULL DEFAULT '{{}}'")


def encode_details(task: Task) -> str:
    return json.dumps({"notes": task.notes, "due": task.due,
                       "parent": task.parent, "assigned": task.assigned})


def decode_details(value: str) -> dict:
    return json.loads(value)
