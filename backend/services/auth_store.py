"""Database-backed authentication with opaque, hashed session tokens."""
from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import json
import secrets
from uuid import uuid4

from backend.services.patient_store import database, now

def initialize():
    with database() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('user','admin')),
            status TEXT NOT NULL CHECK(status IN ('active','disabled')),
            onboarding_complete INTEGER NOT NULL DEFAULT 0, created TEXT NOT NULL,
            updated TEXT NOT NULL, last_login TEXT)""")
        columns = {row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()}
        if "avatar_url" not in columns:
            db.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
        db.execute("""CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, token_hash TEXT NOT NULL UNIQUE,
            csrf_hash TEXT NOT NULL, created TEXT NOT NULL, last_seen TEXT NOT NULL,
            expires TEXT NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)""")
        db.execute("""CREATE TABLE IF NOT EXISTS audit_log (
            id TEXT PRIMARY KEY, actor_user_id TEXT, action TEXT NOT NULL,
            target_type TEXT NOT NULL, target_id TEXT, created TEXT NOT NULL, metadata TEXT NOT NULL)""")

def _hash(value: str): return hashlib.sha256(value.encode()).hexdigest()

def hash_password(password: str):
    if len(password) < 10 or not any(c.islower() for c in password) or not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
        raise ValueError("Le mot de passe doit contenir au moins 10 caractères, une majuscule, une minuscule et un chiffre")
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return "scrypt$16384$8$1$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(digest).decode()

def verify_password(password: str, encoded: str):
    try:
        _, n, r, p, salt, expected = encoded.split("$")
        digest = hashlib.scrypt(password.encode(), salt=base64.urlsafe_b64decode(salt), n=int(n), r=int(r), p=int(p), dklen=32)
        return hmac.compare_digest(digest, base64.urlsafe_b64decode(expected))
    except (ValueError, TypeError):
        return False

def public_user(row):
    return {"id": row[0], "email": row[1], "display_name": row[3], "role": row[4], "status": row[5], "onboarding_complete": bool(row[6]), "created_at": row[7], "last_login_at": row[9], "avatar_url": row[10]}

def create_user(email, password, display_name, role="user", onboarding=False):
    initialize(); stamp = now(); user_id = uuid4().hex
    try:
        with database() as db:
            db.execute("INSERT INTO users (id,email,password_hash,display_name,role,status,onboarding_complete,created,updated,last_login,avatar_url) VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?, NULL, NULL)", (user_id, email.strip().lower(), hash_password(password), display_name.strip(), role, int(onboarding), stamp, stamp))
            audit(db, user_id, "user.created", "user", user_id, {"role": role})
    except Exception as exc:
        if "UNIQUE constraint" in str(exc): raise ValueError("Un compte existe déjà pour cette adresse") from exc
        raise
    return get_user(user_id)

def get_user(user_id):
    initialize()
    with database() as db: row = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    return public_user(row) if row else None

def authenticate(email, password):
    initialize()
    with database() as db: row = db.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
    if not row or not verify_password(password, row[2]) or row[5] != "active": return None
    with database() as db: db.execute("UPDATE users SET last_login=?, updated=? WHERE id=?", (now(), now(), row[0]))
    return get_user(row[0])

def create_session(user_id, days=7):
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(24)
    created = datetime.now(timezone.utc); expires = created + timedelta(days=days)
    with database() as db:
        db.execute("DELETE FROM sessions WHERE expires < ?", (created.isoformat(),))
        db.execute("INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?)", (uuid4().hex, user_id, _hash(token), _hash(csrf), created.isoformat(), created.isoformat(), expires.isoformat()))
        audit(db, user_id, "session.created", "user", user_id, {})
    return token, csrf, expires

def session_user(token):
    if not token: return None
    initialize(); stamp = now()
    with database() as db:
        row = db.execute("SELECT u.*, s.csrf_hash, s.id FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires>? AND u.status='active'", (_hash(token), stamp)).fetchone()
        if row: db.execute("UPDATE sessions SET last_seen=? WHERE id=?", (stamp, row[12]))
    if not row: return None
    return public_user(row), row[11]

def revoke_session(token):
    if token:
        with database() as db: db.execute("DELETE FROM sessions WHERE token_hash=?", (_hash(token),))

def csrf_valid(expected_hash, header, cookie):
    return bool(header and cookie and hmac.compare_digest(header, cookie) and hmac.compare_digest(expected_hash, _hash(header)))

def complete_onboarding(user_id, display_name):
    with database() as db:
        db.execute("UPDATE users SET display_name=?, onboarding_complete=1, updated=? WHERE id=?", (display_name.strip(), now(), user_id))
        audit(db, user_id, "onboarding.completed", "user", user_id, {})
    return get_user(user_id)

def change_password(user_id, current, new):
    with database() as db: row = db.execute("SELECT password_hash FROM users WHERE id=?", (user_id,)).fetchone()
    if not row or not verify_password(current, row[0]): raise ValueError("Mot de passe actuel incorrect")
    with database() as db:
        db.execute("UPDATE users SET password_hash=?, updated=? WHERE id=?", (hash_password(new), now(), user_id))
        db.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
        audit(db, user_id, "password.changed", "user", user_id, {})

def update_avatar(user_id, data_url):
    with database() as db:
        db.execute("UPDATE users SET avatar_url=?, updated=? WHERE id=?", (data_url, now(), user_id))
        audit(db, user_id, "avatar.updated", "user", user_id, {"removed": data_url is None})
    return get_user(user_id)

def list_users():
    with database() as db: rows = db.execute("SELECT * FROM users ORDER BY created DESC").fetchall()
    return [public_user(row) for row in rows]

def update_user(actor_id, user_id, role=None, status=None):
    current = get_user(user_id)
    if not current: raise KeyError(user_id)
    if actor_id == user_id and (role == "user" or status == "disabled"): raise ValueError("Vous ne pouvez pas désactiver ou rétrograder votre propre compte")
    with database() as db:
        if role: db.execute("UPDATE users SET role=?, updated=? WHERE id=?", (role, now(), user_id))
        if status: db.execute("UPDATE users SET status=?, updated=? WHERE id=?", (status, now(), user_id))
        audit(db, actor_id, "user.updated", "user", user_id, {"role": role, "status": status})
    return get_user(user_id)

def bootstrap_admin(email, password, display_name):
    initialize()
    with database() as db: row = db.execute("SELECT id FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
    if row: return get_user(row[0])
    return create_user(email, password, display_name, role="admin", onboarding=True)

def admin_overview():
    initialize()
    with database() as db:
        counts = {
            "users": db.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            "active_users": db.execute("SELECT COUNT(*) FROM users WHERE status='active'").fetchone()[0],
            "admins": db.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0],
            "sessions": db.execute("SELECT COUNT(*) FROM sessions WHERE expires>?", (now(),)).fetchone()[0],
            "patients": db.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
            "reports": db.execute("SELECT COUNT(*) FROM reports").fetchone()[0],
        }
        audits = db.execute("""SELECT a.action,a.target_type,a.target_id,a.created,u.display_name
            FROM audit_log a LEFT JOIN users u ON u.id=a.actor_user_id
            ORDER BY a.created DESC LIMIT 12""").fetchall()
        recent_patients = db.execute("""SELECT p.id,json_extract(p.body,'$.display_name'),p.updated,u.display_name,u.email
            FROM patients p LEFT JOIN patient_owners o ON o.patient_id=p.id LEFT JOIN users u ON u.id=o.user_id
            ORDER BY p.updated DESC LIMIT 8""").fetchall()
    return {"counts": counts,
        "audit": [{"action": r[0], "target_type": r[1], "target_id": r[2], "created_at": r[3], "actor": r[4] or "Système"} for r in audits],
        "recent_patients": [{"id": r[0], "display_name": r[1], "updated_at": r[2], "owner_name": r[3] or "Non attribué", "owner_email": r[4]} for r in recent_patients]}

def audit(db, actor, action, target_type, target_id, metadata):
    db.execute("INSERT INTO audit_log VALUES (?, ?, ?, ?, ?, ?, ?)", (uuid4().hex, actor, action, target_type, target_id, now(), json.dumps(metadata)))
