# core/event_bus.py
# Stage 4q — Event Bus
# Synchronous publish/subscribe message bus.
# Modules emit named events; subscribers handle them in registration order.
# Nothing calls another module directly — it emits and moves on.
#
# Stage 4s: EventBusModule implements PocketModule.
#   start()        — no-op; bus is ready at import time
#   stop()         — clears all subscriptions cleanly
#   health_check() — confirms at least the core subscriptions are registered
#   on_event()     — not applicable; the bus IS the event system

import traceback
from collections import defaultdict
from typing import Callable

from core.pocket_module import PocketModule


# ═════════════════════════════════════════════════════════════════════════════
# EVENT BUS
# ═════════════════════════════════════════════════════════════════════════════

class EventBus:
    """
    Synchronous publish/subscribe event bus.
    Emit blocks until all subscribers for that event have run.

    Usage:
        bus.subscribe("avatar.expression", my_handler)
        bus.emit("avatar.expression", {"name": "happy", "source": "llm"})

    Handler signature:
        def my_handler(event: dict) -> None
    """

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Register a handler for an event type."""
        if not callable(handler):
            raise TypeError(f"Handler for '{event_type}' must be callable, got {type(handler)}")
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Remove a specific handler for an event type."""
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)

    def unsubscribe_all(self, event_type: str = None) -> None:
        """Remove all handlers. Pass event_type to clear one type, omit to clear all."""
        if event_type:
            self._subscribers[event_type].clear()
        else:
            self._subscribers.clear()

    def emit(self, event_type: str, payload: dict = None) -> None:
        """
        Fire an event. Calls all subscribers synchronously in registration order.
        A failing subscriber logs the error and does not block the remaining subscribers.
        """
        if payload is None:
            payload = {}

        event = {"type": event_type, **payload}
        handlers = list(self._subscribers.get(event_type, []))

        for handler in handlers:
            try:
                handler(event)
            except Exception:
                print(f"  [EventBus] ERROR in handler for '{event_type}' ({handler.__name__}):")
                traceback.print_exc()

    def subscribers_for(self, event_type: str) -> list:
        """Return list of registered handlers for an event type. Useful for debugging."""
        return list(self._subscribers.get(event_type, []))

    def all_event_types(self) -> list:
        """Return all event types that have at least one subscriber."""
        return [k for k, v in self._subscribers.items() if v]

    def __repr__(self) -> str:
        lines = ["[EventBus] Registered subscriptions:"]
        for event_type, handlers in self._subscribers.items():
            if handlers:
                names = ", ".join(h.__name__ for h in handlers)
                lines.append(f"  {event_type} → {names}")
        if len(lines) == 1:
            lines.append("  (none)")
        return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════════
# LIFECYCLE — Stage 4s
# ═════════════════════════════════════════════════════════════════════════════

class EventBusModule(PocketModule):
    """
    Lifecycle wrapper for the event bus.
    start() is a no-op — the bus singleton is ready at import time.
    stop() clears all subscriptions for clean shutdown.
    health_check() confirms the bus is instantiated and callable.
    """

    def start(self) -> None:
        pass

    def stop(self) -> None:
        bus.unsubscribe_all()

    def health_check(self) -> bool:
        try:
            assert callable(bus.emit)
            assert callable(bus.subscribe)
            return True
        except Exception as e:
            print(f"  [EventBusModule] health_check error: {e}")
            return False

    def on_event(self, event: dict) -> None:
        # The bus is the event system — it doesn't consume its own events.
        pass


# Singletons — import these everywhere
bus = EventBus()
event_bus_module = EventBusModule()