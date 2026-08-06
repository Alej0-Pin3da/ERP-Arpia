import asyncio
import os
import sys
import threading

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _BACKEND_DIR)
os.chdir(_BACKEND_DIR)

from a2wsgi import ASGIMiddleware
from a2wsgi.asgi import ASGIResponder
from app.main import app


class ForkSafeASGIMiddleware(ASGIMiddleware):
    """a2wsgi wrapper safe for Passenger/LiteSpeed smart spawning.

    ASGIMiddleware starts a background event-loop thread at import time.
    Passenger/LiteSpeed forks worker children after import and threads do not
    survive fork: the loop exists in the child but nothing serves it, so every
    request hangs and the worker is killed (signal 15).

    This wrapper creates a fresh loop + runner thread per request and tears
    it down when the response generator is exhausted.
    """

    def __init__(self, app, wait_time=None):
        self.app = app
        self.wait_time = wait_time

    def __call__(self, environ, start_response):
        loop = asyncio.new_event_loop()
        thread = threading.Thread(target=loop.run_forever, daemon=True)
        thread.start()
        try:
            responder = ASGIResponder(self.app, loop, self.wait_time)
        except Exception:
            loop.call_soon_threadsafe(loop.stop)
            thread.join(timeout=2)
            raise
        return self._run(responder(environ, start_response), loop, thread)

    def _run(self, chunks, loop, thread):
        try:
            for chunk in chunks:
                yield chunk
        finally:
            loop.call_soon_threadsafe(loop.stop)
            thread.join(timeout=2)


application = ForkSafeASGIMiddleware(app)
