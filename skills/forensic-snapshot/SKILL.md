---
name: forensic-snapshot
version: 1.2.0
type: custom
description: Case 升格后、深入取证前固定证据快照。
---

# 固证快照（forensic-snapshot）

## Skill 类型

自定义 Skill

## 使用场景

攻击链溯源开头：Case 升格后、深入取证前，先固定证据。

## 输入

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| case_id | string | 是 | 案件 ID |
| host | string | 否 | 主机标识（与 `ip` 至少其一） |
| ip | string | 否 | IP（与 `host` 至少其一） |
| time_window | object | 是 | `{start, end}` 查询时间窗 |
| event_refs | array | 是* | 待固证事件引用清单；*与 `evidence_refs` **二选一必填**（同义，ALIGNMENT §8） |
| evidence_refs | array | 是* | `event_refs` 别名；triage 简报常用此名 |

## 输出

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| snapshot_id | string | 是 | 快照 ID（下游 correlator **必收**） |
| items | array | 是 | `[{ref, hash, type}]` |
| entities | object | 是 | 候选实体 `{hosts[], ips[], accounts[]}`（供 correlator） |
| time_window | object | 是 | 与入参一致或收敛后的 `{start,end}` |
| gaps | array | 是 | 固证缺口（无则为 `[]`） |

## 调用条件

Case 状态为 `TRIAGED` 或 `INVESTIGATING`，且任何深入 hunt / 主动取证动作之前。

## 依赖

工具：`mock_edr`（查事件）、`mock_evidence`（存快照与哈希）。

## 失败处理

`mock_edr` / `mock_evidence` 失败 → 各重试 2 次；仍失败记 `gaps`，不阻塞后续取证；遵守隐蔽性预算（StealthBudget）。

## 权限与安全

只读；快照写入证据库，哈希必写；不写生产系统。

## 复用价值

任意取证场景复用（横向移动、拖库、勒索等）。

## 验证方式

快照可回放：按 `snapshot_id` 能取回全部证据与哈希。

## 版本

`1.2.0` — 接受 `evidence_refs`≡`event_refs`；输出补 `entities`/`time_window` 供 correlator。

## 开源

Apache-2.0，随 AegisLoop 发布。
