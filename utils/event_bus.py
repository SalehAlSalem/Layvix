import collections
import asyncio
import threading

class BroadcastManager:
    """
    Thread-Safe Central Hub for broadcasting events.
    This is the SINGLE SOURCE OF TRUTH for event propagation.
    Now with SSE Backpressure via bounded deque.
    """
    MAX_QUEUE = 500

    def __init__(self):
        self.loop = None
        self._buffer = collections.deque(maxlen=self.MAX_QUEUE)
        self._subscribers = []
        self._lock = threading.Lock()
        self._closed = False

    def init(self, loop: asyncio.AbstractEventLoop):
        """Called by the FastAPI Bridge on startup to attach the main event loop."""
        self.loop = loop

    def subscribe(self) -> asyncio.Queue:
        """Returns a new async Queue for an SSE client."""
        q = asyncio.Queue(maxsize=self.MAX_QUEUE)
        with self._lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q):
        """Removes an active subscriber queue."""
        with self._lock:
            if q in self._subscribers:
                self._subscribers.remove(q)

    def publish(self, data):
        """
        Safely publishes data from ANY thread to the async event loop.
        Safe against early execution (before FastAPI starts).
        """
        if self.loop is None or self._closed:
            return
            
        # Append to buffer (drops oldest if full automatically)
        self._buffer.append(data)
            
        try:
            with self._lock:
                current_subs = list(self._subscribers)
            for q in current_subs:
                self.loop.call_soon_threadsafe(
                    lambda _q=q: _q.put_nowait(data) if not _q.full() else None
                )
        except Exception:
            pass  # Publish should NEVER crash the calling thread

    def close(self):
        """Closes the manager to new events, useful during shutdown."""
        self._closed = True

# Global Singleton Instance
event_bus = BroadcastManager()
