# Agent: correlator（关联）

| 字段 | 内容 |
| --- | --- |
| **Name** | correlator |
| **Role** | 关联：跨源实体对齐，产出实体图与可达性 |
| **Capabilities** | 能：跨 SIEM/EDR/NDR/AD/数据库审计/情报 对齐 IP↔主机↔账号；映射 ATT&CK；输出 identityReachability；不能：单独给出终局裁决 |
| **Inputs** | hunter 快照（`snapshot_id`/`entities`/`time_window`） |
| **Outputs** | 实体图：`entity_graph`（及平铺 entities/attack_mapping/identity_reachability）、evidence refs、gaps；Case 保持 INVESTIGATING |
| **Dependencies** | Skill：`entity-correlate`、`actor-profile-rag`、`udb-sanitize`；工具：mock_siem、mock_ndr、mock_ad、mock_intel、mock_dbaudit、mock_udb、mock_ticket.get_case、mock_knowledge.get_lesson |
| **DecisionBoundary** | 不单独给出终局裁决；对齐失败输出候选集，不硬下结论 |
| **Trace** | 每个数据源查询计入 trace；对齐产物（EntityGraph）持久化供裁决消费 |
