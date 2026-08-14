# AegisLoop 冻结契约（合仓对齐）

> 冲突时以本文件为准。改 ARG / plan / Tier-0 / ECP / 交接对象时先改这里。

## 1. ARG 风险定级（与 `skills/arg-risk-guard/SKILL.md` / create 消息一致）

| risk_level | treatment | 典型动作 | 人审 |
| --- | --- | --- | --- |
| L0 | auto | 只读探测、低危标记 | 否 |
| L1 | gray | 低危缓解（**非** isolate_host） | 否 |
| L2 | approval | `block_ip`、`scale_out`、`disable_account` | 是（审批后可执行） |
| L3 | suggest | `block_domain` | **不执行**，仅建议 |
| L4 | approval | `isolate_host` / `quarantine` / `reset_credentials` | **强制人审** |

- Tier-0 命中（`hits_tier0=true`）→ 升为 **L4 + need_human=true**。
- 对外文案：人审对象是 **L2/L4**（及 Tier-0）；**不要**再写「L2/L3 审批」。

## 2. Tier-0 字段名

统一 **`hits_tier0`**（禁止 `tier0_hit`）。

## 3. plan 对外 schema（B→C）

见 `schemas/dict_table1.json`。`actions[]` 允许字段：

`type, target, scope, risk_level, need_human, blast_radius, hits_tier0, treatment[, order, rollback]`

禁止对外 `affected` / `reason`。`compliance-notify` 是 Skill，**不是** plan.action.type。

## 4. ECP.grade

仅：`trusted` | `suspicious` | `untrusted`。

## 5. Case 状态机

主链：`NEW → TRIAGED → INVESTIGATING → VERDICT_PENDING → PLANNED → AWAITING_APPROVAL → EXECUTING → VERIFYING → SETTLE → CLOSED`

硬规则：

- **verdict** 只推进到 `VERDICT_PENDING`（不得直接 `PLANNED`）
- **planner** 才写 `PLANNED`
- **aegis-leader** 才写 `AWAITING_APPROVAL`（need_human / hits_tier0 时）
- **executor** 只推进到 `EXECUTING`（**不得**写 `VERIFYING`）；**禁止** leader 写 `EXECUTING`
- **closer** 负责 `VERIFYING → SETTLE → CLOSED`
- L0/L1 全自动且无需人审时，可从 `PLANNED` **跳过** `AWAITING_APPROVAL` 直接由 leader @executor → executor 写 `EXECUTING`
- 需要人审时：leader → `AWAITING_APPROVAL` → soc-lead approve → leader @executor → executor → `EXECUTING`

## 6. 跨线交接对象（A→B→C）——必须同一套字段

### 6.1 verdict（A 产出 → B planner / C claim）

```json
{
  "root_cause": "attack",
  "confidence": 0.87,
  "claim_ref": "",
  "claim": "外部入侵：T1003 → T1021 → T1078",
  "grade": "trusted",
  "hypotheses": [{"id":"H1","type":"attack","desc":"...","confidence":0.87}],
  "evidence": [{"id":"...","strength":"strong","ref":"..."}],
  "contradicting_evidence": [],
  "gaps": [],
  "provenance": {"agent":"verdict","ts":"..."}
}
```

| 字段 | 用途 |
| --- | --- |
| `root_cause` | **机器枚举**：`attack` \| `misop` \| `drill` \| `capacity` \| `unknown`；containment-plan 分支用它 |
| `claim` | 人类可读一句话（可与 ECP 叙述并存） |
| `claim_ref` | claim-provenance 回填：`verified:…` 或 `unverified`；产出前可为空串 |
| `confidence` / `grade` | 置信与 ECP 等级 |

### 6.2 plan（B planner → leader / executor / closer）

见 §3；另含顶层 `root_cause`, `data_leak_risk`, `plan_confidence`, `rollback_point`, `rollout`。

### 6.3 execution（B executor → C residual / lesson）

```json
{
  "status": "executed",
  "tel_ref": "tel:…",
  "actions": [{"type":"…","target":"…","status":"done|done(fallback)|suggested_only|rejected_by_human|blocked_pending_approval"}],
  "compliance_ticket": null,
  "rollback_tel": "tel:…"
}
```

| `execution.status` | 含义 |
| --- | --- |
| `executed` | 允许的动作已执行（含 fallback） |
| `partial` | 部分成功 |
| `blocked_pending_approval` | 整单仍等人审 |

`tel_ref` **必填**（可与 `rollback_tel` 同值）。  
residual-verify 读入上述 status 后，写出更新后的 `execution.status` ∈ `verified|needs_attention|approval_pending|unverified`。  
closer 对外可用 `verify_status` 作为 residual 结果的别名，但内部必须以 residual-verify 输出为准。

## 7. 工具调用体（易错点）

| 工具 | 正确 body 关键字段 |
| --- | --- |
| `mock_siem.search_events` | `event_id`, `host`, `user`, `since`, `until`（**无** `keyword`） |
| `mock_ticket.create_followup` | `case_id`, `reason`, `severity`（**无** `title`/`details`） |
| `mock_contain.isolate_host` | `host`；可选 `simulate_timeout` |
| `mock_contain.block_ip` | `ip` |
| `mock_contain.block_domain` | `domain`（**L3 suggest_only：可调用记录建议，不得当真执行处置语义以外的生产写**；本 mock 仅记 suggested） |
| `mock_contain.disable_account` | `account` |
| `mock_udb.sanitize` | **`fields`**（对象）；兼容别名 `object` |

## 8. A 线 Skill 字段别名（防断链）

| 上游字段 | 下游字段 | 规则 |
| --- | --- | --- |
| triage `evidence_refs[]` / ECP `evidence[].ref` | hunter `event_refs` | **同义**；hunter 必须接受二者之一 |
| hunter `snapshot_id` + `entities` + `time_window` | correlator 同名字段 | hunter **对外必出** `snapshot_id` |
| correlator `entities` + `attack_mapping` + `identity_reachability` | verdict `entity_graph` | correlator 可直接输出 `entity_graph={nodes,edges,attck,reachability}`，或由 verdict 将三者包成 `entity_graph` |

## 9. 审批顺序（禁止 execute-then-ask）

1. planner 出 plan（含 risk / hits_tier0）
2. aegis-leader ARG+Blast
3. 若 need_human 或 hits_tier0 → `AWAITING_APPROVAL`，请示 soc-lead
4. soc-lead `approve` 后，**leader @executor**
5. executor 再执行允许动作并写 `EXECUTING`
6. closer 再 `VERIFYING→SETTLE→CLOSED`
