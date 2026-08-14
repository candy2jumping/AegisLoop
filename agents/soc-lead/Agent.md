# soc-lead（Human）

## Identity（附录 A）

| 字段 | 内容 |
| --- | --- |
| Name | `soc-lead` |
| Role | Human / 人审（IR 指挥官） |
| Capabilities | 审批 L2/L4 与 Tier-0 命中动作；批准或驳回 lesson `proposed→active`；可要求补证或退回 planner |
| Inputs | Leader 提交的处置方案、ARG/Blast 定级、爆炸半径、证据摘要、TEL/Trace 引用 |
| Outputs | `approve` / `reject` / `request_changes` + 理由；可选 lesson 激活指令 |
| Dependencies | 依赖 Leader 汇总材料；不直接调生产工具 |
| DecisionBoundary | 可拒绝并退回；超时未批则动作保持 `approval_pending`，禁止自动升格执行 |
| Trace | 审批事件必须写入审计（关联 TraceId / TEL） |

## Mission

人在回路：高风险与关键资产动作的最终拍板者。日常弱信号研判由 Agent 自动完成；禁用账号、广域变更、Tier-0 等必须经本角色。

## 与官方 HITL 的关系

阿里云 HITL 为人机协同审批壳（偏云 CLI 高风险操作）。本角色吸收其「高风险暂停等人确认」模式，但审批语义绑定 AegisLoop 的 ARG / Blast / Tier-0 / lesson 激活，而非替换为云 HITL Skill。

## Approval Contract

```json
{
  "case_id": "CASE-2001",
  "action_id": "disable-svc-account-finance",
  "decision": "approve",
  "reason": "爆炸半径可控且证据 verified",
  "approver": "soc-lead",
  "ts": "2026-08-05T10:25:00+08:00"
}
```
