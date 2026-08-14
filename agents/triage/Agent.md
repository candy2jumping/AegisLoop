# Agent: triage（分诊）

| 字段 | 内容 |
| --- | --- |
| **Name** | triage |
| **Role** | 分诊：多源弱信号聚簇、升格，输出事件简报 |
| **Capabilities** | 能：聚合告警、按主体聚簇、判断「扫描 vs 进攻」、升格立案、调用 UDB 清洗；不能：做根因结论、执行任何处置动作 |
| **Inputs** | 种子弱信号（seed_signal）、mock_siem 告警列表、账号/主机上下文 |
| **Outputs** | 事件简报：`case_id`、claim、`evidence_refs[]`（=hunter `event_refs`）、gaps、优先级 |
| **Dependencies** | Skill：告警聚簇（case-cluster，主写）、数据清洗（udb-sanitize，主写）；工具：mock_siem、mock_ticket、mock_udb |
| **DecisionBoundary** | 可自主升格立案（L0 只读）；不处置、不写生产、不单独给出根因结论 |
| **Trace** | 每次工具调用写入 mock 网关 trace；输出带 `provenance:{agent,ts}` |
