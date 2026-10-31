# Synthetic sample data (all records are fictional)

Seeded into SQLite by `agent/db.py` on first run. No real student information.

## students

| id | name | programme | batch | email |
|---|---|---|---|---|
| S101 | Aarav Mehta | PGDM Big Data Analytics | 2025-27 | aarav@example.edu |
| S102 | Diya Rao | PGDM AI & Data Science | 2025-27 | diya@example.edu |
| S103 | Kabir Singh | PGDM Big Data Analytics | 2025-27 | kabir@example.edu |

## fees

| student_id | total | paid | due_date | status |
|---|---|---|---|---|
| S101 | 120000 | 75000 | 2026-11-05 | Partially paid |
| S102 | 120000 | 120000 | 2026-11-05 | Paid |
| S103 | 120000 | 0 | 2026-10-30 | Pending |

## scholarships

| student_id | name | status | amount |
|---|---|---|---|
| S102 | Merit Scholarship | Approved | 30000 |
| S103 | Need-based Scholarship | Under review | 20000 |

`tickets` and `memory` start empty and are filled at runtime.
