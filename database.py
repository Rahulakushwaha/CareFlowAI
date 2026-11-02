import os, sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "careflow.db"

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            email TEXT DEFAULT '',
            category TEXT NOT NULL,
            message TEXT NOT NULL,
            summary TEXT DEFAULT '',
            priority TEXT DEFAULT 'Medium',
            draft_response TEXT DEFAULT '',
            status TEXT DEFAULT 'Open',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )""")
        conn.commit()

def create_inquiry(patient_name,email,category,message,summary,priority,draft_response,status="Open"):
    now=datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        cur=conn.execute("""INSERT INTO inquiries
        (patient_name,email,category,message,summary,priority,draft_response,status,created_at,updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",(patient_name,email,category,message,summary,priority,draft_response,status,now,now))
        row=conn.execute("SELECT * FROM inquiries WHERE id=?",(cur.lastrowid,)).fetchone()
        conn.commit()
        return dict(row)

def list_inquiries(limit=None):
    query="SELECT * FROM inquiries ORDER BY created_at DESC, id DESC"
    params=()
    if limit:
        query += " LIMIT ?"; params=(int(limit),)
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(query,params).fetchall()]

def get_inquiry(inquiry_id):
    with get_connection() as conn:
        row=conn.execute("SELECT * FROM inquiries WHERE id=?",(int(inquiry_id),)).fetchone()
        return dict(row) if row else None

def update_inquiry(inquiry_id, **fields):
    allowed={"category","summary","priority","draft_response","status","patient_name","email","message"}
    updates={k:v for k,v in fields.items() if k in allowed}
    if not updates: return False
    updates["updated_at"]=datetime.now().isoformat(timespec="seconds")
    clause=", ".join(f"{k}=?" for k in updates)
    values=list(updates.values())+[int(inquiry_id)]
    with get_connection() as conn:
        cur=conn.execute(f"UPDATE inquiries SET {clause} WHERE id=?",values)
        conn.commit()
        return cur.rowcount>0

def metrics():
    data=list_inquiries()
    return {"total":len(data),"open":sum(x["status"]=="Open" for x in data),
            "in_progress":sum(x["status"]=="In Progress" for x in data),
            "resolved":sum(x["status"]=="Resolved" for x in data)}

def seed_demo_data():
    if list_inquiries(): return 0
    from ai_engine import process_inquiry
    samples=[
        ("Priya Sharma","priya@example.test","Appointments","Hello, I would like to book an appointment for next week."),
        ("Rahul Mehta","rahul@example.test","Clinic Hours","Could you please share the clinic's opening hours on Saturday?"),
        ("Aisha Khan","aisha@example.test","Billing","I have a question about the invoice for my recent visit."),
        ("Vikram Iyer","vikram@example.test","General Inquiry","Do you offer telehealth consultations?"),
        ("Neha Patil","neha@example.test","Clinical Question","I have a health concern and would like advice about symptoms."),
        ("Arjun Desai","arjun@example.test","Appointments","Can I reschedule my appointment to Friday?"),
        ("Meera Joshi","meera@example.test","Billing","Can I receive an itemized copy of my bill?"),
        ("Kabir Shah","kabir@example.test","Clinic Hours","Are you open during public holidays?")
    ]
    statuses=["Open","In Progress","Resolved","Open","In Progress","Resolved","Open","Resolved"]
    for idx,(name,email,category,message) in enumerate(samples):
        r=process_inquiry(message,category)
        row=create_inquiry(name,email,category,message,r["summary"],r["priority"],r["draft_response"],statuses[idx])
    return len(samples)
