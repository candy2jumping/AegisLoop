# SKILL: 合规通报（compliance-notify）

| 字段 | 内容 |
| --- | --- |
| **Skill 名称** | compliance-notify（合规通报） |
| **Skill 类型** | 自定义 Skill |
| **使用场景** | 处置执行后/收尾：仅当 `data_leak_risk=true` 时发合规通报并生成工单（TEL 落账） |
| **输入参数** | `event`（object：含动作 + 结果）、`data_leak_risk`（bool） |
| **输出结果** | `{ticket_id: str \| null}`；未识别泄露时 `{ticket_id: null, skipped: true, reason}` |
| **调用条件** | `data_leak_risk=true`（识别到数据泄露）；`false` 时跳过不发单 |
| **依赖工具/系统** | 机制 `TEL.append`；可配合 `mock_ticket` 出工单引用 |
| **失败处理** | TEL 写失败重试 2 次，仍失败记 gaps 并上报，不伪造 ticket_id；`data_leak_risk=false` 明确 skipped |
| **权限与安全** | 仅通报/工单 TEL，不写生产处置；不得在无泄露标记时滥发 |
| **复用价值** | 主挂接 executor；planner / soc-lead 可声明调用（不强制） |
| **验证方式** | Golden：`data_leak_risk=true`→非空 ticket_id；Badcase：`false`→skipped 且 ticket_id=null |
| **版本** | v1.0.0（变更记录见文末） |
| **开源分发** | Apache-2.0，随 AegisLoop 基座 Skill 发布 |

## 变更记录

- v1.0.0（2026-08-05）：初版，对齐附录 B 十字段与「仅数据泄露触发」口径。
