"""Lightweight HTTP server using Python standard library."""

import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

# Ensure compiler package is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from compiler.driver import compile_source

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "samples")


class CompilerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_POST(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/api/compile":
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": {"type": "RequestError", "message": "Empty request body", "line": 0, "column": 0}}).encode("utf-8"))
                return

            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body)
                source_code = data.get("source", "")
                result = compile_source(source_code)
                # If compilation failed with syntax/semantic error, return 200 with success=False payload
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode("utf-8"))
            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": {"type": "JSONError", "message": "Invalid JSON payload", "line": 0, "column": 0}}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": {"type": "ServerError", "message": str(e), "line": 0, "column": 0}}).encode("utf-8"))
        else:
            self.send_error(404, "Endpoint not found")

    def do_GET(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/api/samples":
            samples = {}
            if os.path.exists(SAMPLES_DIR):
                for fname in sorted(os.listdir(SAMPLES_DIR)):
                    if fname.endswith(".c"):
                        with open(os.path.join(SAMPLES_DIR, fname), "r", encoding="utf-8") as f:
                            samples[fname] = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(samples).encode("utf-8"))
        else:
            super().do_GET()


def run_server(port: int = 8000):
    server_address = ("", port)
    httpd = HTTPServer(server_address, CompilerHandler)
    print(f"ThreeAddrGen Compiler Laboratory running at http://localhost:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
