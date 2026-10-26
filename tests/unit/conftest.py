import json
import socketserver
import threading
import http.server

import pytest


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("content-length", 0))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        self.server.hits.append(body)
        out = json.dumps(self.server.reply).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *args):  # keep test output quiet
        pass


@pytest.fixture
def mock_llm():
    """A local OpenAI-style endpoint. ``srv.reply`` is the JSON it returns; ``srv.hits`` the bodies received."""
    srv = socketserver.TCPServer(("127.0.0.1", 0), _Handler)
    srv.hits = []
    srv.reply = {"choices": [{"message": {"content": "all good"}}]}
    srv.url = f"http://127.0.0.1:{srv.server_address[1]}/v1/chat"
    srv.host = f"127.0.0.1:{srv.server_address[1]}"
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield srv
    srv.shutdown()
    srv.server_close()


@pytest.fixture
def backstop(mock_llm):
    """Install only the HTTP backstop (fresh stats) for a provider pointing at ``mock_llm``."""
    import anchor.runtime as rt
    from anchor.runtime.interceptors import http_backstop as hb
    from anchor.runtime.interceptors.base import InterceptorMode, SessionStats

    rt.deactivate()  # importing anchor.runtime auto-activates; start from a known state
    rt.register_provider(mock_llm.host, "mockllm")

    def install(mode="block"):
        hb.deactivate_backstop()
        stats = SessionStats()
        assert hb.activate_backstop(InterceptorMode(mode), stats)
        return stats

    yield install
    hb.deactivate_backstop()
