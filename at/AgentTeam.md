# AegisLoop SOC AgentTeam（控制面 · Owner C）

Team 名称：`aegisloop-soc`  
TeamLeader：`aegis-leader`（创建 Team 时由 manager **独立生成**，禁止业务 Worker 兼任）

## AgentTeams 映射

| 框架能力 | 本设计 |
| --- | --- |
| 角色编排 | 独立 Leader + 7 Worker + Human（`soc-lead`） |
| 任务拆解 | Leader 按调查阶段派单并附预算 |
| 上下文传递 | ECP / plan IO：`schemas/dict_table1.json` + `contracts/ALIGNMENT.md`；大取证物传引用 |
| 协同执行 | 调查组 peerMentions 开放；**Executor 禁止被 Worker 直 @** |
| 状态追踪 | `NEW → TRIAGED → INVESTIGATING → VERDICT_PENDING → PLANNED → AWAITING_APPROVAL → EXECUTING → VERIFYING → SETTLE → CLOSED`；异常：`ESCALATED` / `ABANDONED` / `DEGRADED` |
| 人在回路 | `soc-lead` 审批 **L2/L4** 与 Tier-0（**L3 suggest_only**）；lesson `active` 须人审 |

## 通信隔离（Write Zone）

```text
soc-lead ⇄ aegis-leader ──@──► executor（唯一写）
                │
                ├── triage / hunter / correlator / verdict / planner / closer
                └── ✕ Worker 不得直 @ executor
```

前闸：Leader 在触达 executor 前必须声明调用 `arg-risk-guard` + `blast-radius-guard`（Skill 正文归 B）。  
路由口径（对齐 B 已锁输出 / `contracts/ALIGNMENT.md`）：`need_human=true` 或 `hits_tier0=true` → `AWAITING_APPROVAL` / `soc-lead`；`compliance-notify` 由 B（planner/executor）触发，C 不挂接。

## C 线 Agent 与 Skill

| Agent | Owner | Skills |
| --- | --- | --- |
| `aegis-leader` | C | 声明：arg/blast（B）；claim-provenance |
| `closer` | C | claim-provenance★、residual-verify、lesson-settle⑧ |
| `soc-lead` | C | Human 审批（无生产写 Skill） |

横切只读：`actor-profile-rag`★ 正文归 C，挂接方为 correlator/verdict（A 声明调用）。

## 运行时说明

与官方 `opspilot-zero-demo` 同构：Worker 通过 HTTP mock 工具网关取数；本地 `agents/*`、`skills/*` 供评审与 Registry 替换。完整 create 消息见 `at/create_agents_messages.md`。
