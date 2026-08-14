---
name: arg-risk-guard
version: 1.1.0
type: custom
description: ARG 风险闸门。定级表与 contracts/ALIGNMENT.md §1 一致。
---

# 风险闸门（arg-risk-guard）★

## Skill 类型

自定义 Skill（机制 ARG 的可调用封装）

## 使用场景

横切：planner 出方案打级、aegis-leader 路由前闸、executor 动手前闸；给动作定 L0–L4 并判断 `need_human`。权威：`contracts/ALIGNMENT.md` §1。

## 输入

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| action | object | 是 | `{type, target, scope}` |

## 输出

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| risk_level | string | 是 | `L0`\|`L1`\|`L2`\|`L3`\|`L4` |
| need_human | bool | 是 | 是否强制人审 |
| reason | string | 是 | 定级理由 |
| treatment | string | 是 | `auto`\|`gray`\|`approval`\|`suggest` |

## ARG 定级表（ALIGNMENT §1）

| risk_level | treatment | 典型动作 | 人审 |
| --- | --- | --- | --- |
| L0 | auto | 只读探测、低危标记 | 否 |
| L1 | gray | 低危缓解（**非**隔离主机） | 否 |
| L2 | approval | `block_ip`、`scale_out`、`disable_account` | 是（审批后可执行） |
| L3 | suggest | `block_domain` | 不执行，仅建议 |
| L4 | approval | `isolate_host` / `quarantine` / `reset_credentials` | **强制人审** |

补充：Tier-0 命中（`hits_tier0=true`，由 blast 给出）→ 无论原级别，升为 **L4 + need_human=true**。  
策略：`auto_execute=[L0,L1]`；`approval_required=[L2,L4]`；`suggest_only=[L3]`；`tier0=force_human_review`。

## 调用条件

planner 生成候选动作时；leader 触达 executor 前；executor 执行每个动作前。缺 `action.type` → 拒绝定级。

## 依赖

定级规则见 `contracts/ALIGNMENT.md` §1；无外部必选工具；可选 `mock_ticket` 审计落账。

## 失败处理

ARG 不可用 → 默认升为需人审（保守失败）；超时重试 2 次；不绕过闸门继续写。

## 权限与安全

只读定级；不写生产；不替代人审批结果。

## 复用价值

挂接 planner / aegis-leader / executor（横切★）。

## 验证方式

**Golden**：`isolate_host`→L4+need_human+approval；`block_ip`→L2；`block_domain`→L3 suggest；低危→L0/L1。  
**Badcase**：缺 `action.type`→拒绝定级并记 gaps。

## 版本

`1.1.0` — 定级表与 ALIGNMENT §1 对齐。

## 开源

Apache-2.0，随 AegisLoop 基座 Skill 发布。
