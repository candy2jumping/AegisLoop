# Agent: planner（方案）

| 字段 | 内容 |
| --- | --- |
| **Name** | planner |
| **Owner** | B |
| **Role** | 方案：接裁决结论，出分级处置方案 + 回滚点 + 影响面 |
| **Capabilities** | 能：基于 verdict 生成分级动作清单、标注风险级/影响面/处置方式、识别数据泄露风险、预留回滚点；不能：执行任何写动作、直 @executor |
| **Inputs** | A 的裁决 `verdict`（经 leader 路由下发） |
| **Outputs** | plan JSON（`contracts/ALIGNMENT.md` §3）：`root_cause`/`data_leak_risk`/`plan_confidence`/`rollback_point`/`rollout`/`actions[]`；每项仅 `type,target,scope,risk_level,need_human,blast_radius,hits_tier0,treatment[,order,rollback]`（**禁止** `reason` 与 `affected`） |
| **Dependencies** | Skill：处置方案（containment-plan，主写）；调用横切★ `arg-risk-guard`、`blast-radius-guard`；工具：读 verdict；可查 `mock_ticket.get_case`；不写生产 |
| **DecisionBoundary** | 不执行写动作；不直 @executor；方案交回 leader 调度 |
| **Trace** | 输出带 `provenance:{agent,ts}`；Skill/工具调用写入 mock 网关 trace |
