# AgentTeams SOC 任务消息

7 个业务 Worker、独立 TeamLeader Worker `aegis-leader` 以及 `aegisloop-soc` Team 创建完成后，在 Element Web/Matrix 会话列表中找到名称以 `Team` 开头、对应 `aegisloop-soc` 的 Team 房间。

进入 Team 房间后，在输入框先输入并选中 `@<team_leader_name>`（应指向 `aegis-leader`），再把下面的任务复制到这条 @ 消息里发送。不要把任务发给 `manager`。`manager` 用于创建和管理 Agent/Team；Team 房间中的 leader 用于接收业务任务并调度 Worker。

消息只包含用户能自然提供的弱信号现象和少量初始告警。SIEM 全量事件、EDR 进程树、NDR 流量、AD 认证、DB 审计、威胁情报、证据回执、处置与验证结果等，应由 Agent 通过工具网关主动查询。

## 主任务：CASE-2001 / lateral_movement_t1021

```text
@<team_leader_name>

请让你的 Team 处理一条新的 SOC 弱信号调查任务。

case_id: CASE-2001
scenario_id: lateral_movement_t1021
组织：Aegis 演示科技有限公司（虚构）
环境：Windows AD 域 + 财务/报表/数据库三网段 + VPN
联系人 / 人审：soc-lead

现象：
今早约 09:01，安全运营收到一条跨源弱信号：财务终端 10.20.3.17（finance-ws-17）在凌晨 02:09 向域控 10.0.0.8 发起 SMB 连接（ADMIN$），且同一主机在 02:06 附近出现针对 lsass.exe 的异常进程访问。单条告警不够立案，但两者同时出现，值班同事建议升格调查。财务同事反馈账号 zhang-san 昨夜有异常远程使用痕迹，但说不清细节。

初始告警（仅用户可见的少量条目）：
- 09:01 mock_siem.correlation finance_host_smb_to_dc + lsass_access severity=medium
- 02:09 SIEM 5140 财务终端访问域控管理共享 ADMIN$（src=10.20.3.17 dst=10.0.0.8）
- 02:06 EDR 提示 finance-ws-17 上疑似 lsass 内存访问（细节需工具查询）

请按 routing_order 自动协同：triage → hunter → correlator → verdict → planner →（由你做 ARG+Blast 前闸）→ executor → closer。
注意 Write Zone：业务 Worker 不得 @executor；只有你在前闸通过后（或 soc-lead 审批后）才能 @executor。
请输出完整 SOC 事故报告（含证据链、裁决 claim、处置与审批、验证与 lesson）。
```

## 可选：审批待决时的人工回复

若 Team 进入 `AWAITING_APPROVAL`，或明确请示 Tier-0 / L2–L4 动作，Human（`soc-lead`）可在同一 Team 房间回复：

```text
@<team_leader_name>

soc-lead 审批回复：
case_id: CASE-2001
decision: approve
scope: Tier-0 / L2-L4 pending actions in current plan
reason: 爆炸半径可控，证据已 verified；批准后请你 @executor 执行允许动作（Case→EXECUTING），再由 closer 做 VERIFYING→SETTLE→CLOSED。
```
