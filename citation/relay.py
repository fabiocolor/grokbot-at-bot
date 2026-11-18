#!/usr/bin/env python3
"""Forward a citation from the T3 Code desktop app to the configured webhook."""

import datetime
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import socket
import threading
import time
import urllib.error
import urllib.request


HOST = "127.0.0.1"
PORT = 47811
ORIGIN = "t3code://app"
CONFIG = Path.home() / ".config/grokbot/webhook.env"
MAX_BODY = 128 * 1024
DEDUPE_SECONDS = 120

# A None deadline means the original delivery is still in flight.
_deliveries = {}
_lock = threading.Lock()


def load_config():
    values = {}
    for line in CONFIG.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"\s*(?:export\s+)?(GROKBOT_WEBHOOK_(?:URL|AUTH))\s*=\s*(.*?)\s*", line)
        if match:
            name, value = match.groups()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            values[name] = value

    url = values.get("GROKBOT_WEBHOOK_URL", "")
    auth = values.get("GROKBOT_WEBHOOK_AUTH", "")
    if (not re.fullmatch(r"https://[^/\s]+(?:/\S*)?", url)
            or not auth or auth.startswith("PASTE_")
            or re.search(r"[\x00-\x1f\x7f]", url + auth)):
        raise ValueError("Missing or invalid webhook settings")
    return url, auth


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def forward(payload, url, auth):
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "Authorization": auth},
    )
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=20) as response:
            return response.status
    except urllib.error.HTTPError as error:
        with error:
            return error.code


def required_text(body, field, limit):
    value = body.get(field)
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError("Invalid citation field")
    return value


def citation_payload(body):
    payload = {
        "source": "t3code",
        "kind": "cite",
        "host": socket.gethostname(),
        "projectId": None,
        "projectTitle": None,
        "threadTitle": None,
        "due": None,
        "note": None,
        "sentAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    }
    for field, limit in (("environmentId", 200), ("threadId", 200), ("messageId", 500),
                         ("quote", 20000), ("request", 8000)):
        payload[field] = required_text(body, field, limit)
    if body.get("projectId") is not None:
        payload["projectId"] = required_text(body, "projectId", 200)
    identity = [payload[field] for field in
                ("environmentId", "threadId", "messageId", "quote", "request")]
    for field in ("quoteStart", "quoteEnd"):
        offset = body.get(field)
        if offset is not None and (type(offset) is not int or offset < 0):
            raise ValueError("Invalid citation offset")
        identity.append(offset)
    key = hashlib.sha256(json.dumps(identity).encode()).digest()
    return payload, key


def reserve(key):
    now = time.monotonic()
    with _lock:
        expired = [k for k, (deadline, _) in _deliveries.items()
                   if deadline is not None and deadline <= now]
        for k in expired:
            del _deliveries[k]
        if key in _deliveries:
            return _deliveries[key][1]
        _deliveries[key] = (None, "pending")
        return None


class Handler(BaseHTTPRequestHandler):
    server_version = "t3-bot-cite"

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, *args):
        pass

    def _origin_ok(self):
        return (self.headers.get("Origin") == ORIGIN
                and self.headers.get("Host") == f"{HOST}:{PORT}")

    def _respond(self, status, body=None):
        self.send_response(status)
        if self._origin_ok():
            self.send_header("Access-Control-Allow-Origin", ORIGIN)
            self.send_header("Vary", "Origin")
        if body is None:
            self.send_header("Access-Control-Allow-Methods", "POST")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Private-Network", "true")
            self.end_headers()
            return
        data = json.dumps(body).encode()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _error(self, status, message):
        self._respond(status, {"ok": False, "error": message})

    def do_OPTIONS(self):
        if self.path != "/cite" or not self._origin_ok():
            return self._error(403, "origin not allowed")
        self._respond(204)

    def do_GET(self):
        if self.path == "/health" and self.headers.get("Host") == f"{HOST}:{PORT}":
            return self._respond(200, {"ok": True})
        self._error(404, "not found")

    def do_POST(self):
        if self.path != "/cite":
            return self._error(404, "not found")
        if not self._origin_ok():
            return self._error(403, "origin not allowed")
        if self.headers.get_content_type() != "application/json":
            return self._error(415, "expected JSON")
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= MAX_BODY:
                raise ValueError("Invalid body size")
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                raise ValueError("Expected JSON object")
            payload, key = citation_payload(body)
        except (ValueError, OSError, RecursionError):
            return self._error(400, "invalid citation payload")

        try:
            url, auth = load_config()
        except (OSError, ValueError):
            return self._error(503, "check the local Grok Bot webhook configuration")

        previous = reserve(key)
        if previous == "sent":
            return self._respond(200, {"ok": True, "duplicate": True})
        if previous == "pending":
            return self._error(409, "this citation is already being sent")
        if previous == "uncertain":
            return self._error(409, "delivery uncertain; check the bot before retrying")

        try:
            status = forward(payload, url, auth)
        except (OSError, ValueError):
            with _lock:
                _deliveries[key] = (time.monotonic() + DEDUPE_SECONDS, "uncertain")
            return self._error(502, "delivery uncertain; check the bot before retrying")
        if 200 <= status < 300:
            with _lock:
                _deliveries[key] = (time.monotonic() + DEDUPE_SECONDS, "sent")
            return self._respond(200, {"ok": True})
        with _lock:
            del _deliveries[key]
        self._error(502, f"webhook returned HTTP {status}")


class Server(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        # Request and transport exceptions can include private URLs or headers.
        pass


if __name__ == "__main__":
    with Server((HOST, PORT), Handler) as server:
        print(f"T3 citation relay listening on {HOST}:{PORT}", flush=True)
        server.serve_forever()
