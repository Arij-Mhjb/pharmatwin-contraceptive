"""SQLite persistence for user-owned simulated patients and immutable reports."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import sqlite3
from uuid import uuid4
from backend.config import get_settings

def now(): return datetime.now(timezone.utc).isoformat()

@contextmanager
def database():
    path = get_settings().patient_store_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path, timeout=15) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("CREATE TABLE IF NOT EXISTS patients (id TEXT PRIMARY KEY, body TEXT NOT NULL, updated TEXT NOT NULL)")
        connection.execute("CREATE TABLE IF NOT EXISTS reports (id TEXT PRIMARY KEY, patient_id TEXT NOT NULL, created TEXT NOT NULL, body TEXT NOT NULL)")
        connection.execute("CREATE TABLE IF NOT EXISTS patient_owners (patient_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, created TEXT NOT NULL)")
        yield connection

def save_patient(patient_id, data):
    with database() as db:
        db.execute("INSERT INTO patients VALUES (?, ?, ?) ON CONFLICT(id) DO UPDATE SET body=excluded.body,updated=excluded.updated", (patient_id, json.dumps(data, ensure_ascii=False), now()))

def patient(patient_id):
    with database() as db:
        row = db.execute("SELECT body FROM patients WHERE id=?", (patient_id,)).fetchone()
    if not row: raise KeyError(patient_id)
    return json.loads(row[0])

def claim_patient(user_id, patient_id):
    with database() as db:
        db.execute("INSERT INTO patient_owners VALUES (?, ?, ?)", (patient_id, user_id, now()))

def owns_patient(user_id, patient_id):
    with database() as db:
        row = db.execute("SELECT 1 FROM patient_owners WHERE patient_id=? AND user_id=?", (patient_id, user_id)).fetchone()
    return bool(row)

def patients(user_id=None, include_unowned=False):
    with database() as db:
        if include_unowned:
            rows = db.execute("SELECT id, body, updated FROM patients ORDER BY updated DESC").fetchall()
        else:
            rows = db.execute("SELECT p.id, p.body, p.updated FROM patients p JOIN patient_owners o ON o.patient_id=p.id WHERE o.user_id=? ORDER BY p.updated DESC", (user_id,)).fetchall()
    return [{"id": row[0], "display_name": json.loads(row[1])["display_name"], "updated_at": row[2]} for row in rows]

def save_report(patient_id, body):
    result = {**body, "id": uuid4().hex, "patient_id": patient_id, "created_at": now()}
    with database() as db:
        db.execute("INSERT INTO reports VALUES (?, ?, ?, ?)", (result["id"], patient_id, result["created_at"], json.dumps(result, ensure_ascii=False)))
    return result

def reports(patient_id):
    with database() as db:
        rows = db.execute("SELECT body FROM reports WHERE patient_id=? ORDER BY created DESC", (patient_id,)).fetchall()
    return [json.loads(row[0]) for row in rows]
