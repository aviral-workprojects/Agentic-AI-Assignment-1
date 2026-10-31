import json, time
from . import context, redact, tools, trace
from .providers.base import LLMError, USER_MESSAGES

MAX_ITERS = 5

def chat(provider, sid, history, question):
    """One user turn. history = plain [{role, content}] (mutated only on success). Secrets are redacted before
    reaching the model, history or trace."""
    t0 = time.time()
    q = redact.redact(question)
    system, msgs, mems = context.build(sid, q, history)
    tr = {"student": sid, "q": q, "provider": provider.name, "model": provider.model, "tools": [], "chunks": [],
          "memories": list(mems), "in_tok": 0, "out_tok": 0, "usage_available": True, "iters": 0, "error": None}
    answer, ok = "", False
    try:
        for _ in range(MAX_ITERS):
            r = provider.generate(system, msgs, tools.SCHEMAS)
            tr["iters"] += 1
            if r.in_tok is None or r.out_tok is None:
                tr["usage_available"] = False
            tr["in_tok"] += r.in_tok or 0
            tr["out_tok"] += r.out_tok or 0
            if not r.tool_calls:
                answer, ok = r.text.strip(), True
                break
            msgs.append({"role": "assistant", "text": r.text, "tool_calls": r.tool_calls})
            results = []
            for tc in r.tool_calls:
                res = tools.run(tc.name, tc.args if tc.args_valid else None, sid)
                tr["tools"].append({"name": tc.name, "args": {k: str(v) for k, v in tc.args.items()} if tc.args_valid else {},
                                    "ok": "error" not in res})
                tr["chunks"] += [c["id"] for c in res.get("chunks", [])]
                results.append({"id": tc.id, "name": tc.name, "content": json.dumps(res)})
            msgs.append({"role": "tool", "results": results})
        else:
            answer, ok = "Sorry, I couldn't complete that. Please try again or raise a support ticket.", True
    except LLMError as e:
        tr["error"] = {"kind": e.kind, "code": e.code}
        answer = USER_MESSAGES.get(e.kind, USER_MESSAGES["unknown"])
    if tr["error"] is None and not answer:
        answer = "I couldn't produce an answer. Please rephrase your question."
    if not tr["usage_available"]:   # provider did not report usage on some call: do not present partial sums as real
        tr["in_tok"] = tr["out_tok"] = None
    tr["latency_s"] = round(time.time() - t0, 2)
    tr["answer"] = answer
    if ok:  # failed provider call leaves the conversation untouched
        history += [{"role": "user", "content": q}, {"role": "assistant", "content": redact.redact(answer)}]
    trace.log(tr)
    return answer, tr
