"""
core/tool_registry.py — Pocket Tool Registry
───────────────────────────────────────────────────────────────────────────────
Schema-first registry that replaces the if/elif command chain in
pocket.py's cli_input_loop().

Each tool is one Tool entry: a command name (+ aliases), a handler, a
human/model-facing description, and a JSON-schema for its parameters.

For now the schema is METADATA. CLI commands are typed by the user and arrive
already-structured, so there is nothing malformed to reject — validation is not
exercised on this path. The schema is here as a first-class field so the later
natural-language dispatch cut (model emits a tool call → validate against this
schema → route high-risk calls through propose_action()) plugs straight in
without reshaping the registry.

Handlers currently live in pocket.py because several touch engine-level state
(overlay/monitor for shutdown, project_root for path resolution). Which handlers
become model-callable — and whether they move into core — is the "agent→tool
path" decision gated AFTER this cut, so it is deliberately not decided here.
"""

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Tool:
    name: str                                   # canonical command, e.g. "/read"
    handler: Callable[[str], None]              # receives the raw argument string ("" if none)
    description: str                            # human + (later) model-facing
    params_schema: dict = field(default_factory=dict)  # JSON-schema; metadata for now
    risk: str = "low"                          # "low" | "medium" | "high" — gating hint for NL dispatch
    aliases: tuple = ()                        # extra tokens that map to this tool
    exact: bool = False                        # match only on full input (bare-word aliases like quit/exit/bye)
    takes_args: bool = False                   # if True and no args given → print usage
    arg_hint: str = ""                         # placeholder for the help line, e.g. "<file>"
    usage: str = ""                            # shown when a required arg is missing
    model_callable: bool = False               # opt-in: exposed to the model as an Ollama tool (4.5f NL dispatch)
    model_handler: "Callable[[dict], str] | None" = None  # model path: validated args dict → result text for the model


class ToolRegistry:
    """
    Maps command tokens (name + aliases) to Tools and dispatches raw CLI lines.

    dispatch() returns True if a tool handled the line, False if the caller
    should fall through to normal conversation. That boolean is the ONLY
    behavioural contract the CLI loop depends on.

    Two match modes:
      - first-token match (slash commands): token = first word, rest = args
      - exact match (exact=True, e.g. quit/exit/bye): whole input must equal
        the token, so common English words don't hijack a conversation line
        ("bye now, see you tomorrow" stays conversation).
    """

    def __init__(self):
        self._by_token: dict[str, Tool] = {}   # first-token matched (slash commands)
        self._by_exact: dict[str, Tool] = {}   # full-input matched (bare-word aliases)
        self._ordered: list[Tool] = []

    def register(self, tool: Tool) -> None:
        if tool.model_callable and tool.model_handler is None:
            # Slash handlers print and start their own turn; calling one from
            # inside a turn would deadlock on the turn mutex. The model path
            # needs a handler that RETURNS its result instead.
            raise ValueError(f"model_callable tool needs a model_handler: {tool.name}")
        target = self._by_exact if tool.exact else self._by_token
        for token in (tool.name, *tool.aliases):
            token = token.lower()
            if token in self._by_token or token in self._by_exact:
                raise ValueError(f"tool token already registered: {token}")
            target[token] = tool
        self._ordered.append(tool)

    def get(self, token: str) -> "Tool | None":
        t = token.lower()
        return self._by_exact.get(t) or self._by_token.get(t)

    def get_function(self, name: str) -> "Tool | None":
        """Look up a model-callable tool by its Ollama function name ("read")."""
        for t in self._ordered:
            if t.model_callable and t.name.lstrip("/") == name:
                return t
        return None

    def tools(self) -> list:
        """Tools in registration order (for the help line / a future /help)."""
        return list(self._ordered)

    def to_ollama_tools(self) -> list[dict]:
        """
        Export model-callable tools as Ollama's `tools` array (4.5f NL dispatch).

        Only tools with model_callable=True are exposed — opt-in, so a new tool
        is never handed to the model by accident. The function name drops the
        leading slash ("/read" → "read"); params_schema is passed through as
        plain JSON Schema (keeps the Stage 7 MCP adapter free).

        Ollama does NOT validate arguments against these schemas. Validation on
        receipt stays our job (impr. #2), and every model-originated call still
        routes through propose_action() (ADR-001: model invocation ≠ approval).
        """
        out = []
        for t in self._ordered:
            if not t.model_callable:
                continue
            out.append({
                "type": "function",
                "function": {
                    "name": t.name.lstrip("/"),
                    "description": t.description,
                    "parameters": t.params_schema or {"type": "object", "properties": {}},
                },
            })
        return out

    def format_commands(self) -> str:
        """Build the 'Commands: ...' line from the live registry (never stale)."""
        parts = [f"{t.name} {t.arg_hint}".strip() for t in self._ordered]
        return "Commands: " + "  ".join(parts)

    def dispatch(self, user_input: str) -> bool:
        """
        Route one raw input line. Returns True if a registered tool handled it,
        False if it should fall through to normal conversation.

        Token match is case-insensitive; the argument string keeps its original
        case (paths, queries, etc. must not be lowercased).
        """
        # Exact-match tools first (bare-word aliases must equal the whole line).
        tool = self._by_exact.get(user_input.lower())
        if tool is not None:
            tool.handler("")
            return True

        token, _, args = user_input.partition(" ")
        tool = self._by_token.get(token.lower())
        if tool is None:
            return False

        args = args.strip()
        if tool.takes_args and not args:
            print(f"  {tool.usage}\n")
            return True

        tool.handler(args)
        return True


# Module-level singleton — matches the memory_module / tts_module / bus pattern.
registry = ToolRegistry()