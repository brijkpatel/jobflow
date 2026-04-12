from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread


def health_payload() -> dict[str, str]:
    return {"status": "ok"}


class HealthServer:
    def __init__(self, host: str, port: int, *, mcp_tool=None) -> None:
        _HealthHandler.mcp_tool = mcp_tool
        self._server = ThreadingHTTPServer((host, port), _HealthHandler)
        self._thread = Thread(target=self._server.serve_forever, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()


class _HealthHandler(BaseHTTPRequestHandler):
    mcp_tool = None

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/health":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = json.dumps(health_payload()).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/mcp" or self.mcp_tool is None:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = self.rfile.read(int(self.headers.get("Content-Length", "0") or "0"))
        request = json.loads(body.decode("utf-8"))
        response = _handle_jsonrpc(self.mcp_tool, request)
        payload = json.dumps(response).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def _handle_jsonrpc(mcp_tool, request: dict) -> dict:
    method = request.get("method")
    request_id = request.get("id")
    if method == "tools/list":
        result = {
            "tools": [
                {
                    "name": mcp_tool.name,
                    "description": mcp_tool.description,
                    "inputSchema": mcp_tool.input_schema,
                }
            ]
        }
    elif method == "tools/call":
        params = request.get("params", {})
        if params.get("name") != mcp_tool.name:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32602, "message": "unknown tool"},
            }
        arguments = params.get("arguments", {})
        try:
            tool_result = asyncio.run(mcp_tool.handle(**arguments))
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32000, "message": str(exc)},
            }
        result = {"content": [{"type": "json", "json": tool_result}]}
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": "method not found"},
        }
    return {"jsonrpc": "2.0", "id": request_id, "result": result}
