import bcrypt
from functions.database import get_conn

def create_user(username, password):
    conn = get_conn()
    c = conn.cursor()
    try:
        pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        c.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, pw)
        )
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT password_hash, role, timezone FROM users WHERE username=?",
        (username,)
    )
    row = c.fetchone()
    conn.close()

    if row and bcrypt.checkpw(password.encode(), row[0]):
        return {
            "username": username,
            "role": row[1],
            "timezone": row[2],
        }
    return None
