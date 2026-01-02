from functions.database import get_conn

def set_attendance(event_id, username, status):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO attendance (event_id, username, status)
        VALUES (?, ?, ?)
        ON CONFLICT(event_id, username)
        DO UPDATE SET status=excluded.status
    """, (event_id, username, status))
    conn.commit()
    conn.close()

def get_attendance(event_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT username, status FROM attendance WHERE event_id=?",
        (event_id,)
    )
    rows = c.fetchall()
    conn.close()
    return rows
