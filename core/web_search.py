# core/web_search.py
# Web search (4h) — pluggable backend, consent-gated, audit-logged.
#
# Backends are swappable via config.yaml -> web_search.backend.
# Only the backend function changes; the public search() API stays fixed, so
# moving from Tavily (cloud) to SearXNG (local) later touches one function.
#
# Public API:
#   search(query, require_approval=True) -> dict
#   format_for_llm(result)               -> str
#
# Result dict shape:
#   {
#       "ok":      bool,
#       "query":   str,
#       "results": [{"title": str, "url": str, "content": str}, ...],
#       "answer":  str | None,     # backend summary, if available
#       "error":   str | None,
#   }
#
# Stage 4s: WebSearchModule implements PocketModule.
#   start()        — no-op; the backend client is created lazily per call
#   stop()         — no-op; nothing persistent to close
#   health_check() — verifies the active backend is configured (key/url present).
#                    Does NOT hit the network — avoids burning Tavily credits and
#                    avoids needing internet at startup. Web search is optional,
#                    so do NOT add this module to run_startup_checks().
#   on_event()     — handles "web.search" events for future bus-driven search (5b)

import os

from core.config_loader import CFG
from core.event_bus import bus
from core.permissions import log_decision, record_outcome
from core.pocket_module import PocketModule


# ── Config ────────────────────────────────────────────────────────────────────
# .get() with defaults so a missing web_search block never KeyErrors at import.
_WS          = CFG.get("web_search", {})
BACKEND      = _WS.get("backend", "tavily")
MAX_RESULTS  = _WS.get("max_results", 5)
SEARCH_DEPTH = _WS.get("search_depth", "basic")   # basic = 1 credit, advanced = 2
MAX_CONTENT  = _WS.get("max_content_chars", 500)  # per-result truncation


# ═════════════════════════════════════════════════════════════════════════════
# CONSENT — search-specific, mirrors permissions.propose_action() style
# ═════════════════════════════════════════════════════════════════════════════
# We deliberately do NOT route the query through is_command_allowed(). That
# denylist (rm -rf, format, shutdown, ...) is for SHELL commands — a query like
# "how to format a USB drive" would be falsely blocked. Search still gets a y/n
# gate for Pocket-initiated calls and is logged to the same decision log.

def _confirm_search(query: str) -> bool:
    print("\n" + "─" * 50)
    print("  Pocket wants to:")
    print(f"  Search the web for: {query}")
    print()
    print(f"  Backend: {BACKEND}")
    print("─" * 50)

    try:
        response = input("  Approve? [y/n]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        response = "n"

    approved = response == "y"
    log_decision(
        description=f"Search the web for: {query}",
        command=f"web_search[{BACKEND}]: {query}",
        approved=approved,
    )
    print("  [Approved]\n" if approved else "  [Rejected]\n")
    return approved


# ═════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═════════════════════════════════════════════════════════════════════════════

def search(query: str, require_approval: bool = True) -> dict:
    """Search the web via the configured backend.

    require_approval=True  — Pocket-initiated: prompts the user for y/n.
    require_approval=False — the user typed /search themselves: no prompt, still logged.
    """
    query = (query or "").strip()
    if not query:
        return _fail(query, "empty query")

    command = f"web_search[{BACKEND}]: {query}"

    if require_approval:
        if not _confirm_search(query):
            return _fail(query, "rejected by the user")
    else:
        # Explicit /search — the user's invocation is the approval, but still log it.
        log_decision(description=f"Search the web for: {query}",
                     command=command, approved=True)

    try:
        if BACKEND == "tavily":
            result = _search_tavily(query)
        elif BACKEND == "searxng":
            result = _search_searxng(query)
        else:
            return _fail(query, f"unknown backend '{BACKEND}'")
    except Exception as e:
        record_outcome(command, f"error: {e}")
        return _fail(query, str(e))

    record_outcome(command, f"ok: {len(result['results'])} results")
    return result


def format_for_llm(result: dict) -> str:
    """Turn a result dict into a clean text block for handle_user_input_sync()."""
    if not result["ok"]:
        return f"(web search failed: {result['error']})"

    lines = []
    if result.get("answer"):
        lines.append(f"Summary: {result['answer']}\n")

    for i, r in enumerate(result["results"], 1):
        lines.append(f"[{i}] {r['title']}")
        lines.append(f"    {r['url']}")
        lines.append(f"    {r['content']}")
        lines.append("")

    return "\n".join(lines).strip()


# ── Internal helpers ──────────────────────────────────────────────────────────

def _fail(query: str, error: str) -> dict:
    return {"ok": False, "query": query, "results": [], "answer": None, "error": error}


def _truncate(text: str) -> str:
    text = (text or "").strip()
    return text if len(text) <= MAX_CONTENT else text[:MAX_CONTENT].rstrip() + "…"


# ═════════════════════════════════════════════════════════════════════════════
# BACKENDS — only these change when swapping providers
# ═════════════════════════════════════════════════════════════════════════════

def _search_tavily(query: str) -> dict:
    """Tavily cloud backend. Returns LLM-ready results in one call."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY not set in .env")

    # Lazy import — keeps this module importable even if tavily-python isn't
    # installed yet, so pocket.py won't crash on startup over an optional feature.
    from tavily import TavilyClient

    client   = TavilyClient(api_key=api_key)
    response = client.search(
        query,
        max_results=MAX_RESULTS,
        search_depth=SEARCH_DEPTH,
        include_answer=True,
    )

    results = [
        {
            "title":   r.get("title", ""),
            "url":     r.get("url", ""),
            "content": _truncate(r.get("content", "")),
        }
        for r in response.get("results", [])
    ]

    return {
        "ok":      True,
        "query":   query,
        "results": results,
        "answer":  response.get("answer"),
        "error":   None,
    }


def _search_searxng(query: str) -> dict:
    """Local SearXNG backend — Stage 6/7 upgrade path.

    SearXNG returns ranked URLs + snippets but NOT clean page content, so a
    fully local solution also needs a fetch/extract step (requests + a
    readability extractor) bolted on here before returning. Stubbed until then.
    """
    raise NotImplementedError("SearXNG backend not built yet — see Stage 6/7")


# ═════════════════════════════════════════════════════════════════════════════
# LIFECYCLE — Stage 4s
# ═════════════════════════════════════════════════════════════════════════════

class WebSearchModule(PocketModule):
    """Lifecycle wrapper for web search.

    start()        — no-op. Backend clients are created lazily per search() call.
    stop()         — no-op. Nothing persistent to close.
    health_check() — verifies the active backend is configured WITHOUT making a
                     network call (costs no Tavily credits, works offline). Web
                     search is optional — do NOT add this module to
                     run_startup_checks(); a missing key shouldn't block boot.
    on_event()     — handles {"type": "web.search", "text": "..."} for future
                     bus-driven proactive search (Stage 5b).
    """

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def health_check(self) -> bool:
        try:
            if BACKEND == "tavily":
                return bool(os.getenv("TAVILY_API_KEY"))
            if BACKEND == "searxng":
                return bool(_WS.get("searxng_url"))
            return False
        except Exception as e:
            print(f"  [WebSearchModule] health_check error: {e}")
            return False

    def on_event(self, event: dict) -> None:
        if event.get("type") != "web.search":
            return
        text = event.get("text", "")
        if not text:
            return
        result = search(text)  # require_approval=True — Pocket-initiated
        if result["ok"]:
            # 4.5g: hand the results to the LLM over the bus (no lazy import of
            # core.llm). persist=False matches /search: web results stay out of
            # vector memory.
            bus.emit("llm.query", {
                "text": (f"I searched the web for: {text}\n\n"
                         f"Here are the results:\n\n{format_for_llm(result)}"),
                "persist": False,
            })


web_search_module = WebSearchModule()
