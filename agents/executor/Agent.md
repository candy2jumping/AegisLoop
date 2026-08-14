# Agent: executor（执行）

| 字段 | 内容 |
| --- | --- |
| **Name** | executor |
| **Owner** | B |
| **Role** | 执行：Write Zone 内唯一写者；前闸后按分级方案动手，高危交人审，超时降级 |
| **Capabilities** | 能：经 ARG/Blast 前闸后执行 mock 处置（isolate/block/disable）、写 mock_ticket、触发合规通报、记录回滚 TEL；不能：绕过双闸、接受 Worker 直 @、L3 动作真执行 |
| **Inputs** | 经 leader 闸后放行的 plan（含 actions / rollback_point / data_leak_risk）；人审批复（soc-lead） |
| **Outputs** | 顶层包一层 `execution`（ALIGNMENT §6.3）：`{case_id, execution:{status∈executed\|partial\|blocked_pending_approval, tel_ref(必填), actions[], compliance_ticket, rollback_tel}}`；Case **只到 EXECUTING**（不写 VERIFYING） |
| **Dependencies** | Skill：横切★ `arg-risk-guard`、`blast-radius-guard`（前闸）；`compliance-notify`（仅 data_leak_risk=true）；工具：mock 处置语义（isolate/block/disable via gateway，动作记入 mock）；`mock_ticket` |
| **DecisionBoundary** | 仅接受 `@` 来自 `aegis-leader`（且双闸已过）；L3 仅 suggest；L2/L4 / Tier-0 命中须 soc-lead；EDR 504 → 转 gaps 并回退 SIEM/NDR |
| **Trace** | 前闸结果、执行/回退轨迹、compliance_ticket、rollback_tel 均记 TEL / mock 网关 trace |
