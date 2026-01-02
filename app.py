import streamlit as st
import pytz
from datetime import datetime
from streamlit_calendar import calendar

from functions.database import init_db
from functions.auth import authenticate_user, create_user
from functions.events import get_events, create_event, delete_event, update_event_time
from functions.attendance import set_attendance, get_attendance

# --------------------------------------------------
# CONFIG / INIT
# --------------------------------------------------
st.set_page_config(layout="wide")
init_db()

if "auth" not in st.session_state:
    st.session_state.auth = None

SUBJECT_COLORS = {
    "Birthday Event": "#1f77b4",
    "Social Event": "#2ca02c",
    "Vacation Event": "#9467bd",
    "Urgent": "#d62728",
    "Other": "#7f7f7f",
}

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def sort_events(events, user_tz):
    today = datetime.now(user_tz).date()

    def rank(e):
        start = datetime.fromisoformat(e["start"]).astimezone(user_tz).date()
        if start == today:
            return (0, start)
        elif start > today:
            return (1, start)
        else:
            return (2, start)

    return sorted(events, key=rank)

# --------------------------------------------------
# LOGIN
# --------------------------------------------------
if not st.session_state.auth:
    st.title("🔐 Login - Borgström Calendar")

    mode = st.radio("", ["Login", "Sign Up"], horizontal=True)
    username = st.text_input("Username", width=200)
    password = st.text_input("Password", type="password", width=200)

    if st.button(mode, type="primary"):
        if mode == "Sign Up":
            if create_user(username, password):
                st.success("Account created. You can now log in.")
        else:
            auth = authenticate_user(username, password)
            if auth:
                st.session_state.auth = auth
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.stop()

# --------------------------------------------------
# USER CONTEXT
# --------------------------------------------------
user = st.session_state.auth
is_admin = user["role"] == "admin"
user_tz = pytz.timezone(user["timezone"])

# --------------------------------------------------
# SIDEBAR — CREATE EVENT
# --------------------------------------------------
with st.sidebar:
    st.header("➕ Create Event")

    title = st.text_input("Title")
    subject = st.selectbox("Subject", SUBJECT_COLORS.keys())
    description = st.text_area("Description")
    private = st.checkbox("Private event")

    start = st.datetime_input("Start")
    end = st.datetime_input("End")

    recurring = st.checkbox("Recurring")
    rrule = st.selectbox(
        "Repeat",
        ["FREQ=DAILY", "FREQ=WEEKLY", "FREQ=MONTHLY"]
    ) if recurring else None

    if st.button("Create", type="primary"):
        create_event({
            "title": title,
            "subject": subject,
            "description": description,
            "start": user_tz.localize(start).isoformat(),
            "end": user_tz.localize(end).isoformat(),
            "timezone": user["timezone"],
            "created_by": user["username"],
            "is_private": int(private),
            "recurrence": rrule,
            "subject_color": SUBJECT_COLORS[subject],
        })
        st.rerun()

    st.divider()

    if st.button("🚪 Logout"):
        st.session_state.auth = None
        st.rerun()

# --------------------------------------------------
# LAYOUT
# --------------------------------------------------
left, right = st.columns([1.1, 1])

# --------------------------------------------------
# CALENDAR (LEFT)
# --------------------------------------------------
calendar_events = []

for e in get_events():
    if not is_admin:
        if e["is_private"] and e["created_by"] != user["username"]:
            continue

    start_dt = datetime.fromisoformat(e["start"]).astimezone(user_tz)
    end_dt = datetime.fromisoformat(e["end"]).astimezone(user_tz)

    calendar_events.append({
        "id": e["id"],
        "title": f"{e['title']} ({e['created_by']})",
        "start": start_dt.strftime("%Y-%m-%dT%H:%M"),
        "end": end_dt.strftime("%Y-%m-%dT%H:%M"),
        "rrule": e["recurrence"],
        "backgroundColor": e["subject_color"],
        "borderColor": e["subject_color"],
    })

with left:
    st.subheader("📅 Borgström Calendar")

    cal = calendar(
        events=calendar_events,
        options={
            "editable": True,
            "eventDrop": True,
            "eventResize": True,
            "height": 550,
        },
        key="calendar",
    )

if cal and "eventDrop" in cal:
    ev = cal["eventDrop"]["event"]
    update_event_time(
        ev["id"], ev["start"], ev["end"],
        user["username"], is_admin
    )
    st.rerun()

# --------------------------------------------------
# EVENT LIST / DETAILS (RIGHT)
# --------------------------------------------------
with right:
    st.subheader("📋 Events")

    raw_events = []
    for e in get_events():
        if not is_admin:
            if e["is_private"] and e["created_by"] != user["username"]:
                continue
        raw_events.append(e)

    visible_events = sort_events(raw_events, user_tz)

    if not visible_events:
        st.info("No events available.")
    else:
        for e in visible_events:
            start_dt = datetime.fromisoformat(e["start"]).astimezone(user_tz)
            end_dt = datetime.fromisoformat(e["end"]).astimezone(user_tz)

            badge = f"""
            <span style="
                background-color:{e['subject_color']};
                color:white;
                padding:3px 8px;
                border-radius:8px;
                font-size:12px;">
                {e['subject']}
            </span>
            """

            header = f"{e['title']} — {start_dt.strftime('%Y-%m-%d %H:%M')}"

            with st.expander(header):
                st.markdown(badge, unsafe_allow_html=True)
                st.write(f"**Creator:** {e['created_by']}")
                st.write(f"**Time:** {start_dt} → {end_dt}")
                st.write(e["description"])

                c1, c2 = st.columns(2)
                if c1.button("✅ Will attend", key=f"a{e['id']}"):
                    set_attendance(e["id"], user["username"], "attending")
                if c2.button("❌ Will not attend", key=f"d{e['id']}"):
                    set_attendance(e["id"], user["username"], "not_attending")

                st.markdown("**Attendance:**")
                for u, s in get_attendance(e["id"]):
                    st.write(f"- {u}: {s}")

                if is_admin or e["created_by"] == user["username"]:
                    st.divider()
                    if st.button("🗑 Delete event", key=f"x{e['id']}"):
                        delete_event(e["id"], user["username"], is_admin)
                        st.rerun()

                if is_admin:
                    st.divider()
                    st.markdown("### 🛡 Admin Controls")
                    st.caption("Admin can moderate all events")
