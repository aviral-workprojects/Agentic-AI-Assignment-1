# Student Support Agent – Assignment 1

A chat agent for a PGDM institute that answers student queries (fees, scholarships, course changes, support requests). One agent decides per question whether to answer directly, call a tool, retrieve handbook policy, or use remembered information. All student records are **synthetic** (see `data/sample_data.md`); no real student data or credentials are in this repo.

## Architecture
```
app.py (Streamlit chat)  ──►  agent/loop.py
   redact input → context.build → provider.generate ⇄ tools (max 5 iterations) → trace
        agent/context.py     system prompt + relevant memories + last 4 turns + question
        agent/tools.py       6 tools, schema-validated; the model can never supply a student id
        agent/retrieval.py   handbook chunks → BM25 top-k
        agent/memory.py      SQLite persistent memory, whitelist + secret filter
        agent/redact.py      OTP/password/API-key/card/email/phone redaction
        agent/trace.py       one JSON line per turn
        agent/providers/     groq (default), gemini, anthropic adapters → common LLMResponse / LLMError
        agent/db.py          SQLite (always-closed connections; synthetic seed)
data/handbook.md  data/sample_data.md      eval/  tests/  scripts/
```
**Agent loop:** the model gets the question, context and tool schemas. If it returns tool calls, each is validated and executed for the signed-in student, results go back to the model, and this repeats (max 5) until it produces a final answer. Provider failures return a generic message and leave chat history unchanged.

## Tools
| tool | purpose |
|---|---|
| `get_student_record` | profile (name, programme, batch, email) |
| `get_fee_status` | total, paid, balance, due date, status |
| `get_scholarship_status` | scholarship records and status |
| `create_support_ticket` | creates a ticket (subject + details required; missing details → the agent asks first) |
| `search_policy` | handbook retrieval (returns only relevant chunks, or "no relevant policy found") |
| `save_memory` | persists a stable fact (programme, batch, preferred_contact, language) |

Unknown tools, extra/missing/non-string arguments, or malformed model JSON are rejected before execution; tool errors return a safe message the model must relay without inventing data.

## Retrieval
`data/handbook.md` is split by `##` heading into chunks with stable ids (e.g. `payment-portal-failure`), indexed with BM25 (stop-words + light stemming). `search_policy` returns at most 2 chunks scoring ≥ 0.7 and ≥ 0.5× the best score; otherwise nothing, plus a note telling the model the handbook does not cover it. The system prompt requires answers only from returned chunks (cited by id) and an explicit "not enough information" + ticket offer otherwise. `python eval\calibrate_retrieval.py` shows scores for labelled relevant/irrelevant queries (11/11 relevant top-1; one known false positive, "placement statistics for last year").

## Selective memory
Stored in SQLite per student, persisting across sessions ("New session" clears chat only). The model may call `save_memory`, but code accepts only 4 whitelisted keys, values ≤ 80 chars, and rejects secrets (OTP, password, PIN, CVV, card numbers, API keys, tokens). Secrets are also redacted *before* reaching the model, history and traces. Temporary or one-off statements are not stored.

## Context selection
Each call contains: system prompt, only memories relevant to the question (programme always), last 4 turns, the question, and – only if the model asks – the top handbook chunks. The handbook is never sent whole.

## Trace and evaluation
Trace (`traces/trace.jsonl`, git-ignored): student, redacted question/answer, tools (name, redacted args, ok), retrieved chunk ids, memory keys used, iterations, latency, input/output tokens (`null` if the provider doesn't report them), provider/model, error kind. Tool results and prompts are never stored.

`eval/cases_a1.json` has 13 cases: fee status, portal-failure policy, scholarship, memory write, memory recall in a new session, OTP not stored, temporary info not stored, unsupported policy (`no_policy`), course-change rule, ticket creation, tool outage, small talk, missing ticket details. Checks are rule-based (required/forbidden tools, answer content, memory and ticket side-effects). `no_policy` checks *behaviour*: the agent used `search_policy`, acknowledges missing information (wording-tolerant patterns), and makes no unsupported policy claim (no citation without retrieved evidence, no affirmative refund statement). The eval runs on an isolated DB (`eval/.eval_data/eval.db`) and never touches `data/students.db`. Output: `eval/results_a1.md` (per-case result, tools, tool-choice ✓/✗, evidence, latency, tokens, observations); an existing results file is archived as `results_a1.prev-<timestamp>.md` before being replaced.

## Setup (Windows PowerShell)
```powershell
cd C:\Users\Aviral\Downloads\student-support-agent-a1-gemini\student-support-agent
python -m venv .venv                      # skip if it exists
.\.venv\Scripts\Activate.ps1              # if blocked: Set-ExecutionPolicy -Scope Process Bypass
pip install -r requirements.txt
Copy-Item .env.example .env               # skip if .env exists
notepad .env                              # LLM_PROVIDER=groq, GROQ_API_KEY=<your key>, MODEL=openai/gpt-oss-20b
```
`.env` is git-ignored; never paste the key into code, README, screenshots or chat (revoke it at console.groq.com/keys if exposed).

## Run
```powershell
python -m compileall -q .
python -m unittest discover -s tests -t .          # offline: no key, no network
python scripts\smoke_groq.py --list-models         # live, metadata only
python scripts\smoke_groq.py                       # live: ONE text request
python scripts\smoke_groq.py --with-tool           # live: ONE synthetic tool-call request
streamlit run app.py
python eval\run_eval.py                            # dry run: prints expected call count
python eval\run_eval.py --yes                      # live full eval (13 turns, ~28 calls typical, max 65) after smoke tests pass
python eval\run_eval.py --yes --only no_policy                 # live single case -> eval\results_a1_partial.md
python eval\run_eval.py --yes --only no_policy --merge         # live single case, replaces only that row in results_a1.md (provenance noted)
```
Free tier: limits are account-specific (console.groq.com/settings/limits); calls are spaced by `LLM_MIN_INTERVAL_S` (default 2 s) and SDK retries are capped (`GROQ_MAX_RETRIES` ≤ 3). **Do not upgrade or add payment details.** There is no automatic fallback to another provider. Other providers: `pip install -r requirements-optional.txt` and see `.env.example`.

## Limitations
- The sidebar student selector is a **demonstration mechanism, not authentication**; anyone can pick any student. Real identity, authorization and approval are Assignment 2.
- Redaction and the memory filter are regex-based (best effort). Retrieval is BM25 over 6 chunks; borderline queries can return a loosely related chunk, so the prompt tells the model to abstain if chunks don't answer.
- Eval latency includes the configured call spacing; 13 rule-based cases on synthetic data are a small sample.
- Memory written earlier in a turn is kept if a later provider call in that turn fails.
