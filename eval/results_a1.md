Provider/model: `groq/openai/gpt-oss-20b`  (call spacing 2.0s included in latency)

| case | result | tools used | tool choice | evidence | latency s | in tok | out tok | note |
|---|---|---|---|---|---|---|---|---|
| fee_status | PASS | get_fee_status | ✓ | - | 4.9 | 1139 | 115 |  |
| portal_failed | PASS | search_policy | ✓ | payment-portal-failure | 8.1 | 1192 | 145 |  |
| scholarship | PASS | get_scholarship_status | ✓ | - | 5.3 | 1121 | 110 |  |
| memory_write | PASS | save_memory | ✓ | - | 5.5 | 1123 | 107 |  |
| memory_recall_new_session | PASS | - | ✓ | mem:preferred_contact | 4.0 | 548 | 58 |  |
| sensitive_otp | PASS | - | n/a | - | 2.6 | 542 | 96 |  |
| temporary_info | PASS | - | n/a | - | 2.9 | 537 | 104 |  |
| no_policy | PASS | search_policy | ✓ | - | 5.7 | 1149 | 103 |  |
| course_change | PASS | search_policy | ✓ | course-change | 5.2 | 1172 | 147 |  |
| create_ticket | PASS | create_support_ticket | ✓ | - | 5.7 | 1155 | 215 |  |
| tool_error | PASS | get_fee_status | ✓ | - | 5.4 | 1096 | 137 |  |
| small_talk | PASS | - | ✓ | - | 5.4 | 536 | 77 |  |
| missing_info | PASS | - | ✓ | - | 2.4 | 532 | 120 |  |

**Accuracy:** 13/13 executed (100%); 0 errored/not run  
**Tool selection appropriate:** 11/11 cases with a tool expectation  
**Latency:** mean 4.9s, p95 8.1s  
**Tokens:** in 11842, out 1534 over 13/13 cases with provider-reported usage

**Key observations / known limitations**
- Pass/fail is rule-based (tool use, answer content, memory and ticket side-effects, abstention); it is not human-graded. Wording checks can mis-grade correct answers, so read FAIL notes.
- Evidence = handbook chunk ids returned by `search_policy` plus `mem:<key>` for memories injected into context. `-` means none: for an unsupported question this is the correct outcome (nothing relevant was retrieved).
- Tool choice: ✓ = all required tools used and no forbidden tool used for that case; n/a = the case sets no tool expectation (or the row comes from an earlier run without that column).
- Latency is wall-clock per case and INCLUDES the configured spacing between LLM calls (`LLM_MIN_INTERVAL_S`) and any bounded SDK retry waits; it is not pure model latency.
- Token counts are provider-reported (Groq `prompt_tokens` / `completion_tokens`; completion includes reasoning tokens). `n/a` = not reported; nothing is estimated.
- 13 cases on synthetic data is a small sample. The Assignment 1 student selector is a demo, not authentication.
