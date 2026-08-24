import sqlite3
import os
import json
from datetime import datetime
import uuid

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "app.db")

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS meetings (
            id TEXT PRIMARY KEY,
            title TEXT,
            date TEXT,
            participants TEXT,
            source TEXT,
            transcript TEXT,
            created_at TEXT,
            thread_id TEXT,
            processing_status TEXT
        );

        CREATE TABLE IF NOT EXISTS decisions (
            id TEXT PRIMARY KEY,
            meeting_id TEXT,
            title TEXT,
            current_value TEXT,
            previous_value TEXT,
            status TEXT,
            reason TEXT,
            confidence REAL,
            created_at TEXT,
            FOREIGN KEY (meeting_id) REFERENCES meetings (id)
        );

        CREATE TABLE IF NOT EXISTS decision_evidence (
            id TEXT PRIMARY KEY,
            decision_id TEXT,
            meeting_id TEXT,
            excerpt TEXT,
            FOREIGN KEY (decision_id) REFERENCES decisions (id)
        );

        CREATE TABLE IF NOT EXISTS commitments (
            id TEXT PRIMARY KEY,
            decision_id TEXT,
            task TEXT,
            owner TEXT,
            deadline TEXT,
            status TEXT,
            FOREIGN KEY (decision_id) REFERENCES decisions (id)
        );

        CREATE TABLE IF NOT EXISTS clarifications (
            id TEXT PRIMARY KEY,
            meeting_id TEXT,
            question TEXT,
            answer TEXT,
            status TEXT,
            FOREIGN KEY (meeting_id) REFERENCES meetings (id)
        );
    ''')
    conn.commit()
    conn.close()

# Helper Functions
def create_meeting(title: str, date: str, participants: list, source: str, transcript: str, thread_id: str = None, processing_status: str = "queued"):
    conn = get_db()
    c = conn.cursor()
    meeting_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    c.execute(
        "INSERT INTO meetings (id, title, date, participants, source, transcript, created_at, thread_id, processing_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (meeting_id, title, date, json.dumps(participants), source, transcript, created_at, thread_id, processing_status)
    )
    conn.commit()
    conn.close()
    return meeting_id

def create_decision(meeting_id: str, title: str, current_value: str, previous_value: str, status: str, reason: str, confidence: float):
    conn = get_db()
    c = conn.cursor()
    dec_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    c.execute(
        "INSERT INTO decisions (id, meeting_id, title, current_value, previous_value, status, reason, confidence, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (dec_id, meeting_id, title, current_value, previous_value, status, reason, confidence, created_at)
    )
    conn.commit()
    conn.close()
    return dec_id

def create_evidence(decision_id: str, excerpt: str, meeting_id: str = None):
    conn = get_db()
    c = conn.cursor()
    ev_id = str(uuid.uuid4())
    c.execute(
        "INSERT INTO decision_evidence (id, decision_id, meeting_id, excerpt) VALUES (?, ?, ?, ?)",
        (ev_id, decision_id, meeting_id, excerpt)
    )
    conn.commit()
    conn.close()
    return ev_id

def create_commitment(decision_id: str, task: str, owner: str, deadline: str, status: str = "Open"):
    conn = get_db()
    c = conn.cursor()
    com_id = str(uuid.uuid4())
    c.execute(
        "INSERT INTO commitments (id, decision_id, task, owner, deadline, status) VALUES (?, ?, ?, ?, ?, ?)",
        (com_id, decision_id, task, owner, deadline, status)
    )
    conn.commit()
    conn.close()
    return com_id

def update_decision_status(decision_id: str, status: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE decisions SET status = ? WHERE id = ?", (status, decision_id))
    conn.commit()
    conn.close()

def update_meeting_status(meeting_id: str, status: str, thread_id: str = None):
    conn = get_db()
    c = conn.cursor()
    if thread_id is not None:
        c.execute("UPDATE meetings SET processing_status = ?, thread_id = ? WHERE id = ?", (status, thread_id, meeting_id))
    else:
        c.execute("UPDATE meetings SET processing_status = ? WHERE id = ?", (status, meeting_id))
    conn.commit()
    conn.close()

def get_all_meetings():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM meetings ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_dashboard_metrics():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM decisions")
    decisions_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM decisions WHERE status = 'Pending approval'")
    pending_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM commitments WHERE status != 'Completed'")
    active_commitments = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM commitments WHERE status = 'Overdue'")
    overdue_commitments = c.fetchone()[0]
    
    conn.close()
    return {
        "decisions": decisions_count,
        "decisions_requiring_review": pending_count,
        "active_commitments": active_commitments,
        "overdue_commitments": overdue_commitments
    }

def get_recent_decisions():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM decisions ORDER BY created_at DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_needs_attention():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM decisions WHERE status = 'Pending approval' ORDER BY created_at DESC LIMIT 5")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_commitments():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT c.*, d.title as decision_title 
        FROM commitments c 
        LEFT JOIN decisions d ON c.decision_id = d.id 
        ORDER BY d.created_at DESC
    """)
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_decision_timeline():
    # Simple timeline aggregation for UI
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM decisions ORDER BY created_at DESC")
    decisions = c.fetchall()
    
    results = []
    for d in decisions:
        dec = dict(d)
        
        c.execute("SELECT * FROM decision_evidence WHERE decision_id = ?", (dec["id"],))
        evidence = c.fetchall()
        
        timeline = []
        if dec["previous_value"]:
            timeline.append({"date": "Previous", "event": "Decision created", "detail": f"Value was: {dec['previous_value']}"})
        
        for e in evidence:
            timeline.append({"date": "Historical", "event": "Evidence found", "detail": e["excerpt"]})
        
        timeline.append({"date": dec["created_at"][:10], "event": f"New value proposed ({dec['status']})", "detail": dec["reason"]})
        
        dec["timeline"] = timeline
        results.append(dec)
        
    conn.close()
    return results

def get_decision_detail(decision_id: str):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT d.*, m.title as meeting_title, m.date as meeting_date FROM decisions d LEFT JOIN meetings m ON d.meeting_id = m.id WHERE d.id = ?", (decision_id,))
    dec = dict(c.fetchone())
    
    c.execute("SELECT * FROM decision_evidence WHERE decision_id = ?", (decision_id,))
    dec["evidence"] = [dict(r) for r in c.fetchall()]
    
    c.execute("SELECT * FROM commitments WHERE decision_id = ?", (decision_id,))
    dec["commitments"] = [dict(r) for r in c.fetchall()]
    
    conn.close()
    return dec

