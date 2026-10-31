"""Automated end-to-end HTTP endpoint tests using Python standard library."""

import json
import threading
import time
import urllib.request
import urllib.error
import pytest
from http.server import HTTPServer
from web.server import CompilerHandler


@pytest.fixture(scope="module")
def server_url():
    """Starts a live instance of CompilerHandler on a random/free port in a background thread."""
    server = HTTPServer(("127.0.0.1", 0), CompilerHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.1)
    url = f"http://127.0.0.1:{port}"
    yield url
    server.shutdown()
    server.server_close()


def test_get_samples_endpoint(server_url):
    req = urllib.request.Request(f"{server_url}/api/samples", method="GET")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert isinstance(data, dict)
        assert "01_arithmetic.c" in data
        assert "02_if_else.c" in data
        assert "03_while_loop.c" in data
        assert "04_boolean_short_circuit.c" in data
        assert "int c = a + b" in data["01_arithmetic.c"] or "c = a +" in data["01_arithmetic.c"]


def test_post_compile_valid_arithmetic(server_url):
    payload = json.dumps({"source": "int a = 10; int b; b = a + 5;"}).encode("utf-8")
    req = urllib.request.Request(
        f"{server_url}/api/compile",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode("utf-8"))
        assert res["success"] is True
        assert len(res["tac_quadruples"]) > 0
        assert res["tac_quadruples"][-1]["op"] == "halt"
        assert len(res["tokens"]) > 0
        assert res["symbol_table"] == {"a": "int", "b": "int"}


def test_post_compile_if_else(server_url):
    payload = json.dumps({"source": "int x = 1; if (x > 0) { x = 2; } else { x = 3; }"}).encode("utf-8")
    req = urllib.request.Request(
        f"{server_url}/api/compile",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode("utf-8"))
        assert res["success"] is True
        assert len(res["backpatch_trace"]) > 0


def test_post_compile_while_loop(server_url):
    payload = json.dumps({"source": "int i = 0; while (i < 5) { i = i + 1; }"}).encode("utf-8")
    req = urllib.request.Request(
        f"{server_url}/api/compile",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode("utf-8"))
        assert res["success"] is True
        assert len(res["tac_quadruples"]) == 7


def test_post_compile_boolean_short_circuit(server_url):
    payload = json.dumps({"source": "int a = 1; int b = 2; if (a < 5 || b > 1) { a = 0; }"}).encode("utf-8")
    req = urllib.request.Request(
        f"{server_url}/api/compile",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode("utf-8"))
        assert res["success"] is True


def test_post_compile_empty_request_body(server_url):
    req = urllib.request.Request(
        f"{server_url}/api/compile",
        data=b"",
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        urllib.request.urlopen(req)
        assert False, "Expected HTTP 400"
    except urllib.error.HTTPError as err:
        assert err.code == 400
        data = json.loads(err.read().decode("utf-8"))
        assert data["success"] is False
        assert data["error"]["type"] == "RequestError"


def test_post_compile_malformed_json(server_url):
    req = urllib.request.Request(
        f"{server_url}/api/compile",
        data=b"not a json",
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        urllib.request.urlopen(req)
        assert False, "Expected HTTP 400"
    except urllib.error.HTTPError as err:
        assert err.code == 400
        data = json.loads(err.read().decode("utf-8"))
        assert data["success"] is False
        assert data["error"]["type"] == "JSONError"


def test_post_compile_compiler_errors(server_url):
    # Lexer error
    payload_lex = json.dumps({"source": "int a = @;"}).encode("utf-8")
    req_lex = urllib.request.Request(f"{server_url}/api/compile", data=payload_lex, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req_lex) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode("utf-8"))
        assert res["success"] is False
        assert res["error"]["type"] == "LexerError"

    # Parser error
    payload_parse = json.dumps({"source": "int a = ;"}).encode("utf-8")
    req_parse = urllib.request.Request(f"{server_url}/api/compile", data=payload_parse, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req_parse) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode("utf-8"))
        assert res["success"] is False
        assert res["error"]["type"] == "ParserError"

    # Semantic error
    payload_sem = json.dumps({"source": "a = 10;"}).encode("utf-8")
    req_sem = urllib.request.Request(f"{server_url}/api/compile", data=payload_sem, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req_sem) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode("utf-8"))
        assert res["success"] is False
        assert res["error"]["type"] == "SemanticError"

