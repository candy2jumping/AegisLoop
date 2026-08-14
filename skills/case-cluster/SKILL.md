# SKILL: 告警聚簇（case-cluster）

| 字段 | 内容 |
| --- | --- |
| **Skill 名称** | case-cluster（告警聚簇） |
| **Skill 类型** | 自定义 Skill |
| **使用场景** | 工作流环节 1-2（线索接入 → 自动研判）：把同一主体（主机/账号/IP）的多条弱信号聚簇、升格为 Case |
| **输入参数** | `alerts[]`（告警列表，来自 mock_siem）、`host` / `account`（主体标识）、`time_window`（默认 30m） |
| **输出结果** | `{case_id, priority, evidence_refs[], claim, gaps[]}`；`evidence_refs` **=** 下游 hunter 的 `event_refs`（同义，见 ALIGNMENT §8） |
| **调用条件** | 告警已过数据清洗（udb-sanitize）且未被标记为注入；满足任一即可升格：① 同一主体在 `time_window` 内 ≥3 条低危告警；② **medium** 相关种子（跨源弱信号同窗，CASE-2001 路径）；③ 窗内 ≥2 条相关信号（不同源或不同规则指向同一主体） |
| **依赖工具/系统** | mock_siem（查告警）、mock_ticket（建单） |
| **失败处理** | 缺字段记 `data_gaps` 不丢弃告警；mock_siem 超时重试 2 次，仍失败则降级为单条直接升格并提示人工；不阻断主链 |
| **权限与安全** | 只读 + 建单；不写生产；外部字段原文仅存引用，不进入上下文 |
| **复用价值** | triage 主用；演练/多场景聚簇逻辑可复用（同一能力换域可复用） |
| **验证方式** | Golden 样例 5 条（含噪声）；CASE-2001 medium 种子 + 双信号窗可升格；二次同特征对照升格率与误报率 |
| **版本** | v1.2.0（变更记录见文末） |
| **开源分发** | Apache-2.0，随 AegisLoop 基座 Skill 发布 |

## 变更记录

- v1.2.0（2026-08-11）：放宽调用条件——允许 medium 相关种子或窗内 ≥2 条相关信号升格（CASE-2001），不再仅限 ≥3 条低危。
- v1.1.0（2026-08-11）：明确 `evidence_refs`≡`event_refs`，对齐 hunter 入参。
- v1.0.0（2026-08-05）：初版，对齐官方附录 B 十字段与 ECP 输出。
