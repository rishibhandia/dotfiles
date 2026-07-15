---
name: gemini-billing-blocks
description: Debugging Gemini / llm-gemini calls that return empty text, JSONDecodeError, or fast-fail across a batch. Use when a Gemini/LLM tagging or extraction loop suddenly speeds up, floods errors, or returns empty responses — often a billing cap, not a code bug.
---

# Gemini billing blocks masquerade as empty-response bugs

## Problem
A working Gemini batch (Simon Willison's `llm` + `llm-gemini`) suddenly starts failing:
every call returns empty/parse-fails, and throughput **spikes** (e.g. 0.2 → 6 items/sec)
because each call errors instantly instead of doing real work. Easy to misread as a
code/data bug or rate-limiting.

## Cause
A billing block returns an **empty completion**, so `resp.text()` is empty →
`json.loads("")` raises `JSONDecodeError` → your error path fires immediately (no
backoff). The two messages (seen via a direct `model.prompt(...)` call):

- `"Your project has exceeded its monthly spending cap"` → raise it at **ai.studio/spend**
- `"Your prepayment credits are depleted"` → add funds at **ai.studio/projects**

Neither string contains `rate` / `quota` / `429`, so rate-limit backoff logic won't
catch it.

## Diagnose
- A sudden **throughput jump** + a flood of `confidence:"error"` (or empty results) =
  fast-failing, not working.
- Confirm with one live call — it surfaces the exact message as a `ModelError`:
  ```python
  import llm
  print(llm.get_model("gemini-3.5-flash").prompt('reply {"ok":true}').text())
  ```

## Recover
1. Clear the block (raise cap / add credits).
2. Live-test one call to confirm it's flowing again.
3. Reset the fast-failed rows (mark them un-tagged) and resume — keep the pipeline
   resumable/idempotent so this is cheap.

## Gotchas & perf notes
- Make error-return dicts include **all** expected keys — a partial error dict causes a
  `KeyError` crash downstream when you serialize it.
- Sequential `llm` calls to a premium flash model run ~0.2/s (latency-bound). A
  `ThreadPoolExecutor` (~8 workers, DB writes kept single-threaded in the consumer) gets
  ~9/s. `flash-lite` is ~6× cheaper ($0.25/$1.50 vs $1.50/$9.00 per 1M) and, on many
  classification tasks, about as good.

## When to use
Any bulk Gemini / `llm` job that starts returning empty responses, JSONDecode errors, or
unexpectedly races through items.
