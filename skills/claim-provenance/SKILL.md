---
name: claim-provenance
version: 1.3.0
type: custom
description: 将 verdict 结论绑定证据回执；失败则 claim_ref=unverified。IO 用 root_cause+claim_ref；ECP.grade∈trusted|suspicious|untrusted。
---

# 结论溯源（claim-provenance）★

## Skill 类型

自定义 Skill

## 使用场景

闭环验证/出证前。顶层 IO **仅表1**：`case_id` / `verdict` / `entities` / `tel_ref`。

## 输入（表1）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| case_id | string | 是 | 案件 ID |
| verdict | object | 是 | `{root_cause, confidence, claim_ref[, claim, grade]}`；`root_cause`∈`attack|misop|drill|capacity|unknown`；尚未溯源时 `claim_ref` 传 `""`；不得内嵌 entities |
| entities | object | 是 | `{host, account, ip, evidence_refs}`，证据引用所在实体，供回执核对 |

`ECP.grade` 仅：`trusted` \| `suspicious` \| `untrusted`（ALIGNMENT §4）。

## 输出（表1）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| case_id | string | 是 | |
| verdict | object | 是 | 更新 `confidence`、`claim_ref`；保留 `root_cause`（及可选 `claim`/`grade`） |
| tel_ref | string | 是 | `TEL.append` 返回的回执 |

```json
{
  "case_id": "CASE-2001",
  "verdict": {
    "root_cause": "attack",
    "confidence": 0.82,
    "claim_ref": "verified:rcpt-EDR-1001",
    "claim": "外部入侵：T1003 → T1021 → T1078",
    "grade": "trusted"
  },
  "tel_ref": "tel:evt-claim-2001"
}
```

规则：无法绑回执 → `claim_ref="unverified"` 且 `confidence ≤ 0.4`。

## 调用条件

1. hypothesis-verdict 已产出 `verdict`；或  
2. closer 封存前复验。

## 依赖（表2 + 工具）

- 机制：`ECP.grade`、`TEL.append`
- 工具：`mock_evidence.get_receipt`

禁止 dependencies 中出现未登记机制名。

## 失败处理

回执缺失/超时：重试 2 → unverified。  
`ECP.grade`∈{suspicious,untrusted}：禁止 verified。  
`TEL.append` 失败：仍返回 verdict，但本 Skill 视为失败（调用方不得当终局 verified）。

## 权限与安全

只读校验 + TEL 记账；不写生产；不绕过 `ARG.check`。

## 复用价值

横切★：`verdict`、`closer`、leader 汇总。

## 验证方式

**Golden**

- 输入：`case_id=CASE-2001`，`verdict={root_cause:"attack", confidence:0.82, claim_ref:""}`，`entities={host:["web-01"], account:["svc_bak"], evidence_refs:["edr:lsass"]}`
- 期望：`verdict.claim_ref="verified:rcpt-EDR-1001"`，`tel_ref` 非空（如 `tel:evt-claim-2001`），`root_cause` 保持，confidence 保持 ≥0.6

**Badcase**

- 回执缺失 / `ECP.grade`∈{suspicious,untrusted} → `claim_ref="unverified"` 且 `confidence≤0.4`，不得输出 verified
- `TEL.append` 失败 → 仍可返回降级后的 verdict，但调用方不得当作终局 verified

## 版本

`1.3.0` — IO 锁定 `root_cause`+`claim_ref`；`ECP.grade`∈trusted|suspicious|untrusted。

## 开源

Apache-2.0。
