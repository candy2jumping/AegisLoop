---
name: hypothesis-verdict
version: 1.3.0
type: custom
description: 多假设竞争裁决，输出 ECP（含 root_cause/claim_ref/claim/grade）。对齐 contracts/ALIGNMENT.md §4/§6.1。
---

# 假设裁决（hypothesis-verdict）

## Skill 类型

自定义 Skill（机制 HD-Loop 的可调用封装）

## 使用场景

溯源 → 结论：对多个竞争假设分别取证、打分，输出裁决结论（ECP）。

## 输入

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| case_id | string | 是 | 案件 ID |
| entity_graph | object | 是* | 跨源关联产出的实体图；*若缺省，可用 correlator 平铺字段组装：`{nodes:entities, edges:[], attck:attack_mapping, reachability:identity_reachability}`（ALIGNMENT §8） |
| entities | array/object | 否 | `entity_graph` 平铺别名 |
| attack_mapping | array | 否 | `entity_graph.attck` 平铺别名 |
| identity_reachability | object | 否 | `entity_graph.reachability` 平铺别名 |
| profile | object | 否 | 画像检索结果（`actor-profile-rag`）；**可空** |
| read_queries | object | 否 | 只读补充查询结果 |

即使 `profile` 为空，仍须播种 **≥3** 条模板假设：`attack` / `misop` / `drill`。

## 输出（ECP）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| root_cause | string | 是 | **机器枚举**：`attack` \| `misop` \| `drill` \| `capacity` \| `unknown` |
| confidence | number | 是 | 0.0–1.0 |
| claim_ref | string | 是 | claim-provenance 回填前可为空串 `""`；之后为 `verified:…` 或 `unverified` |
| claim | string | 是 | 人类可读一句话裁决主张 |
| grade | string | 是 | **仅** `trusted` \| `suspicious` \| `untrusted`（ALIGNMENT §4） |
| hypotheses | array | 是 | `[{id, type, desc, confidence}]`，至少 3 条；`type`∈`attack|misop|drill|capacity|unknown` |
| evidence | array | 是 | 支持证据 |
| contradicting_evidence | array | 是 | 反证 |
| gaps | array | 是 | 缺口 |
| provenance | object | 是 | 溯源元数据 |

## 调用条件

溯源完成；存在竞争假设（不足时由本 Skill 用 attack/misop/drill 模板补齐至 ≥3）。

## 依赖

只读补充查询（`mock_siem`/`mock_edr`/`mock_intel`）；挂接：结论溯源（`claim-provenance`）。

## 失败处理

假设不收敛 → **不**生成无证据终局结论；输出 gaps 与采集建议；Case 转 **`ESCALATED`**。  
`grade∈{suspicious,untrusted}` 时由 claim-provenance 约束 `claim_ref=unverified` 且 `confidence≤0.4`。

## 权限与安全

只读；结论必须绑定证据回执（claim），绑不上标 unverified；不触发任何写动作。Case 状态只推进到 `VERDICT_PENDING`（不得直接 `PLANNED`）。

## 复用价值

任意多假设场景复用（攻击/误报/演练三选）；换域仅换假设模板。

## 验证方式

CASE-2001 输出 H1=0.87/H2=0.09/H3=0.04 与剧本预期一致；证据引用可逐条取回；`grade` 枚举合法；必含 `root_cause`/`claim_ref`/`claim`/`grade`。

## 版本

`1.3.0` — 接受 correlator 平铺字段组装 `entity_graph`（ALIGNMENT §8）。

## 开源

Apache-2.0，随 AegisLoop 基座 Skill 发布。
