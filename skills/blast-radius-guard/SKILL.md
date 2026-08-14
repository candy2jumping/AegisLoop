---
name: blast-radius-guard
version: 1.1.0
type: custom
description: 爆炸半径与 Tier-0 命中检测。字段名统一 hits_tier0（contracts/ALIGNMENT.md §2）。
---

# 影响面闸（blast-radius-guard）★

## Skill 类型

自定义 Skill（爆炸半径 + Tier-0 命中检测）

## 使用场景

横切：planner 出方案算波及范围、aegis-leader / executor 前闸；命中 Tier-0 自动升审。字段名统一 `hits_tier0`（见 `contracts/ALIGNMENT.md` §2）。

## 输入

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| action | object | 是 | `{type, target, scope}` |
| asset_map | object | 否 | 资产上下文；缺省读 `domain/tier0_assets.json` |

## 输出

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| blast_radius | string | 是 | 影响面摘要（对外可写入 plan.actions[].blast_radius） |
| hits_tier0 | bool | 是 | 是否命中 Tier-0 资产 |
| need_human | bool | 是 | Tier-0 命中时必为 true |
| risk_level | string | 是 | 命中 Tier-0 时为 `L4` |

说明：影响面明细可留在本 Skill 内部 / Trace；**不得**把 `affected` 写入对外 plan（ALIGNMENT §3）。

## 调用条件

planner 写方案动作时；leader 触达 executor 前；executor 执行前闸。

## 依赖

`domain/tier0_assets.json`（最高优先资产表；换壳只改此文件）。

## 失败处理

Tier-0 表缺失/不可读 → 保守视为可能命中并升人审；超时重试 2 次；不绕过闸门继续写。

## 权限与安全

只读影响面评估；不写生产；`hits_tier0=true` 强制人审 + L4，不可本地降级。

## 复用价值

挂接 planner / aegis-leader / executor（横切★）；换域仅替换资产表。

## 验证方式

**Golden**：目标 `dc-01`（Tier-0）→ `hits_tier0=true` + 升审 L4；普通主机不升审。  
**Badcase**：缺 target→记 gaps 并保守升审。

## 版本

`1.1.0` — 统一 `hits_tier0`；对外不输出 `affected`。

## 开源

Apache-2.0，随 AegisLoop 基座 Skill 发布。
