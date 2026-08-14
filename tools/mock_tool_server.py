"""AegisLoop 安全场景 HTTP mock 工具网关。

用法：
    python mock_tool_server.py --host 0.0.0.0 --port 18089
路由：
    GET  /health
    GET  /scenarios
    GET  /tools/{scenario_id}/trace
    POST /tools/{scenario_id}/{tool}.{function}
    POST /tools/{scenario_id}/reset
"""

from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict
from urllib.parse import unquote, urlparse

from mock_tools import SecurityMockTools, list_scenarios


TOOL_STATES: Dict[str, SecurityMockTools] = {}


def get_state(scenario_id: str) -> SecurityMockTools:
    if scenario_id not in TOOL_STATES:
        TOOL_STATES[scenario_id] = SecurityMockTools(scenario_id)
    return TOOL_STATES[scenario_id]


def reset_state(scenario_id: str) -> Dict[str, Any]:
    TOOL_STATES[scenario_id] = SecurityMockTools(scenario_id)
    return {"scenario_id": scenario_id, "status": "reset"}


def call_tool(tools: SecurityMockTools, name: str, payload: Dict[str, Any]) -> Any:
    handlers: Dict[str, Callable[[], Any]] = {
        "mock_siem.list_alerts": lambda: tools.list_alerts(payload.get("severity")),
        "mock_siem.get_seed_signal": lambda: tools.get_seed_signal(),
        "mock_siem.search_events": lambda: tools.search_events(
            payload.get("event_id"),
            payload.get("host"),
            payload.get("user"),
            payload.get("since"),
            payload.get("until"),
        ),
        "mock_edr.process_tree": lambda: tools.process_tree(payload.get("host"), payload.get("since"), payload.get("until")),
        "mock_edr.process_access": lambda: tools.process_access(payload.get("target"), payload.get("host")),
        "mock_edr.network_connections": lambda: tools.network_connections(payload.get("host"), payload.get("since"), payload.get("until")),
        "mock_edr.file_events": lambda: tools.file_events(payload.get("host")),
        "mock_ndr.flows": lambda: tools.flows(
            payload.get("src"),
            payload.get("dst"),
            payload.get("port"),
            payload.get("since"),
            payload.get("until"),
        ),
        "mock_ad.auth_log": lambda: tools.auth_log(payload.get("user"), payload.get("ip"), payload.get("since"), payload.get("until")),
        "mock_ad.account_info": lambda: tools.account_info(payload.get("account")),
        "mock_dbaudit.query_log": lambda: tools.query_log(payload.get("user"), payload.get("table"), payload.get("since"), payload.get("until")),
        "mock_dbaudit.baseline": lambda: tools.baseline(payload.get("user"), payload.get("table")),
        "mock_intel.lookup": lambda: tools.lookup(payload.get("value")),
        "mock_intel.stealer_log": lambda: tools.stealer_log(payload.get("account")),
        "mock_intel.search_actor_profile": lambda: tools.search_actor_profile(
            payload.get("query"), payload.get("top_k", 5)
        ),
        "mock_intel.upsert_profile_index": lambda: tools.upsert_profile_index(
            payload.get("lesson_id"), payload.get("features")
        ),
        "mock_evidence.snapshot": lambda: tools.snapshot(payload.get("refs")),
        "mock_evidence.get_receipt": lambda: tools.get_receipt(payload.get("receipt_id")),
        "mock_evidence.seal_tel_entry": lambda: tools.seal_tel_entry(
            payload.get("case_id"),
            payload.get("trace_id"),
            payload.get("payload_ref"),
        ),
        "mock_evidence.export_tel_pack": lambda: tools.export_tel_pack(payload.get("case_id")),
        "mock_probe.check_host": lambda: tools.check_host(payload.get("host"), payload.get("checks")),
        "mock_probe.check_account": lambda: tools.check_account(payload.get("account")),
        "mock_knowledge.write_lesson": lambda: tools.write_lesson(payload.get("lesson")),
        "mock_knowledge.refresh_rag_index": lambda: tools.refresh_rag_index(payload.get("lesson_id")),
        "mock_knowledge.get_lesson": lambda: tools.get_lesson(payload.get("lesson_id")),
        "mock_contain.isolate_host": lambda: tools.isolate_host(
            payload.get("host"), bool(payload.get("simulate_timeout", False))
        ),
        "mock_contain.block_ip": lambda: tools.block_ip(payload.get("ip")),
        "mock_contain.block_domain": lambda: tools.block_domain(payload.get("domain")),
        "mock_contain.disable_account": lambda: tools.disable_account(payload.get("account")),
        "mock_ticket.create_case": lambda: tools.create_case(payload.get("seed")),
        "mock_ticket.get_case": lambda: tools.get_case(payload.get("case_id")),
        "mock_ticket.update_case_status": lambda: tools.update_case_status(
            payload.get("case_id"),
            payload.get("to"),
            payload.get("by"),
            payload.get("note"),
        ),
        "mock_ticket.create_followup": lambda: tools.create_followup(
            payload.get("case_id"),
            payload.get("reason"),
            payload.get("severity", "P2"),
        ),
        "mock_udb.sanitize": lambda: tools.sanitize(
            fields=payload.get("fields"),
            object=payload.get("object"),
        ),
    }
    if name not in handlers:
        available = ", ".join(sorted(handlers))
        raise ValueError(f"unknown tool call '{name}', available: {available}")
    return handlers[name]()


class MockToolHandler(BaseHTTPRequestHandler):
    server_version = "AegisLoopMockToolGateway/0.1"

    def _send(self, status: HTTPStatus, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> Dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw.strip() else {}

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        parts = [unquote(part) for part in parsed.path.strip("/").split("/") if part]
        try:
            if parts == ["health"]:
                self._send(HTTPStatus.OK, {"ok": True, "service": "aegisloop-mock-tool-gateway"})
                return
            if parts == ["scenarios"]:
                self._send(HTTPStatus.OK, {"ok": True, "result": list_scenarios()})
                return
            if len(parts) == 3 and parts[0] == "tools" and parts[2] == "trace":
                tools = get_state(parts[1])
                self._send(HTTPStatus.OK, {"ok": True, "result": tools.trace})
                return
            self._send(HTTPStatus.NOT_FOUND, {"ok": False, "error": "unknown endpoint"})
        except Exception as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        parts = [unquote(part) for part in parsed.path.strip("/").split("/") if part]
        try:
            if len(parts) != 3 or parts[0] != "tools":
                self._send(HTTPStatus.NOT_FOUND, {"ok": False, "error": "expected /tools/{scenario_id}/{tool_call}"})
                return
            scenario_id, tool_call = parts[1], parts[2]
            payload = self._read_json()
            if tool_call == "reset":
                result = reset_state(scenario_id)
            else:
                result = call_tool(get_state(scenario_id), tool_call, payload)
            self._send(HTTPStatus.OK, {"ok": True, "result": result})
        except Exception as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"{self.address_string()} - {fmt % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AegisLoop security mock tool gateway.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=18089, type=int)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), MockToolHandler)
    print(f"AegisLoop mock tool gateway listening on http://{args.host}:{args.port}")
    print("Health: GET /health")
    print("Tool call: POST /tools/{scenario_id}/{tool}.{function}")
    server.serve_forever()


if __name__ == "__main__":
    main()
