# AegisLoop —— GOAI 大赛 赛道一「新智基座｜Agent Infra」提交代码包

> 本仓库是初赛「可执行 AgentTeams 代码包」交付物，基于 **AgentTeams（原名 HiClaw，github.com/alibaba/hiclaw）** 多智能体框架构建。
> 项目定位：大促保障与入侵猎捕双场景下的**受控自愈**多 Agent 协同系统（9 个职能 Agent + 13 个 Skill + 5 个 Infra 机制）。
>
> 配套交付物（不在本仓库，单独提交）：**作品简介**（≤500 字）、**方案 PPT**（官方 19 页模板）。
> 本指南把赛事手册 §5.2「若提交代码包应包含」的 5 项要求逐一映射到本仓库文件，方便评委/组委会直接核验。

---

## 仓库目录速查（一句话说明每个目录）

| 目录/文件 | 一句话作用 |
|---|---|
| `at/` | **★ 运行入口**：部署手册、创建 9 个 Agent 的消息模板、任务消息、Team 规格、环境变量样例 |
| `agents/` | 9 个职能 Agent 的声明与实现（aegis-leader + 7 Worker + Human soc-lead） |
| `souls/` | 9 个 Agent 的人设（SOUL） |
| `skills/` | 13 个 Skill 的声明与实现 |
| `contracts/` | 冻结契约：ARG 风险分级、ECP 证据分级、10 态状态机、Agent 间交接字段 |
| `tools/` | Mock 工具网关：本地可跑，无需真实安全设备 |
| `scenarios/` | 样例输入：横向移动攻击场景剧本 |
| `domain/` | Tier-0 关键资产表与领域类型定义 |
| `evidence/` | **★ 平台 A 线端到端实跑证据**（room-transcript.json，655 条对话） |
| `evidence-supplement/prototype-bline/` | **★ B 线离线原型补充证据**（已如实分区标注） |
| `knowledge/lessons/` | 经验沉淀输出样例 |
| `schemas/` | IO Schema 定义 |
| `docs/` | 设计文档与架构说明 |
| `README.md` | 项目总说明（队友汇总，未改动） |
| `SUBMISSION_GUIDE.md` | 本文件：提交导航 + 官方要求映射 |
| `LICENSE` | MIT 开源协议 |

---

## 一、赛事手册 §5.2 五项要求 → 本仓库文件映射

### 1. 运行入口（如何把它跑起来）
| 文件 | 作用 |
|---|---|
| `at/AGENTTEAMS_RUNBOOK.md` | **完整部署运行手册**：Docker 起平台 → 建 Team → 建 9 个 Agent/Worker → 发起处置任务 |
| `at/create_agents_messages.md` | 在平台对话中创建 9 个 Agent（Worker）的消息模板 |
| `at/run_demo_task_message.md` | 发起一次处置任务（Case-2001 横向移动）的消息模板 |
| `at/team_spec.json` | Team 规格声明（9 Worker + 1 Human approver），可 `kubectl apply` 式导入 |

### 2. 依赖说明
| 文件 | 作用 |
|---|---|
| `README.md` | 项目总说明（Agent/Skill 清单、目录结构） |
| `at/AGENTTEAMS_RUNBOOK.md` | 运行依赖：Docker 环境 + 一个 LLM API Key（通义千问/OpenAI）+ 安装脚本 |
| `at/agentteams.env.example` | 环境变量样例（API Key 占位，需自行填真实值，**真实密钥不进仓库**） |
| `tools/` | 本地 Mock 工具网关（`mock_tool_server.py` + `mock_tools.py` + `tool_catalog.json`），无需真实安全设备 |

### 3. 配置文件
| 文件 | 作用 |
|---|---|
| `at/team_spec.json` | Team/Agent 规格 |
| `at/agentteams.env.example` | 环境配置样例 |
| `contracts/ALIGNMENT.md` | **冻结契约**：ARG 风险分级、ECP 证据分级、10 态状态机、Agent 间交接字段全锁定 |
| `domain/tier0_assets.json` | Tier-0 关键资产表（用于爆炸半径自动升级） |

### 4. 样例输入输出
| 文件 | 作用 |
|---|---|
| `scenarios/lateral_movement_t1021.json` | **输入样例**：T1021 横向移动攻击场景剧本（含告警、资产、上下文） |
| `evidence/room-transcript.json` | **输出样例**：平台端到端实跑的完整对话轨迹（655 条消息） |
| `knowledge/lessons/LESSON-2001.json` | **输出样例**：经验沉淀（LESSON）结构化产物 |

### 5. 运行证据
| 文件 | 作用 |
|---|---|
| `evidence/room-transcript.json` | **平台端到端实跑记录**（A 线研判链：triage→hunter→correlator→verdict，655 条对话） |
| `evidence/element-live-run-20260807.md` | Element Web 平台实跑截图/说明 |
| `evidence/aegis-line-run.md` | A 线研判链手跑报告 |
| `evidence-supplement/prototype-bline/` | **B 线处置闭环离线补充证据**（见下节说明） |

---

## 二、B 线处置闭环的证据状态（如实披露）

赛事评分中「多 Agent 协同 25% + 工程安全 20%」高度依赖 B 线（受控自愈闭环）。
当前状态**如实**说明如下，避免虚标：

- **A 线（研判链）**：已在 AgentTeams/HiClaw 平台端到端实跑，见 `evidence/room-transcript.json`。
- **B 线（处置闭环：planner→前闸→soc-lead 人审→executor→closer→lesson）**：
  - 已在 `contracts/ALIGNMENT.md`、`agents/`、`skills/` 中**完整设计**；
  - 已在 `evidence-supplement/prototype-bline/` 的**离线原型**中跑通（含 `isolate_host`/`block_ip` 执行、`AWAITING_APPROVAL` 人审闸、`rollback` 回滚、`compliance` 合规工单、`LESSON` 沉淀、`resolved=true`）；
  - **平台侧 B 线实跑待补充**（需 Docker + LLM API Key 环境，约 30 分钟可补一次完整 `room-transcript`）。

> 我们未将离线原型日志伪称为平台实跑；`evidence/` 与 `evidence-supplement/` 已明确分区标注。

---

## 三、目录速览（队友汇总包，未改动）

```
AegisLoop-repo/
├── README.md                     # 项目运行说明（队友汇总，未改动）
├── SUBMISSION_GUIDE.md           # 本文件：提交说明 + 官方要求映射
├── LICENSE                       # MIT 开源协议
├── .gitignore
├── agents/                       # 9 个 Agent 定义（aegis-leader/triage/hunter/correlator/verdict/planner/executor/closer/soc-lead）
├── souls/                        # 各 Agent 人设（SOUL）
├── skills/                       # 13 个 Skill 说明书
├── at/                           # ★运行入口：部署手册/建Agent消息/任务消息/team_spec.json/环境样例
├── contracts/                    # 冻结契约 ALIGNMENT.md（ARG/ECP/状态机/交接字段）
├── tools/                        # Mock 工具网关（本地可跑，无需真实设备）
├── scenarios/                    # 样例输入：横向移动场景剧本
├── domain/                       # Tier-0 资产表
├── knowledge/lessons/            # 经验沉淀输出样例
├── schemas/                      # IO schema（claim 等）
├── docs/                         # A 线 ECP 与状态机说明
├── evidence/                     # ★运行证据：平台实跑（A 线）
└── evidence-supplement/prototype-bline/   # ★B 线离线补充证据（非平台实跑）
```

---

## 四、合规与开源披露（红线 §13.7）

- **开源协议**：MIT（见 `LICENSE`）。
- **第三方依赖**：AgentTeams/HiClaw（Apache-2.0 系，见官方仓库）；LLM 推理使用通义千问（商业 API，需自行 Key）。
- **数据来源**：运行证据基于 **Mock 网关 + 动态注入靶场** 生成，**不含任何真实企业数据**；样例场景为自建剧本。
- **未来规划（合规合法）**：拟在合规授权与企业脱敏前提下，接入真实企业环境用于训练与评测，确保合法合规。
