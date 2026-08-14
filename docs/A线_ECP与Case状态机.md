# A 线接口契约 · ECP 字段与 Case 状态机

> **合仓对齐**：verdict 必须含 `root_cause` / `claim_ref`（及 `claim` / `grade`）；Case 状态只推进到 `VERDICT_PENDING`（不得直接 `PLANNED`）。详见 [`contracts/ALIGNMENT.md`](../contracts/ALIGNMENT.md) §5–§6.1。

- 版本：v0.2（合仓对齐）
- 适用范围：A 线四个 Agent（分诊 / 取证 / 关联 / 裁决）
- 关联文件：`tools/tool_catalog.json`、`scenarios/lateral_movement_t1021.json`、`schemas/dict_table1.json`

## 1. ECP 字段定义（A 线输出统一格式）

Agent 之间传递结论一律使用 ECP 结构化格式，不传自然语言摘要、不复制大取证物原文：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `claim` | string | 是 | 一句话结论 |
| `confidence` | number (0-1) | 是 | 置信度 |
| `evidence` | array[{id, strength, ref}] | 是 | 证据引用（指向证据库/事件 ID，不复制原文） |
| `contradicting_evidence` | array | 否（无则空数组） | 反证/不支持当前结论的证据 |
| `gaps` | array[string] | 是（可空） | 数据缺口：无法确认的环节 |
| `provenance` | {agent, ts} | 是 | 来源 Agent 与时间戳 |

示例（裁决输出）：

```json
{
  "root_cause": "attack",
  "claim": "外部入侵：T1003 凭据窃取 → T1021 横向移动 → T1078 身份滥用拖库",
  "confidence": 0.87,
  "claim_ref": "",
  "grade": "trusted",
  "hypotheses": [
    {"id": "H1", "type": "attack", "desc": "真实外部攻击", "confidence": 0.87},
    {"id": "H2", "type": "misop", "desc": "运维误操作", "confidence": 0.09},
    {"id": "H3", "type": "drill", "desc": "红队演练", "confidence": 0.04}
  ],
  "evidence": [
    {"id": "edr:proc_procdump_020607", "strength": "strong", "ref": "mock_evidence"},
    {"id": "ndr:flow_c2_021022", "strength": "strong", "ref": "mock_ndr"},
    {"id": "dbaudit:query_users_021805", "strength": "strong", "ref": "mock_dbaudit"}
  ],
  "contradicting_evidence": [],
  "gaps": ["报表服务器无进程级网络日志", "lsass.dmp 已删除"],
  "provenance": {"agent": "verdict", "ts": "2026-07-28T09:05:00+08:00"}
}
```

## 2. A 线各 Agent 输入输出

| Agent | 输入 | 输出（关键 ECP 字段） |
| --- | --- | --- |
| 分诊 triage | 种子弱信号 + mock_siem 告警列表 | `case_id`、事件简报：claim=疑似横向移动、`evidence_refs[]`（≡ hunter `event_refs`）、gaps、优先级 |
| 取证 hunter | 事件简报（`evidence_refs`/`event_refs`） | 证据快照：必含 `snapshot_id`、`entities`、`time_window`；claim=T1003 凭据转储成立、evidence refs（含哈希）、gaps（lsass.dmp 已删） |
| 关联 correlator | hunter 快照（`snapshot_id`/`entities`/`time_window`） | 实体图：必含 `entity_graph`（及平铺 entities/attack_mapping/identity_reachability）、claim=跨源证据闭合、证据 refs、gaps；Case 保持 INVESTIGATING |
| 裁决 verdict | 实体图（或平铺字段组装） | 裁决结论（ALIGNMENT §6.1）：`root_cause`、`claim_ref`、`claim`、`grade`、confidence、hypotheses、contradicting、gaps、provenance；Case→VERDICT_PENDING |

## 3. Case 状态机

主链状态：`NEW → TRIAGED → INVESTIGATING → VERDICT_PENDING → PLANNED → AWAITING_APPROVAL → EXECUTING → VERIFYING → SETTLE → CLOSED`

异常出口：

| 出口 | 触发条件 |
| --- | --- |
| `ESCALATED` | 证据不足 / Agent 结论冲突 / 提示注入命中 |
| `DEGRADED` | 工具超时或数据异常，降级用旁证继续 |
| `ABANDONED` | 主动放弃（明确判定无需处理） |

**A 线负责区间**：`NEW → TRIAGED → INVESTIGATING → VERDICT_PENDING`。  
- triage→`TRIAGED`；hunter→`INVESTIGATING`；correlator **不改状态**（保持 `INVESTIGATING`）；**仅 verdict**→`VERDICT_PENDING`。  
- 产出统一 verdict（含 `root_cause`/`claim`/`claim_ref`/`grade`）后，交 B 线从 `PLANNED` 起。

## 4. 与 C 的对齐点（结论溯源 claim-provenance）

- 裁决产出对齐 `contracts/ALIGNMENT.md` §6.1：`root_cause` / `claim` / `claim_ref` / `grade` / `confidence` / evidence…
- `claim_ref` 由 claim-provenance 回填（`verified:…` 或 `unverified`）；绑不上回执不得当强证据。
- 画像检索（actor-profile-rag）由 C 提供只读接口，A 线声明挂接，不另写文件。

## 5. 与 B 的工具契约引用

工具名称、函数、参数与返回结构以 `tools/tool_catalog.json` 为准；A 线主要消费：

- `mock_siem.list_alerts / get_seed_signal / search_events`
- `mock_edr.process_tree / process_access / network_connections / file_events`
- `mock_ndr.flows`
- `mock_ad.auth_log / account_info`
- `mock_dbaudit.query_log / baseline`
- `mock_intel.lookup / stealer_log`
- `mock_evidence.snapshot`
- `mock_ticket.create_case / get_case`
