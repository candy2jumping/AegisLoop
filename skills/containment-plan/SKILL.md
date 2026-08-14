---
name: containment-plan
version: 1.1.0
type: custom
description: 将 verdict 转为分级处置 plan。对外 schema 严格对齐 contracts/ALIGNMENT.md §3（无 affected）。
---

# 处置方案（containment-plan）

## Skill 类型

自定义 Skill（主链）

## 使用场景

裁决后 → 方案：接 leader 转来的 verdict，出分级处置方案（每动作带风险级 + 爆炸半径 + treatment）+ 回滚点 + 数据泄露识别。权威契约：`contracts/ALIGNMENT.md` §3。

## 输入

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| verdict | object | 是 | `{root_cause, confidence, claim_ref?}` |
| case_id | string | 否 | 案件 ID，缺省从路由上下文取 |

## 输出

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| root_cause | string | 是 | 与裁决一致或细化 |
| data_leak_risk | bool | 是 | 是否存在数据泄露风险 |
| plan_confidence | number | 是 | 0.0–1.0 |
| rollback_point | string | 是 | 回滚点引用（如 `snap-...`） |
| rollout | string | 是 | 分级 rollout 说明 |
| actions | array | 是 | 见下表；**禁止** `affected` / `reason` |

`actions[]` 每项（对齐 ALIGNMENT §3）：

| 字段 | 类型 | 必填 |
|------|------|------|
| type | string | 是 |
| target | string | 是 |
| scope | string | 是 |
| risk_level | string | 是 |
| need_human | bool | 是 |
| blast_radius | string | 是 |
| hits_tier0 | bool | 是 |
| treatment | string | 是（`auto`\|`gray`\|`approval`\|`suggest`） |
| order | integer | 否 |
| rollback | string | 否 |

定级口径（ALIGNMENT §1）：`isolate_host`→L4+need_human；`block_ip`→L2；`block_domain`→L3 suggest；`hits_tier0=true`→升 L4。

## 调用条件（可判定）

同时满足：

1. Case 状态为 `VERDICT_PENDING`（或刚完成 verdict 路由）；
2. 输入存在非空 `verdict.root_cause` 与数值 `verdict.confidence`；
3. 本 Skill 尚未为该 `case_id` 产出终局 `plan`（或 leader 明确要求重规划）。

不满足 → 不调用，记 `gaps`，不硬编方案。

## 依赖

- Skill：`arg-risk-guard`、`blast-radius-guard`（横切★）
- Tier-0：经 blast 读 `domain/tier0_assets.json`
- 无生产写工具

## 失败处理

缺 `verdict` → 记 `gaps` 不硬编方案；依赖 Skill/工具超时重试 2 次，仍失败则降级并提示人工；不写生产。

## 权限与安全

只读研判 + 出方案；不写生产；不直 @executor。

## 复用价值

planner 主用；主链「结论→动作清单」可换域复用（换 Tier-0/动作表即可）。

## 验证方式

**Golden**：attack 含 `isolate_host`（L4）/`block_ip`（L2）+ Tier-0 升审；capacity 扩容无泄露；actions 无 `affected`。  
**Badcase**：缺 verdict→gaps；闸超时重试 2。

## 版本

`1.1.0` — 对外 plan 去掉 `affected`；字段与 treatment 对齐 `contracts/ALIGNMENT.md`。

## 开源

Apache-2.0，随 AegisLoop 基座 Skill 发布。
