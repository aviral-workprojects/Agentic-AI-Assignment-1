"""Writes data/sample_data.md from the synthetic seed in agent/db.py (uses a temp DB; never touches data/students.db).
Run:  python scripts/export_sample_data.py"""
import os, pathlib, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

def render():
    old = os.environ.get("DB_PATH"); d = tempfile.mkdtemp(); os.environ["DB_PATH"] = os.path.join(d, "s.db")
    try:
        from agent import db
        db.reset()
        out = ["# Synthetic sample data (all records are fictional)", "",
               "Seeded into SQLite by `agent/db.py` on first run. No real student information.", ""]
        with db.connect() as c:
            for t, sql in [("students", "SELECT * FROM students ORDER BY id"), ("fees", "SELECT * FROM fees ORDER BY student_id"),
                           ("scholarships", "SELECT * FROM scholarships ORDER BY student_id")]:
                rows = c.execute(sql).fetchall(); cols = rows[0].keys()
                out += [f"## {t}", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
                out += ["| " + " | ".join(str(r[k]) for k in cols) + " |" for r in rows] + [""]
        out += ["`tickets` and `memory` start empty and are filled at runtime."]
        return "\n".join(out) + "\n"
    finally:
        os.environ.pop("DB_PATH", None)
        if old: os.environ["DB_PATH"] = old

if __name__ == "__main__":
    p = pathlib.Path(__file__).parent.parent / "data" / "sample_data.md"
    p.write_text(render(), encoding="utf-8"); print(f"wrote {p}")
