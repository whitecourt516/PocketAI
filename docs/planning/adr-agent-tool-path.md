
# ADR-001 — Agent→Tool Path: Wire It, Uniform Gating

**Status:** Accepted
**Date:** 2026-08-02
**Stage:** 4.5f (conversation refactor)
**Relates to:** impr. #2 (schema contract), impr. #3 (LLM-out-of-execution-loop), Stage 7 (tool ecosystem), Stage 8 / 8p (supervised autonomy)

---

## Context

As of the tool-registry cut, every action Pocket takes is human-triggered. There
is no path from an LLM response to the executor / file_editor / web search. Every
tool runs because user typed a slash command.

The slash path carries a trust assumption: *user typed it, so his invocation is
the approval.* `/search` passes `require_approval=False`; `/exec` gates
internally; `/edit` relies on backup-before-write. That assumption is correct for
typed commands and **does not survive** the model emitting the call.

Stage 8 (co-pilot, supervised autonomy) assumes an agent→tool path exists. It does
not. This ADR decides whether it does and what shape it takes, while the registry
is fresh — rather than leaving Stage 8 to hit this decision on a colder codebase.

The scaffolding this decision needs is already built:
- the tool registry (name / handler / description / `params_schema` / `risk`),
- a working `propose_action()` y/n gate + `logs/decisions.jsonl`,
- the 4.5c constrained executor (parsed, working-dir-constrained, secret-path-blocked).

## Decision

**Wire the path. Gate every model-originated call uniformly through
`propose_action()`.**

Flow:
**Status:** Accepted
**Date:** 2026-08-02
**Stage:** 4.5f (conversation refactor)
**Relates to:** impr. #2 (schema contract), impr. #3 (LLM-out-of-execution-loop), Stage 7 (tool ecosystem), Stage 8 / 8p (supervised autonomy)

---

## Context

As of the tool-registry cut, every action Pocket takes is human-triggered. There
is no path from an LLM response to the executor / file_editor / web search. Every
tool runs because user typed a slash command.

The slash path carries a trust assumption: *user typed it, so his invocation is
the approval.* `/search` passes `require_approval=False`; `/exec` gates
internally; `/edit` relies on backup-before-write. That assumption is correct for
typed commands and **does not survive** the model emitting the call.

Stage 8 (co-pilot, supervised autonomy) assumes an agent→tool path exists. It does
not. This ADR decides whether it does and what shape it takes, while the registry
is fresh — rather than leaving Stage 8 to hit this decision on a colder codebase.

The scaffolding this decision needs is already built:
- the tool registry (name / handler / description / `params_schema` / `risk`),
- a working `propose_action()` y/n gate + `logs/decisions.jsonl`,
- the 4.5c constrained executor (parsed, working-dir-constrained, secret-path-blocked).

## Decision

**Wire the path. Gate every model-originated call uniformly through
`propose_action()`.**

Flow: