from __future__ import annotations

from pathlib import Path
import sqlite3


def connect_sqlite(path: str | Path = "backend/xengineer.db") -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection

