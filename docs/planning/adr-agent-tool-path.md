
# ADR-001 — Agent→Tool Path: Wire It, Uniform Gating

**Status:** Accepted
**Date:** 2026-08-02
**Stage:** 4.5f (conversation refactor)
**Relates to:** impr. #2 (schema contract), impr. #3 (LLM-out-of-execution-loop), Stage 7 (tool ecosystem), Stage 8 / 8p (supervised autonomy)

---

## Context

As of the tool-registry cut, every action Pocket takes is human-triggered. There
is no path from an LLM response to the executor / file_editor / web search. Every
tool runs because the user typed a slash command.

The slash path carries a trust assumption: *the user typed it, so their invocation is
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

Flow:model response
→ extract tool call
→ validate args against the tool's params_schema (impr. #2 — schema is the boundary)
→ look up the tool in the registry (registry defines the legal shapes)
→ propose_action() ── y/n ──▶ execute (hard stop; the LLM never self-approves)
└─ n ─▶ decline + log `propose_action()` is the single hard stop. Execution happens only on an explicit
`y`. Malformed or schema-invalid tool calls trigger a **re-request**, not a silent
`try/except` swallow and not a best-effort run.

## The Invariant (non-negotiable)

> **Model invocation ≠ approval.**

Every model-originated tool call routes through `propose_action()`. No exceptions,
no per-tool "this one is safe to auto-run" carve-outs. This is the explicit inverse
of the slash path: a typed `/search` skips approval because the human typing *is*
the intent; a model-emitted `/search` does not, because the model emitting it is
not.

Concretely, the agent→tool path must **not** reuse the slash handlers' trust
shortcuts:
- a model-originated web search runs with approval required, even though `/search`
  passes `require_approval=False`;
- a model-originated exec routes through the gate, never around it.

This makes the LLM-out-of-execution-loop principle (impr. #3) concrete: the model
decides *what*; the registry defines the *legal shapes*; the executor accepts only
*validated* calls; `propose_action()` is the deterministic *hard stop*. Nothing
routes around the gate — no broad `try/except` around execution, no fallback path.
The prompt-stance ("external content is data, not instruction") remains a *soft*
defense that makes Pocket *try* to behave; the gate is the *hard* layer that
*enforces* it. The soft layer is never the only thing between Pocket and a
real-world action.

## On the `risk` field (honest scope)

The registry's `risk` field (`low`/`medium`/`high`) does **not** change runtime
behavior under this decision. Uniform gating means every call gates identically
regardless of `risk`. `risk` stays metadata here.

It becomes behaviorally load-bearing later, at **8p**, where the sole relaxation of
the every-action-approved model (6i.8 pre-approved maintenance) needs a risk floor
to scope a tiny whitelist against — inside the sandbox, with exhaustive logging,
only after the executor is provably safe. Until then `risk` documents intent; it
does not gate. This ADR records that so a future reader does not assume `risk`
already filters anything.

## Alternatives considered

**Human-only for now (document, don't wire).** Safest option; defers all agent→tool
risk. Rejected because the machinery (registry, schemas, `risk`, a working gate)
already exists, so deferring buys little safety — uniform gating is already
conservative — while guaranteeing Stage 8 revisits this on a colder codebase. The
cost of deciding now is one document; the cost of deferring is re-derching the
decision later.

**Per-tool auto-run for low-risk calls.** Rejected as premature. Skepticism is the
default; the y/n prompt is cheap; auto-run is exactly the softening the impr. #3
boundary forbids at this stage. Any relaxation waits for 8p's hard gate.

## Consequences

Positive:
- The agent→tool path is defined; Stage 8 no longer assumes a path that doesn't exist.
- `params_schema` stops being dead metadata — it becomes the validation boundary the
  moment NL dispatch lands.
- The gate discipline is uniform and auditable: every model action is one line in
  `decisions.jsonl`.

Costs / risks:
- Every model-proposed action is a y/n interrupt. This is friction by design at this
  stage; 8p is the only place it is ever relaxed, and only under hard gating.
- The extraction/validation layer (model output → tool call) is new attack surface;
  it must fail *closed* (re-request / decline), never *open* (best-effort run).

## Scope of this ADR

This is a **decision**, not a build. No orchestrator changes, no NL-dispatch code
land with this document. The next 4.5f cut — natural-language tool dispatch —
*implements* this decision: it exposes registered tools as model-callable schemas,
validates emitted calls against `params_schema`, and routes them through
`propose_action()` per the invariant above. Slash commands stay as the fast path.

