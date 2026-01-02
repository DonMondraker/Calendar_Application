from functions.database import get_conn

def get_events():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM events")
    rows = c.fetchall()
    conn.close()

    keys = [
        "id", "title", "subject", "description",
        "start", "end", "timezone",
        "created_by", "is_private",
        "recurrence", "subject_color"
    ]

    return [dict(zip(keys, r)) for r in rows]

def create_event(e):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO events
        (title, subject, description, start, end, timezone,
         created_by, is_private, recurrence, subject_color)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tuple(e.values()))
    conn.commit()
    conn.close()

def delete_event(event_id, username, is_admin):
    conn = get_conn()
    c = conn.cursor()
    if is_admin:
        c.execute("DELETE FROM events WHERE id=?", (event_id,))
    else:
        c.execute(
            "DELETE FROM events WHERE id=? AND created_by=?",
            (event_id, username)
        )
    conn.commit()
    conn.close()

def update_event_time(event_id, start, end, username, is_admin):
    conn = get_conn()
    c = conn.cursor()
    if is_admin:
        c.execute(
            "UPDATE events SET start=?, end=? WHERE id=?",
            (start, end, event_id)
        )
    else:
        c.execute(
            "UPDATE events SET start=?, end=? WHERE id=? AND created_by=?",
            (start, end, event_id, username)
        )
    conn.commit()
    conn.close()
