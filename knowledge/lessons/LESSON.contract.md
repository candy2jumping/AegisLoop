# LESSON 落盘契约（Owner C）

## 文件形态

| 文件 | 用途 |
| --- | --- |
| `LESSON-<id>.json` | 机器可读；RAG / 画像索引源 |
| `LESSON-<id>.md` | 人读摘要（可选但初赛建议有） |

路径：`knowledge/lessons/`

## JSON 必填字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `lesson_id` | string | 如 `LESSON-2001` |
| `source_case` | string | 如 `CASE-2001` |
| `trace_id` | string | 关联调查 Trace |
| `trigger` | string | 人类可读触发特征摘要 |
| `trigger_features` | object | 结构化特征（供检索） |
| `attack` | string[] | ATT&CK IDs |
| `rule_suggestion` | string | 检测/升格规则建议 |
| `containment_hint` | string | 处置级别提示 |
| `detectionTuneHints` | string[] | 降噪 / 调优建议（至少 1 条） |
| `status` | string | `proposed` \| `active` \| `rejected` |
| `evidence_completeness` | string | `full` \| `partial` \| `weak` |
| `created_at` | string | ISO-8601 |

## 状态机

```text
write(lesson-settle) → proposed
soc-lead approve     → active   （才允许自动路径强依赖）
soc-lead reject      → rejected
```

## 索引刷新

`lesson-settle` 成功写盘后必须调用：

1. `mock_knowledge.refresh_rag_index`
2. `mock_intel.upsert_profile_index`

任一步失败：保留 JSON 文件，标记 `index_refreshed=false`，不阻断 Case CLOSED。

## 验收

- 二次同特征弱信号可被 `actor-profile-rag` 命中本 lesson
- `status=proposed` 时不得单独驱动自动 L2+ 处置
