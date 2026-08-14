---
name: residual-verify
version: 1.4.0
type: custom
description: 按 plan/execution 残留验证并出证。plan.actions[] 对齐 contracts/ALIGNMENT.md §3；execution 对齐 §6.3。
---

# 残留验证（residual-verify）

## Skill 类型

自定义 Skill

## 使用场景

VERIFYING。顶层 IO：`case_id` / `plan` / `execution` / `verdict` / `closure` / `tel_ref`。

## 输入

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| case_id | string | 是 | |
| plan | object | 是 | 对齐 ALIGNMENT §3：`{root_cause?, data_leak_risk?, plan_confidence, rollback_point, rollout?, actions[]}`；`actions[]` 仅允许 `type,target,scope,risk_level,need_human,blast_radius,hits_tier0,treatment[,order,rollback]`（允许 `hits_tier0`/`treatment`；禁止 `affected`/`reason`） |
| execution | object | 是 | `{status, tel_ref}`（来自 executor）；`status`∈`executed`\|`partial`\|`blocked_pending_approval`；**`tel_ref` 必填** |
| verdict | object | 是 | `{root_cause, confidence, claim_ref}`（建议已经过 claim-provenance） |

## 输出

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| case_id | string | 是 | |
| execution | object | 是 | 更新 status、tel_ref；写出后 `status`∈`verified`\|`needs_attention`\|`approval_pending`\|`unverified` |
| closure | object | 是 | `{resolved, lesson_ref}`；本步 lesson_ref 通常 null |
| tel_ref | string | 是 | 与 execution.tel_ref 一致 |

```json
{
  "case_id": "CASE-2001",
  "execution": {"status": "verified", "tel_ref": "tel:pack-2001"},
  "closure": {"resolved": true, "lesson_ref": null},
  "tel_ref": "tel:pack-2001"
}
```

`execution.status`（输出）∈ `verified` | `needs_attention` | `approval_pending` | `unverified`。  
closer 可用 `verify_status` 作为本 Skill 写出 status 的别名，但内部必须以本输出为准。

## 调用条件

VERIFYING，且 `plan.actions` 与 `execution`（含必填 `tel_ref`）已存在。

## 依赖

- 机制：`TEL.append`、`ECP.grade`
- 工具：`mock_probe.check_host`、`mock_probe.check_account`、`mock_evidence.export_tel_pack`、`mock_ticket.create_followup`

## 失败处理

probe 失败 → unverified + resolved=false，可 followup。  
残留 → needs_attention。  
输入仍为 `blocked_pending_approval` → 写出 `approval_pending`。  
禁止在本 Skill 内执行 isolate/disable/block。

## 权限与安全

只读验证 + 出证；写处置仅 executor。

## 复用价值

主挂接：closer。

## 验证方式

**Golden**

- 输入：含 **L4** `isolate_host`（`need_human=true`，`treatment=approval`，含 `hits_tier0`；**人审批准后**）的 `plan` + `execution={status:"executed", tel_ref:"tel:exec-1"}` + 已溯源 `verdict`
- 期望：`execution.status="verified"`，`closure={resolved:true, lesson_ref:null}`，顶层 `tel_ref` 与 `execution.tel_ref` 一致（如 `tel:pack-2001`）

**Badcase**

- probe 失败 → `execution.status="unverified"`，`closure.resolved=false`，可调 `mock_ticket.create_followup`
- 发现残留 → `needs_attention`；不得在本 Skill 内执行 isolate/disable/block
- 缺 `plan.actions`、`execution` 或 `tel_ref` → 不进入成功 verified
- 输入 `blocked_pending_approval` → 写出 `approval_pending`

## 版本

`1.4.0` — 输入 status∈executed|partial|blocked_pending_approval；`tel_ref` 必填；Golden=L4 isolate after approval。

## 开源

Apache-2.0。
