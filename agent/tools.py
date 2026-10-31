import os, time
from . import db, memory, retrieval

SCHEMAS = [
    {"name": "get_student_record", "description": "Get the signed-in student's profile (name, programme, batch, email).",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "get_fee_status", "description": "Get the signed-in student's fee status: total, paid, balance, due date.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "get_scholarship_status", "description": "Get the signed-in student's scholarship records and status.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "create_support_ticket", "description": "Create a support ticket. Needs a clear subject and details.",
     "input_schema": {"type": "object", "properties": {"subject": {"type": "string"}, "details": {"type": "string"}}, "required": ["subject", "details"]}},
    {"name": "search_policy", "description": "Search the student handbook for policy/rules. Returns the relevant chunks only.",
     "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "save_memory", "description": "Persist a stable fact about the student. Keys: programme, batch, preferred_contact, language. Never sensitive or temporary info.",
     "input_schema": {"type": "object", "properties": {"key": {"type": "string"}, "value": {"type": "string"}}, "required": ["key", "value"]}},
]

def _one(sql, sid):
    with db.connect() as c:
        return c.execute(sql, (sid,)).fetchone()

def get_student_record(sid):
    r = _one("SELECT * FROM students WHERE id=?", sid)
    return dict(r) if r else {"error": "student not found"}

def get_fee_status(sid):
    r = _one("SELECT * FROM fees WHERE student_id=?", sid)
    if not r: return {"error": "no fee record"}
    d = dict(r); d["balance"] = d["total"] - d["paid"]
    return d

def get_scholarship_status(sid):
    with db.connect() as c:
        rows = c.execute("SELECT name, status, amount FROM scholarships WHERE student_id=?", (sid,)).fetchall()
    return {"scholarships": [dict(r) for r in rows]} if rows else {"scholarships": [], "note": "no scholarship record"}

def create_support_ticket(sid, subject, details):
    with db.connect() as c:
        cur = c.execute("INSERT INTO tickets(student_id,subject,body,ts) VALUES(?,?,?,?)", (sid, subject, details, time.time()))
    return {"ticket_id": cur.lastrowid, "status": "open"}

def search_policy(sid, query):
    ch = retrieval.search(query)
    return {"chunks": [{"id": c["id"], "text": c["text"]} for c in ch]} if ch else {"chunks": [], "note": "no relevant policy found: the handbook does not cover this. Tell the student you do not have this information and offer a support ticket; do not state a policy."}

def save_memory(sid, key, value):
    return memory.save(sid, key, value)

FUNCS = {f.__name__: f for f in (get_student_record, get_fee_status, get_scholarship_status, create_support_ticket, search_policy, save_memory)}

MAX_LEN = 500
_BY_NAME = {t["name"]: t["input_schema"] for t in SCHEMAS}

def validate(name, args):
    """Return None if ok, else a safe error string. Model can never pass student_id (not in any schema)."""
    if name not in _BY_NAME: return "unknown tool"
    if not isinstance(args, dict): return "arguments must be an object"
    props, req = _BY_NAME[name].get("properties", {}), _BY_NAME[name].get("required", [])
    if set(args) - set(props): return "unexpected arguments"
    if [k for k in req if k not in args]: return "missing required arguments"
    for v in args.values():
        if not isinstance(v, str) or not v.strip() or len(v) > MAX_LEN: return "invalid argument value"
    return None

def run(name, args, sid):
    if os.getenv("FAIL_TOOL") == name:          # eval hook: simulate outage
        return {"error": "service temporarily unavailable"}
    bad = validate(name, args)
    if bad:
        return {"error": f"invalid tool call: {bad}"}
    try:
        return FUNCS[name](sid, **args)
    except Exception:                            # never leak DB/stack details to the model or student
        return {"error": "tool failed; please try again or raise a support ticket"}
