"""AegisLoop 安全场景 mock 工具：按场景剧本返回仿真数据。

与 opspilot-zero-demo 的 mock 思路一致：剧本 JSON 即"系统"，
工具函数按查询参数过滤数据源事件。所有调用记录进 trace，供可观测验收。
Case 状态机覆盖完整主链（研判→处置→收尾），见 update_case_status。
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_DIR = PROJECT_ROOT / "scenarios"


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def list_scenarios() -> List[str]:
    return sorted(path.stem for path in SCENARIO_DIR.glob("*.json"))


def load_scenario(scenario_id: str) -> Dict[str, Any]:
    path = SCENARIO_DIR / f"{scenario_id}.json"
    if not path.exists():
        available = ", ".join(list_scenarios())
        raise ValueError(f"Unknown scenario '{scenario_id}'. Available: {available}")
    return load_json(path)


def compact(value: Any, max_len: int = 240) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return text if len(text) <= max_len else text[: max_len - 3] + "..."


def _match(actual: Any, expect: Any) -> bool:
    """精确匹配优先，其次子串匹配（方便 Agent 用 IP 段/账号名模糊查询）。"""
    if expect is None:
        return True
    if isinstance(expect, list):
        return any(_match(actual, item) for item in expect)
    a = str(actual).lower()
    e = str(expect).lower()
    return a == e or e in a


def _in_window(ts: str, since: Optional[str], until: Optional[str]) -> bool:
    if since and ts and ts < since:
        return False
    if until and ts and ts > until:
        return False
    return True


class SecurityMockTools:
    """安全场景 mock 工具集：读取剧本，按查询参数过滤数据源。"""

    def __init__(self, scenario_id: str) -> None:
        self.scenario_id = scenario_id
        self.scenario = load_scenario(scenario_id)
        self.trace: List[Dict[str, Any]] = []
        self.actions: List[Dict[str, Any]] = []
        self.receipts: Dict[str, Any] = {}
        self.tel_chain: List[Dict[str, Any]] = []
        self.lessons: Dict[str, Any] = {}
        self.cases: Dict[str, Any] = {}
        self.containment_actions: List[Dict[str, Any]] = []
        self._enrich_host_ips()

    def _enrich_host_ips(self) -> None:
        """给缺少 ip 的事件补上主机 IP，使 Agent 既可按主机名也可按 IP 查询。"""
        host_ips = {
            host["name"]: host["ip"]
            for host in self.scenario.get("entities", {}).get("hosts", [])
        }
        for source in self.scenario.get("data_sources", {}).values():
            for ev in source:
                host = ev.get("host")
                if host and "ip" not in ev and host in host_ips:
                    ev["ip"] = host_ips[host]

    # ---------- 基础设施 ----------
    def _record(self, tool: str, fn: str, args: Dict[str, Any], result: Any) -> Any:
        self.trace.append(
            {
                "time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "tool": tool,
                "function": fn,
                "args": args,
                "result_preview": compact(result),
            }
        )
        return result

    def _source(self, name: str) -> List[Dict[str, Any]]:
        return self.scenario.get("data_sources", {}).get(name, [])

    def _filter(
        self,
        events: Iterable[Dict[str, Any]],
        since: Optional[str] = None,
        until: Optional[str] = None,
        **kw: Any,
    ) -> List[Dict[str, Any]]:
        out = []
        for ev in events:
            if not _in_window(str(ev.get("time", "")), since, until):
                continue
            matched = True
            for k, v in kw.items():
                if k == "host":
                    if not (_match(ev.get("host"), v) or _match(ev.get("ip"), v)):
                        matched = False
                        break
                elif not _match(ev.get(k), v):
                    matched = False
                    break
            if matched:
                out.append(ev)
        return out

    def reset(self) -> None:
        self.trace.clear()
        self.actions.clear()
        self.receipts.clear()
        self.tel_chain.clear()
        self.lessons.clear()
        self.cases.clear()
        self.containment_actions.clear()
        if hasattr(self, "case_status"):
            delattr(self, "case_status")

    # ---------- mock_siem ----------
    def list_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        events = [e for e in self._source("siem") if not e.get("benign")]
        result = self._filter(events, severity=severity)
        return self._record("mock_siem", "list_alerts", {"severity": severity}, result)

    def get_seed_signal(self) -> Dict[str, Any]:
        return self._record("mock_siem", "get_seed_signal", {}, self.scenario["seed_signal"])

    def search_events(
        self,
        event_id: Optional[int] = None,
        host: Optional[str] = None,
        user: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        result = self._filter(
            self._source("siem"),
            since=since,
            until=until,
            event_id=event_id,
            host=host,
            user=user,
        )
        return self._record(
            "mock_siem",
            "search_events",
            {"event_id": event_id, "host": host, "user": user, "since": since, "until": until},
            result,
        )

    # ---------- mock_edr ----------
    def process_tree(self, host: Optional[str] = None, since: Optional[str] = None, until: Optional[str] = None) -> List[Dict[str, Any]]:
        result = self._filter(self._source("edr"), since=since, until=until, event=1, host=host)
        return self._record("mock_edr", "process_tree", {"host": host, "since": since, "until": until}, result)

    def process_access(self, target: Optional[str] = None, host: Optional[str] = None) -> List[Dict[str, Any]]:
        result = self._filter(self._source("edr"), event=10, target_image=target, host=host)
        return self._record("mock_edr", "process_access", {"target": target, "host": host}, result)

    def network_connections(self, host: Optional[str] = None, since: Optional[str] = None, until: Optional[str] = None) -> List[Dict[str, Any]]:
        result = self._filter(self._source("edr"), since=since, until=until, event=3, host=host)
        return self._record("mock_edr", "network_connections", {"host": host, "since": since, "until": until}, result)

    def file_events(self, host: Optional[str] = None) -> List[Dict[str, Any]]:
        result = self._filter(self._source("edr"), event=11, host=host)
        return self._record("mock_edr", "file_events", {"host": host}, result)

    # ---------- mock_ndr ----------
    def flows(
        self,
        src: Optional[str] = None,
        dst: Optional[str] = None,
        port: Optional[int] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        result = self._filter(
            self._source("ndr"),
            since=since,
            until=until,
            src=src,
            dst=dst,
            port=port,
        )
        return self._record("mock_ndr", "flows", {"src": src, "dst": dst, "port": port, "since": since, "until": until}, result)

    # ---------- mock_ad ----------
    def auth_log(self, user: Optional[str] = None, ip: Optional[str] = None, since: Optional[str] = None, until: Optional[str] = None) -> List[Dict[str, Any]]:
        result = self._filter(self._source("ad"), since=since, until=until, user=user, src_ip=ip)
        return self._record("mock_ad", "auth_log", {"user": user, "ip": ip, "since": since, "until": until}, result)

    def account_info(self, account: Optional[str] = None) -> List[Dict[str, Any]]:
        users = self.scenario.get("entities", {}).get("users", [])
        result = self._filter(users, account=account)
        return self._record("mock_ad", "account_info", {"account": account}, result)

    # ---------- mock_dbaudit ----------
    def query_log(self, user: Optional[str] = None, table: Optional[str] = None, since: Optional[str] = None, until: Optional[str] = None) -> List[Dict[str, Any]]:
        result = self._filter(self._source("dbaudit"), since=since, until=until, user=user, table=table)
        return self._record("mock_dbaudit", "query_log", {"user": user, "table": table, "since": since, "until": until}, result)

    def baseline(self, user: Optional[str] = None, table: Optional[str] = None) -> List[Dict[str, Any]]:
        baselines = self.scenario.get("baselines", [])
        result = self._filter(baselines, user=user, table=table)
        return self._record("mock_dbaudit", "baseline", {"user": user, "table": table}, result)

    # ---------- mock_intel ----------
    def lookup(self, value: Optional[str] = None) -> List[Dict[str, Any]]:
        result = self._filter(self._source("intel"), value=value)
        return self._record("mock_intel", "lookup", {"value": value}, result)

    def stealer_log(self, account: Optional[str] = None) -> List[Dict[str, Any]]:
        result = self._filter(self._source("intel"), kind="stealer_log", value=account)
        return self._record("mock_intel", "stealer_log", {"account": account}, result)

    def search_actor_profile(self, query: Any = None, top_k: int = 5) -> Dict[str, Any]:
        lesson_path = PROJECT_ROOT / "knowledge" / "lessons" / "LESSON-2001.json"
        hits: List[Dict[str, Any]] = []
        if lesson_path.exists():
            lesson = load_json(lesson_path)
            hits.append(
                {
                    "lesson_id": lesson.get("lesson_id", "LESSON-2001"),
                    "path": str(lesson_path.relative_to(PROJECT_ROOT)).replace(chr(92), "/"),
                    "score": 0.86,
                    "trigger_features": lesson.get("trigger_features", {}),
                    "query": query,
                }
            )
            hits = hits[: max(1, int(top_k or 5))]
        result = {"hits": hits, "top_k": top_k}
        return self._record("mock_intel", "search_actor_profile", {"query": query, "top_k": top_k}, result)

    def upsert_profile_index(self, lesson_id: Optional[str] = None, features: Any = None) -> Dict[str, Any]:
        result = {"indexed": True, "index_version": "v1", "lesson_id": lesson_id, "features": features}
        return self._record(
            "mock_intel",
            "upsert_profile_index",
            {"lesson_id": lesson_id, "features": features},
            result,
        )

    # ---------- mock_evidence ----------
    def snapshot(self, refs: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        events = self._source("evidence")
        if refs:
            events = [e for e in events if any(_match(e.get("ref"), r) for r in refs)]
        result = self._record("mock_evidence", "snapshot", {"refs": refs}, events)
        receipt_id = f"rcpt-evidence-snapshot-{len(self.receipts)+1:04d}"
        self.receipts[receipt_id] = {
            "receipt_id": receipt_id,
            "tool": "mock_evidence",
            "function": "snapshot",
            "refs": refs,
            "events": events,
        }
        return result

    def get_receipt(self, receipt_id: Optional[str] = None) -> Dict[str, Any]:
        rid = str(receipt_id or "")
        if rid in self.receipts:
            return self._record("mock_evidence", "get_receipt", {"receipt_id": rid}, self.receipts[rid])
        for entry in reversed(self.trace):
            preview = str(entry.get("result_preview", ""))
            args = compact(entry.get("args", {}))
            if rid and (rid in preview or rid in args):
                fabricated = {
                    "receipt_id": rid,
                    "fabricated": True,
                    "from_trace": {
                        "tool": entry.get("tool"),
                        "function": entry.get("function"),
                        "args": entry.get("args"),
                        "result_preview": entry.get("result_preview"),
                    },
                }
                self.receipts[rid] = fabricated
                return self._record("mock_evidence", "get_receipt", {"receipt_id": rid}, fabricated)
        result = {"receipt_id": rid, "error": "receipt not found"}
        return self._record("mock_evidence", "get_receipt", {"receipt_id": rid}, result)

    def seal_tel_entry(
        self,
        case_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        payload_ref: Optional[str] = None,
    ) -> Dict[str, Any]:
        prev_hash = self.tel_chain[-1]["hash"] if self.tel_chain else ("0" * 64)
        body = {
            "case_id": case_id,
            "trace_id": trace_id,
            "payload_ref": payload_ref,
            "prev_hash": prev_hash,
            "seq": len(self.tel_chain) + 1,
        }
        digest = hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
        tel_entry_id = f"tel-{case_id or 'CASE'}-{len(self.tel_chain)+1:04d}"
        entry = {**body, "tel_entry_id": tel_entry_id, "hash": digest}
        self.tel_chain.append(entry)
        result = {"tel_entry_id": tel_entry_id, "prev_hash": prev_hash, "hash": digest}
        return self._record(
            "mock_evidence",
            "seal_tel_entry",
            {"case_id": case_id, "trace_id": trace_id, "payload_ref": payload_ref},
            result,
        )

    def export_tel_pack(self, case_id: Optional[str] = None) -> Dict[str, Any]:
        entries = [e for e in self.tel_chain if not case_id or e.get("case_id") == case_id]
        root_hash = entries[-1]["hash"] if entries else ("0" * 64)
        pack_uri = f"evidence/{case_id or 'CASE'}-tel.json"
        result = {"pack_uri": pack_uri, "root_hash": root_hash, "entry_count": len(entries)}
        return self._record("mock_evidence", "export_tel_pack", {"case_id": case_id}, result)

    # ---------- mock_ticket ----------
    def create_case(self, seed: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.case_status = "NEW"
        case = {
            "case_id": self.scenario["incident_id"],
            "title": self.scenario["title"],
            "seed_signal": seed or self.scenario["seed_signal"],
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "status": self.case_status,
        }
        self.cases[case["case_id"]] = case
        self.actions.append({"action": "create_case", "case": case})
        return self._record("mock_ticket", "create_case", {"seed": seed}, case)

    def get_case(self, case_id: Optional[str] = None) -> Dict[str, Any]:
        case = {
            "case_id": self.scenario["incident_id"],
            "title": self.scenario["title"],
            "status": getattr(self, "case_status", "NEW"),
        }
        if case_id and str(case_id) != self.scenario["incident_id"]:
            return self._record("mock_ticket", "get_case", {"case_id": case_id}, {"error": "case not found"})
        return self._record("mock_ticket", "get_case", {"case_id": case_id}, case)

    def update_case_status(
        self,
        case_id: Optional[str] = None,
        to: Optional[str] = None,
        by: Optional[str] = None,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """A 线案件状态机：只允许按契约迁移，非法迁移直接拒绝。"""
        case_id = case_id or self.scenario["incident_id"]
        if case_id and str(case_id) != self.scenario["incident_id"]:
            return self._record(
                "mock_ticket", "update_case_status", {"case_id": case_id, "to": to, "by": by},
                {"allowed": False, "error": "case not found"},
            )
        current = getattr(self, "case_status", "NEW")
        # Keep in sync with contracts/ALIGNMENT.md §5.
        allowed = {
            "NEW": ["TRIAGED", "ESCALATED", "ABANDONED"],
            "TRIAGED": ["INVESTIGATING", "ESCALATED", "ABANDONED"],
            "INVESTIGATING": ["VERDICT_PENDING", "DEGRADED", "ESCALATED", "ABANDONED"],
            "VERDICT_PENDING": ["PLANNED", "ESCALATED", "DEGRADED", "ABANDONED"],
            "PLANNED": ["AWAITING_APPROVAL", "EXECUTING", "ESCALATED", "ABANDONED"],
            "AWAITING_APPROVAL": ["EXECUTING", "PLANNED", "ESCALATED", "ABANDONED"],
            "EXECUTING": ["VERIFYING", "DEGRADED", "ESCALATED", "ABANDONED"],
            "VERIFYING": ["SETTLE", "EXECUTING", "ESCALATED", "ABANDONED"],
            "SETTLE": ["CLOSED", "ESCALATED"],
            "CLOSED": [],
            "ESCALATED": ["INVESTIGATING", "ABANDONED", "CLOSED"],
            "DEGRADED": ["INVESTIGATING", "VERIFYING", "ESCALATED", "ABANDONED"],
            "ABANDONED": [],
        }
        if not to or to not in allowed.get(current, []):
            return self._record(
                "mock_ticket", "update_case_status", {"case_id": case_id, "to": to, "by": by},
                {"allowed": False, "error": f"非法状态迁移 {current} -> {to}", "current": current},
            )
        self.case_status = to
        if case_id in self.cases:
            self.cases[case_id]["status"] = to
        transition = {
            "case_id": case_id,
            "from": current,
            "to": to,
            "by": by,
            "note": note,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        self.actions.append({"action": "update_case_status", "transition": transition})
        return self._record(
            "mock_ticket", "update_case_status", {"case_id": case_id, "to": to, "by": by, "note": note},
            {"allowed": True, "transition": transition, "status": to},
        )


    # ---------- mock_probe ----------
    def _host_isolated(self, host: str) -> bool:
        for action in self.containment_actions:
            if action.get("type") == "isolate_host" and _match(action.get("target"), host):
                return True
        return False

    def _account_disabled(self, account: str) -> bool:
        for action in self.containment_actions:
            if action.get("type") == "disable_account" and _match(action.get("target"), account):
                return True
        return False

    def check_host(self, host: Optional[str] = None, checks: Any = None) -> Dict[str, Any]:
        host = host or ""
        receipt_id = f"rcpt-probe-host-{abs(hash(host)) % 10_000_000:07d}"
        findings: List[Dict[str, Any]] = []
        hl = host.lower()
        if ("finance" in hl or "report" in hl) and not self._host_isolated(host):
            findings.append(
                {
                    "type": "residual_smb",
                    "severity": "medium",
                    "detail": "Residual SMB session / lateral artifact still observed (demo)",
                    "host": host,
                }
            )
        result = {"ok": True, "findings": findings, "receipt_id": receipt_id, "checks": checks}
        self.receipts[receipt_id] = {
            "receipt_id": receipt_id,
            "tool": "mock_probe",
            "function": "check_host",
            "result": result,
        }
        return self._record("mock_probe", "check_host", {"host": host, "checks": checks}, result)

    def check_account(self, account: Optional[str] = None) -> Dict[str, Any]:
        account = account or ""
        disabled = self._account_disabled(account)
        receipt_id = f"rcpt-probe-account-{abs(hash(account)) % 10_000_000:07d}"
        result = {
            "disabled": disabled,
            "active_sessions": 0 if disabled else 1,
            "receipt_id": receipt_id,
            "account": account,
        }
        self.receipts[receipt_id] = {
            "receipt_id": receipt_id,
            "tool": "mock_probe",
            "function": "check_account",
            "result": result,
        }
        return self._record("mock_probe", "check_account", {"account": account}, result)

    # ---------- mock_knowledge ----------
    def write_lesson(self, lesson: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        lesson = dict(lesson or {})
        lesson_id = lesson.get("lesson_id")
        if not lesson.get("status"):
            lesson["status"] = "proposed"
        path_str = None
        if lesson_id:
            lessons_dir = PROJECT_ROOT / "knowledge" / "lessons"
            lessons_dir.mkdir(parents=True, exist_ok=True)
            out = lessons_dir / f"{lesson_id}.json"
            with out.open("w", encoding="utf-8") as f:
                json.dump(lesson, f, ensure_ascii=False, indent=2)
                f.write("\n")
            path_str = str(out.relative_to(PROJECT_ROOT)).replace(chr(92), "/")
            self.lessons[str(lesson_id)] = lesson
        result = {"path": path_str, "lesson_id": lesson_id, "status": lesson.get("status", "proposed")}
        return self._record("mock_knowledge", "write_lesson", {"lesson": lesson}, result)

    def refresh_rag_index(self, lesson_id: Optional[str] = None) -> Dict[str, Any]:
        lessons_dir = PROJECT_ROOT / "knowledge" / "lessons"
        doc_count = len(list(lessons_dir.glob("LESSON-*.json"))) if lessons_dir.exists() else 0
        if lesson_id and lesson_id in self.lessons and doc_count == 0:
            doc_count = len(self.lessons)
        result = {"ok": True, "doc_count": doc_count, "lesson_id": lesson_id}
        return self._record("mock_knowledge", "refresh_rag_index", {"lesson_id": lesson_id}, result)

    def get_lesson(self, lesson_id: Optional[str] = None) -> Dict[str, Any]:
        lid = str(lesson_id or "")
        if lid in self.lessons:
            return self._record("mock_knowledge", "get_lesson", {"lesson_id": lid}, self.lessons[lid])
        lesson_file = PROJECT_ROOT / "knowledge" / "lessons" / f"{lid}.json"
        if lesson_file.exists():
            lesson = load_json(lesson_file)
            self.lessons[lid] = lesson
            return self._record("mock_knowledge", "get_lesson", {"lesson_id": lid}, lesson)
        result = {"error": "lesson not found", "lesson_id": lid}
        return self._record("mock_knowledge", "get_lesson", {"lesson_id": lid}, result)

    # ---------- mock_contain ----------
    def _contain(self, action_type: str, target: str, via: str, status: str) -> Dict[str, Any]:
        receipt_id = f"rcpt-contain-{action_type}-{abs(hash(target)) % 10_000_000:07d}"
        action = {
            "type": action_type,
            "target": target,
            "via": via,
            "status": status,
            "receipt_id": receipt_id,
        }
        self.containment_actions.append(action)
        result = {"ok": True, "via": via, "status": status, "receipt_id": receipt_id}
        self.receipts[receipt_id] = {
            "receipt_id": receipt_id,
            "tool": "mock_contain",
            "function": action_type,
            "result": result,
        }
        return result

    def isolate_host(self, host: Optional[str] = None, simulate_timeout: bool = False) -> Dict[str, Any]:
        host = host or ""
        if simulate_timeout:
            result = {"ok": False, "code": 504, "msg": "EDR timeout", "via": "EDR"}
            return self._record(
                "mock_contain",
                "isolate_host",
                {"host": host, "simulate_timeout": True},
                result,
            )
        result = self._contain("isolate_host", host, "EDR", "isolated(Mock)")
        return self._record(
            "mock_contain",
            "isolate_host",
            {"host": host, "simulate_timeout": False},
            result,
        )

    def block_ip(self, ip: Optional[str] = None) -> Dict[str, Any]:
        ip = ip or ""
        result = self._contain("block_ip", ip, "WAF", "blocked(Mock)")
        return self._record("mock_contain", "block_ip", {"ip": ip}, result)

    def block_domain(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """L3 suggest_only：只记建议，不写真实封禁语义。"""
        domain = domain or ""
        result = {
            "ok": True,
            "suggested_only": True,
            "action": "block_domain",
            "domain": domain,
            "status": "suggested_only",
            "note": "L3 suggest_only — recorded as suggestion, not executed",
        }
        self.actions.append({"action": "block_domain", "result": result})
        return self._record("mock_contain", "block_domain", {"domain": domain}, result)

    def disable_account(self, account: Optional[str] = None) -> Dict[str, Any]:
        account = account or ""
        result = self._contain("disable_account", account, "AD", "disabled(Mock)")
        return self._record("mock_contain", "disable_account", {"account": account}, result)

    # ---------- mock_ticket extras ----------
    def create_followup(
        self,
        case_id: Optional[str] = None,
        reason: Optional[str] = None,
        severity: str = "P2",
    ) -> Dict[str, Any]:
        ticket_id = f"TICKET-FU-{case_id or 'CASE'}-{len(self.actions)+1:04d}"
        ticket = {
            "ticket_id": ticket_id,
            "case_id": case_id,
            "reason": reason,
            "severity": severity or "P2",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "status": "OPEN",
        }
        self.actions.append({"action": "create_followup", "ticket": ticket})
        return self._record(
            "mock_ticket",
            "create_followup",
            {"case_id": case_id, "reason": reason, "severity": severity},
            ticket,
        )

    # ---------- mock_udb（UDB 数据清洗） ----------
    def sanitize(self, fields: Optional[Dict[str, Any]] = None, object: Any = None, **kwargs: Any) -> Dict[str, Any]:
        """清洗外部字段。标准键 fields；兼容别名 object（ALIGNMENT §7）。"""
        if fields is None and object is not None:
            fields = object if isinstance(object, dict) else {"payload": object}
        if fields is None and "object" in kwargs:
            obj = kwargs["object"]
            fields = obj if isinstance(obj, dict) else {"payload": obj}
        fields = fields or {}
        injection_markers = [
            "ignore previous instructions",
            "ignore all previous",
            "忽略以上",
            "忽略之前",
            "system prompt",
            "admin says",
            "你是管理员",
            "disregard",
            "reveal your",
            "打印你的系统提示词",
        ]
        clean: Dict[str, Any] = {}
        injected_fields: List[str] = []
        for key, value in fields.items():
            text = str(value).lower()
            if any(marker in text for marker in injection_markers):
                injected_fields.append(key)
            else:
                clean[key] = value
        injected = len(injected_fields) > 0
        return self._record(
            "mock_udb",
            "sanitize",
            {"fields": fields},
            {
                "clean_fields": clean,
                "injected": injected,
                "injected_fields": injected_fields,
                "threat_level": "high" if injected else "low",
                "notes": ["注入字段已隔离，仅存引用不进入上下文"] if injected else [],
            },
        )
