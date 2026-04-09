"""
Shared pytest fixtures for CEAP tests.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest


@pytest.fixture
def schema_server():
    """Start a minimal HTTP server that serves registered JSON schemas.

    Binds to a random free port on localhost. Schemas are registered
    via ``server.register(path, schema_dict)``, which returns the full URL.

    Usage::

        def test_something(schema_server):
            url = schema_server.register("/my.json", {"type": "object", ...})
            # use url in test
    """
    registry: dict[str, bytes] = {}

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            body = registry.get(self.path)
            if body is not None:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            pass  # suppress test output

    server = HTTPServer(("127.0.0.1", 0), _Handler)
    host, port = server.server_address

    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    class _Server:
        base_url = f"http://{host}:{port}"

        def register(self, path: str, schema: dict) -> str:
            """Register schema at path; return its absolute URL."""
            registry[path] = json.dumps(schema).encode()
            return f"{self.base_url}{path}"

    yield _Server()

    server.shutdown()
