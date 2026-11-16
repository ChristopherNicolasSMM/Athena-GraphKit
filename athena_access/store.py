"""SQLite storage for accounts, memberships and resource grants."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1, epoch INTEGER NOT NULL DEFAULT 0,
    email_verified INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS organizations (id TEXT PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS groups (
    id TEXT PRIMARY KEY, organization TEXT NOT NULL REFERENCES organizations(id), name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS organization_members (
    organization TEXT REFERENCES organizations(id) ON DELETE CASCADE,
    user INTEGER REFERENCES users(id) ON DELETE CASCADE, PRIMARY KEY(organization,user)
);
CREATE TABLE IF NOT EXISTS group_members (
    team TEXT REFERENCES groups(id) ON DELETE CASCADE,
    user INTEGER REFERENCES users(id) ON DELETE CASCADE, PRIMARY KEY(team,user)
);
CREATE TABLE IF NOT EXISTS grants (
    scope TEXT NOT NULL, resource TEXT NOT NULL,
    principal TEXT NOT NULL CHECK(principal IN ('user','group','organization')),
    target TEXT NOT NULL, level INTEGER NOT NULL CHECK(level IN (1,2)),
    PRIMARY KEY(scope,resource,principal,target)
);
CREATE TABLE IF NOT EXISTS password_resets (
    digest TEXT PRIMARY KEY, user INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS account_registrations (
    digest TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, expires INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS attempts (
    bucket TEXT PRIMARY KEY, expires INTEGER NOT NULL, count INTEGER NOT NULL
);
"""

SUBJECTS = """
    SELECT 'user' AS principal, CAST(:uid AS TEXT) AS target
    UNION ALL
    SELECT 'organization', organization FROM organization_members WHERE user=:uid
    UNION ALL
    SELECT 'group', gm.team FROM group_members gm JOIN groups g ON g.id=gm.team
      JOIN organization_members om ON om.organization=g.organization AND om.user=gm.user
      WHERE gm.user=:uid
"""


class AccessStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.connect() as db:
            db.executescript(SCHEMA)
        with self.connect(write=True) as db:
            columns = {column['name'] for column in db.execute('PRAGMA table_info(users)')}
            if 'email_verified' not in columns:
                # Existing accounts were created by the operator or by email activation.
                db.execute('ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 1')

    @contextmanager
    def connect(self, *, write=False):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            if write:
                db.execute('BEGIN IMMEDIATE')
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def level(db, uid, scope, resource):
        return db.execute(
            f"""SELECT COALESCE(MAX(level),0) FROM grants JOIN ({SUBJECTS}) USING(principal,target)
                WHERE scope=:scope AND resource=:resource""",
            {'uid': uid, 'scope': scope, 'resource': resource},
        ).fetchone()[0]
