---
name: actor-profile-rag
version: 1.2.0
type: custom
description: 按 entities 检索画像/LESSON，输出 hypotheses。IO 严格表1。
---

# 画像检索（actor-profile-rag）★

## Skill 类型

自定义 Skill

## 使用场景

关联后、裁决前。顶层 IO **仅表1**：`case_id` / `entities` / `symptoms` / `hypotheses`。

## 输入（表1）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| case_id | string | 是 | |
| entities | object | 是 | `{host, account, ip}`（来自 correlator 对齐结果） |
| symptoms | array | 是 | 来自 triage/聚簇；无症状时传 `[]` |

## 输出（表1）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| case_id | string | 是 | |
| hypotheses | array | 是 | 无命中为 `[]`，禁止编造 |

```json
{
  "case_id": "CASE-2001",
  "hypotheses": [
    {
      "id": "H1",
      "type": "attack",
      "confidence": 0.72,
      "prior_from_lesson": "LESSON-2001",
      "prior_boost": 0.08
    }
  ]
}
```

## 调用条件

entity-correlate 完成后，或 hypothesis-verdict 启动前。

## 依赖（表2 + 工具）

- 机制：`UDB.sanitize`（检索命中必须先清洗）
- 工具：`mock_intel.search_actor_profile`、`mock_knowledge.get_lesson`

## 失败处理

超时重试 2 → `hypotheses=[]`，不阻断主链。

## 权限与安全

只读；不写生产；不 @executor。

## 复用价值

横切★：correlator、verdict。

## 验证方式

**Golden**

- 输入：`entities={host:["web-01"], account:["svc_bak"]}`，`symptoms=["smb_to_dc"]`
- 期望：`hypotheses` 至少一条含 `prior_from_lesson="LESSON-2001"`、`prior_boost` 为数值；可用 `knowledge/lessons/LESSON-2001.json` 二次命中对照

**Badcase**

- 无命中 / 工具超时重试 2 次仍失败 → `hypotheses=[]`，不编造画像，不阻断主链
- 未经 `UDB.sanitize` 的命中不得写入 hypotheses

## 版本

`1.2.0` — IO 锁定表1；只出先验 hypotheses。

## 开源

Apache-2.0。
