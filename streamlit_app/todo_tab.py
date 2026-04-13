import sqlite3
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st
import plotly.express as px

DB_PATH = "habits.db"


def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL DEFAULT 'General',
        name TEXT NOT NULL,
        kind TEXT NOT NULL CHECK(kind IN ('check', 'number')),
        unit TEXT,
        goal_num REAL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        habit_id INTEGER NOT NULL,
        day TEXT NOT NULL,
        value_num REAL,
        value_check INTEGER,
        note TEXT,
        updated_at TEXT NOT NULL,
        UNIQUE(habit_id, day),
        FOREIGN KEY(habit_id) REFERENCES habits(id)
    );
    """)

    conn.commit()

    cur.execute("PRAGMA table_info(habits);")
    cols = [r[1] for r in cur.fetchall()]
    if "category" not in cols:
        cur.execute("ALTER TABLE habits ADD COLUMN category TEXT NOT NULL DEFAULT 'General';")
        conn.commit()

    cur.execute("PRAGMA table_info(habits);")
    cols = [r[1] for r in cur.fetchall()]
    if "goal_num" not in cols:
        cur.execute("ALTER TABLE habits ADD COLUMN goal_num REAL;")
        conn.commit()

    cur.execute("SELECT COUNT(*) FROM habits;")
    n = cur.fetchone()[0]
    if n == 0:
        defaults = [
            ("Faith", "Praying", "check", None, None),
            ("Sport", "steps", "number", "step", None),
            ("Sport", "Running", "number", "km", None),
            ("Sport", "Sport (any)", "check", None, None),
            ("Sport", "legs", "check", None, None),
            ("Sport", "back", "check", None, None),
            ("Sport", "core-abs", "check", None, None),
            ("Food", "Food on-plan", "check", None, None),
            ("Food", "Protein", "number", "g", 90),
            ("Hydration", "Water", "number", "Liters", None),
            ("study", "n8n", "check", None, None),
            ("study", "printemps des sciences", "check", None, None),
            ("study", "prepa exams", "check", None, None),
            ("Supplements", "Vitamin D", "check", None, None),
            ("Supplements", "Collagen", "check", "g", None),
            ("Supplements", "Creatine", "check", "g", None),
            ("Supplements", "Protein (supp)", "check", "g", None),
            ("Supplements", "Zinc", "check", "mg", None),
            ("Supplements", "Magnesium", "check", "mg", None),
            ("Supplements", "Vitamin C", "check", "mg", None),
        ]

        cur.executemany(
            "INSERT INTO habits(category, name, kind, unit, goal_num) VALUES (?,?,?,?,?);",
            defaults
        )
        conn.commit()

    conn.close()


def list_habits():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM habits ORDER BY category, id;", conn)
    conn.close()
    return df


def upsert_entry(habit_id: int, day: str, kind: str, value, note: str):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")

    if kind == "check":
        value_check = 1 if bool(value) else 0
        cur.execute("""
        INSERT INTO entries(habit_id, day, value_check, value_num, note, updated_at)
        VALUES (?, ?, ?, NULL, ?, ?)
        ON CONFLICT(habit_id, day) DO UPDATE SET
            value_check=excluded.value_check,
            note=excluded.note,
            updated_at=excluded.updated_at;
        """, (habit_id, day, value_check, note, now))
    else:
        value_num = None if value in ("", None) else float(value)
        cur.execute("""
        INSERT INTO entries(habit_id, day, value_num, value_check, note, updated_at)
        VALUES (?, ?, ?, NULL, ?, ?)
        ON CONFLICT(habit_id, day) DO UPDATE SET
            value_num=excluded.value_num,
            note=excluded.note,
            updated_at=excluded.updated_at;
        """, (habit_id, day, value_num, note, now))

    conn.commit()
    conn.close()


def get_entries_range(start_day: date, end_day: date):
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT e.day, e.habit_id, h.category, h.name, h.kind, h.unit, h.goal_num,
               e.value_num, e.value_check, e.note
        FROM entries e
        JOIN habits h ON h.id = e.habit_id
        WHERE date(e.day) BETWEEN date(?) AND date(?)
        ORDER BY e.day ASC, h.category ASC, h.id ASC;
    """, conn, params=(start_day.isoformat(), end_day.isoformat()))
    conn.close()
    if not df.empty:
        df["day"] = pd.to_datetime(df["day"]).dt.date
    return df


def get_entry_for_day(day: date):
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT e.day, e.habit_id, h.category, h.name, h.kind, h.unit, h.goal_num,
               e.value_num, e.value_check, e.note
        FROM habits h
        LEFT JOIN entries e
            ON e.habit_id = h.id AND e.day = ?
        ORDER BY h.category ASC, h.id ASC;
    """, conn, params=(day.isoformat(),))
    conn.close()
    if not df.empty and df["day"].notna().any():
        df.loc[df["day"].notna(), "day"] = pd.to_datetime(df.loc[df["day"].notna(), "day"]).dt.date
    return df


def build_status_grid(entries_df, habits_df, start_day, end_day):
    days = pd.date_range(start_day, end_day, freq="D").date

    labels = [f'{r["category"]} • {r["name"]}' for _, r in habits_df.iterrows()]
    grid = pd.DataFrame(0, index=labels, columns=[d.isoformat() for d in days])

    id_to_label = {int(r["id"]): f'{r["category"]} • {r["name"]}' for _, r in habits_df.iterrows()}
    id_to_kind = {int(r["id"]): r["kind"] for _, r in habits_df.iterrows()}
    id_to_goal = {int(r["id"]): r.get("goal_num") for _, r in habits_df.iterrows()}

    for _, e in entries_df.iterrows():
        hid = int(e["habit_id"])
        label = id_to_label.get(hid)
        if not label:
            continue
        d = e["day"].isoformat()
        if d not in grid.columns:
            continue

        if id_to_kind[hid] == "check":
            grid.loc[label, d] = 1 if e["value_check"] == 1 else 0
        else:
            val = e["value_num"]
            if pd.isna(val):
                grid.loc[label, d] = 0
            else:
                goal = id_to_goal.get(hid)
                if goal is not None and not pd.isna(goal):
                    grid.loc[label, d] = 1 if float(val) >= float(goal) else 0
                else:
                    grid.loc[label, d] = 1

    return grid


def render_todo_tab():
    init_db()

    st.subheader("✅ Daily To-Do / Habit Tracker")

    habits = list_habits()

    selected_day = st.date_input("Day", value=date.today(), key="todo_day")
    days_back = st.selectbox("Range", [7, 14, 30, 90, 180], index=2, key="todo_range")

    day_df = get_entry_for_day(selected_day)

    with st.form("checkin"):
        for category, group in habits.groupby("category", sort=True):
            st.markdown(f"### {category}")
            for _, h in group.iterrows():
                hid = int(h["id"])
                name = h["name"]
                kind = h["kind"]
                unit = h["unit"] or ""

                row = day_df[day_df["habit_id"] == hid]
                existing_check = False
                existing_num = None
                if not row.empty:
                    if pd.notna(row["value_check"].iloc[0]):
                        existing_check = bool(row["value_check"].iloc[0])
                    if pd.notna(row["value_num"].iloc[0]):
                        existing_num = row["value_num"].iloc[0]

                c1, c2 = st.columns([2, 2])
                with c1:
                    st.write(name)
                with c2:
                    if kind == "check":
                        val = st.checkbox("Done", value=existing_check, key=f"chk_{hid}")
                    else:
                        txt = st.text_input(
                            f"{unit}",
                            value="" if existing_num is None else str(existing_num),
                            key=f"num_{hid}"
                        )
                        val = None if txt.strip() == "" else float(txt)
                    st.session_state[f"val_{hid}"] = val

        submitted = st.form_submit_button("Save")

    if submitted:
        for _, h in habits.iterrows():
            hid = int(h["id"])
            kind = h["kind"]
            val = st.session_state.get(f"val_{hid}")
            upsert_entry(hid, selected_day.isoformat(), kind, val, "")
        st.rerun()

    end_day = date.today()
    start_day = end_day - timedelta(days=days_back - 1)

    entries = get_entries_range(start_day, end_day)

    st.subheader("Status grid")

    status_grid = build_status_grid(entries, habits, start_day, end_day)

    fig = px.imshow(status_grid, aspect="auto", labels=dict(x="Day", y="Habit", color="Met"))
    fig.update_coloraxes(showscale=False)
    fig.update_layout(height=max(450, 26 * len(status_grid.index)))

    st.plotly_chart(fig, use_container_width=True)