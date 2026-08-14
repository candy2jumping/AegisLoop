---
name: lesson-settle
version: 1.2.0
type: custom
description: 闭环⑧写 LESSON，输出 closure.lesson_ref。IO 严格表1。
---

# 经验沉淀（lesson-settle）

## Skill 类型

自定义 Skill

## 使用场景

SETTLE。顶层 IO **仅表1**：`case_id` / `verdict` / `execution` / `closure` / `entities` / `symptoms`。

## 输入（表1）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| case_id | string | 是 | |
| verdict | object | 是 | `{root_cause, confidence, claim_ref}` |
| execution | object | 是 | `{status, tel_ref}` |
| closure | object | 是 | `{resolved, lesson_ref}`（来自 residual-verify；本步常 lesson_ref=null） |
| entities | object | 是 | `{host, account, ip}` |
| symptoms | array | 是 | 无则 `[]` |

## 输出（表1）

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| case_id | string | 是 | |
| closure | object | 是 | `{resolved, lesson_ref}` |

```json
{
  "case_id": "CASE-2001",
  "closure": {
    "resolved": true,
    "lesson_ref": "LESSON-2001"
  }
}
```

文件落盘 `knowledge/lessons/LESSON-*.json` 为实现细节；**对外 IO 不另起顶层字段**。

## 调用条件

residual-verify 完成后进入 SETTLE。

## 依赖（表2 + 工具）

- 机制：`TEL.append`
- 工具：`mock_knowledge.write_lesson`、`mock_knowledge.refresh_rag_index`、`mock_intel.upsert_profile_index`

## 失败处理

写失败重试 2 → `lesson_ref=null`，不阻断 CLOSED。默认 proposed，active 须 soc-lead。

## 权限与安全

只写知识库；不写生产策略。

## 复用价值

closer；下游 actor-profile-rag。

## 验证方式

**Golden**

- 输入：`case_id=CASE-2001` 的 `verdict` / `execution` / `closure={resolved:true, lesson_ref:null}` / `entities` / `symptoms`
- 期望：落盘 `knowledge/lessons/LESSON-2001.json`（status 默认 `proposed`），输出 `closure.lesson_ref="LESSON-2001"`；索引刷新后可被 actor-profile-rag 二次命中

**Badcase**

- `write_lesson` 失败重试 2 次仍失败 → `lesson_ref=null`，不阻断案件 CLOSED
- 不得在无人审情况下将 lesson 直接标为 `active`（须 soc-lead）

## 版本

`1.2.0` — IO 锁定表1；对外只回写 closure.lesson_ref。

## 开源

Apache-2.0。
