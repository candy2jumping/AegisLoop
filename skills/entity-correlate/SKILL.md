---
name: entity-correlate
version: 1.2.0
type: custom
description: 跨 SIEM/NDR/AD/DB/情报对齐实体并映射 ATT&CK。
---

# 跨源关联（entity-correlate）

## Skill 类型

自定义 Skill

## 使用场景

攻击链溯源中段：跨 SIEM/NDR/AD/数据库审计/情报对齐实体并映射 ATT&CK。

## 输入

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| case_id | string | 是 | 案件 ID |
| snapshot_id | string | 是 | 取证快照 ID |
| entities | object | 是 | 候选实体集（主机/IP/账号等） |
| time_window | object | 是 | `{start, end}` |
| sources | array | 是 | 待关联数据源列表；**必须 ≥2** |

## 输出

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| nodes | array | 是 | 实体节点 |
| edges | array | 是 | 关联边 |
| attck | array | 是 | ATT&CK 映射 |
| reachability | object | 是 | 含 identityReachability |
| evidence_refs | array | 是 | 证据引用 |
| gaps | array | 是 | 缺口（无则为 `[]`） |
| entity_graph | object | 是 | **信封别名**：`{nodes, edges, attck, reachability}`，供 verdict/`hypothesis-verdict` 直接消费（ALIGNMENT §8） |

对外 ECP 亦可平铺为 `entities` / `attack_mapping` / `identity_reachability`；verdict 须能把平铺字段包成 `entity_graph`。

## 调用条件

存在 **≥2** 个数据源信号待关联；取证快照已就绪。

## 依赖

工具：`mock_ndr`（flows）、`mock_ad`（auth_log/account_info）、`mock_siem`（search_events）、`mock_dbaudit`（query_log/baseline）、`mock_intel`（lookup）。

## 失败处理

单源失败 → **该源重试 2 次**，仍失败记 gaps 并输出候选集；多源冲突不硬下结论，交裁决处理。

## 权限与安全

全程只读；实体数据仅在共享状态中传递，不复制原始日志。

## 复用价值

横向移动、拖库等多源场景复用；换域仅换数据源契约。

## 验证方式

剧本 CASE-2001 实体图可复现；可达性结论与人工核对一致。

## 版本

`1.2.0` — 输出增加 `entity_graph` 信封，对齐 verdict 入参。

## 开源

Apache-2.0，随 AegisLoop 发布。
