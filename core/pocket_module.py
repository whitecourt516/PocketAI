# core/pocket_module.py
# Stage 4s — Module Lifecycle Contract
#
# Every core module inherits from PocketModule and implements all four methods.
# This gives 4j (startup health checks), 4q (event bus), 4r (state manager),
# and 4n (WebSocket reconnection) a single consistent interface to work with.
#
# Rules:
#   - start()        must be safe to call exactly once at launch
#   - stop()         must be safe to call exactly once on clean shutdown
#   - health_check() must return True/False only — no exceptions, no side effects
#   - on_event()     receives a dict from the event bus; unknown events are ignored
#
# Python enforces the contract at instantiation time via abc.ABC.
# If a subclass is missing any of these four methods, Python raises a
# TypeError before the module is ever used.

from abc import ABC, abstractmethod


class PocketModule(ABC):
    """Base class for all Pocket core modules.

    Subclasses must implement all four abstract methods.
    Attempting to instantiate a subclass that is missing any of them
    raises TypeError immediately — caught at startup, not mid-session.
    """

    @abstractmethod
    def start(self) -> None:
        """Called once at launch, in dependency order.

        Use for: loading models, opening connections, starting threads,
        bootstrapping data. Must not block indefinitely — if a service is
        unavailable, log the failure and return; let health_check() report it.
        """

    @abstractmethod
    def stop(self) -> None:
        """Called once on clean shutdown, in reverse dependency order.

        Use for: draining queues, closing connections, stopping threads,
        flushing buffers. Should complete quickly and never raise.
        """

    @abstractmethod
    def health_check(self) -> bool:
        """Return True if this module is ready to serve requests, False otherwise.

        Called by 4j at startup and by 4j.1 during the session.
        Must never raise an exception — catch internally and return False.
        Must have no side effects — it is called repeatedly.
        """

    @abstractmethod
    def on_event(self, event: dict) -> None:
        """Called by the event bus (4q) when an event is emitted.

        The event dict always contains at least:
            {"type": "<event_name>", ...payload fields...}

        Modules ignore event types they don't care about.
        Must never raise — unknown event types are silently skipped.
        """
