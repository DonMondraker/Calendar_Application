import sqlite3

DB = "users.db"

def get_conn():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password_hash BLOB,
        role TEXT DEFAULT 'user',
        timezone TEXT DEFAULT 'UTC'
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY,
        title TEXT,
        subject TEXT,
        description TEXT,
        start TEXT,
        end TEXT,
        timezone TEXT,
        created_by TEXT,
        is_private INTEGER,
        recurrence TEXT,
        subject_color TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        event_id INTEGER,
        username TEXT,
        status TEXT,
        PRIMARY KEY (event_id, username)
    )
    """)

    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        import bcrypt
        pw = bcrypt.hashpw(b"Admin", bcrypt.gensalt())
        c.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("Admin", pw, "admin")
        )

    conn.commit()
    conn.close()
