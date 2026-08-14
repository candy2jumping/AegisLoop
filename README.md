# AegisLoop SOC AgentTeams 最小 Demo

这是一个面向初赛提交的最小可运行 demo。用户只提供弱信号现象和少量初始告警，AgentTeams 中的 7 个业务 LLM Agent 通过 HTTP mock 工具网关主动查询 SIEM、EDR、NDR、AD、DB 审计、威胁情报、证据与工单数据；创建 Team 时由 manager 创建独立 TeamLeader Worker `aegis-leader` 负责调度协作，在 Write Zone + ARG/Blast 闸控下完成「零人工研判 + 受控自愈」闭环。Human `soc-lead` 仅介入 **L2/L4** 与 Tier-0 审批（L3 suggest_only）。

完整运行手册见 [at/AGENTTEAMS_RUNBOOK.md](at/AGENTTEAMS_RUNBOOK.md)。正式演示走 AgentTeams UI（见下方启动步骤）。

**初赛提交包即本文件夹（`aegisloop-demo/`）。**

## Demo 要证明什么

风险定级 / plan schema / ECP.grade 以 [contracts/ALIGNMENT.md](contracts/ALIGNMENT.md) 为唯一真相源。

1. AgentTeams 可创建并管理 **9 个角色语义**：独立 TeamLeader `aegis-leader` + 7 业务 Worker + Human `soc-lead`。
2. **13 个 Skill**（含 ARG/Blast、claim-provenance、ECP 裁决、lesson-settle 等）可内联进创建消息，Worker 不依赖宿主机目录。
3. **Write Zone**：只有 `executor` 写；业务 Worker 不得直 `@executor`；仅 `aegis-leader` 在闸后可触达。
4. **ARG / Blast** 前闸：高风险与 Tier-0 强制 `soc-lead`；低风险进入自动化执行语义。
5. **ECP** 结构化结论传递 + 证据回执溯源；收尾 **lesson settle** 沉淀可复用知识。

## Demo 场景

| 场景 ID | Case | 类型 | 预期处置 |
| --- | --- | --- | --- |
| `lateral_movement_t1021` | `CASE-2001` | 财务终端凭证窃取 → SMB 横向移动 → 只读账号拖库（T1003→T1021→T1078） | `isolate_host=L4` 强制人审；`block_ip=L2` 审批；`block_domain=L3` 仅建议；`hits_tier0=true` 升 L4；泄露触发合规；closer 验证并写 LESSON |

## 核心 Agent

| Agent | 作用 | 关键 Skill | 工具 |
| --- | --- | --- | --- |
| Aegis TeamLeader | 创建 Team 时由 manager 生成的独立 Worker，名称固定为 `aegis-leader` | 声明：`arg-risk-guard`, `blast-radius-guard`, `claim-provenance` | 调度；闸后唯一可 `@executor` |
| triage | 弱信号聚簇升格 | `case-cluster`, `udb-sanitize` | `mock_siem`, `mock_ticket`, `mock_udb` |
| hunter | 固证取证 | `forensic-snapshot`, `udb-sanitize` | `mock_edr`, `mock_evidence.snapshot` |
| correlator | 跨源实体关联 | `entity-correlate`, `actor-profile-rag`, `udb-sanitize` | `mock_ndr`, `mock_ad`, `mock_intel`, `mock_dbaudit`, `mock_siem`, `mock_udb` |
| verdict | 假设竞争裁决（ECP） | `hypothesis-verdict`, `claim-provenance`, `actor-profile-rag`, `udb-sanitize` | `mock_evidence.get_receipt`, 只读补充查询 |
| planner | 分级处置方案 | `containment-plan`（声明 ARG/Blast） | `mock_ticket.get_case` |
| executor | Write Zone 唯一写者 | ARG/Blast 前闸, `compliance-notify` | `mock_contain.*`, `mock_ticket` |
| closer | 验证 / TEL / lesson | `claim-provenance`, `residual-verify`, `lesson-settle` | `mock_probe.*`, `mock_evidence` seal/export, `mock_knowledge.*`, `mock_intel.upsert_profile_index` |
| soc-lead（Human） | L2/L4 与 Tier-0 审批（L3 suggest_only） | — | 审批语义，不直连生产写 |

## 最短运行流程

1. 启动 mock 工具网关：

```bash
cd <DEMO_DIR>
python3 tools/mock_tool_server.py --host 0.0.0.0 --port 18089
```

2. 安装 AgentTeams，并按安装器引导完成 LLM/API Key/端口/运行时配置：

```bash
bash <(curl -sSL https://higress.ai/hiclaw/install.sh)
```

3. 找到 Docker 容器访问工具网关的地址：

```bash
docker inspect -f '{{range .NetworkSettings.Networks}}{{println .Gateway}}{{end}}' hiclaw-manager
docker exec -it hiclaw-manager curl http://<GATEWAY_IP>:18089/health
```

如果 manager 容器名不是 `hiclaw-manager`，按运行手册第 4 步先确认实际容器名。

4. 在 Element Web 打开 `manager` 房间，把 [at/create_agents_messages.md](at/create_agents_messages.md) 里的 `http://172.18.0.1:18089` 替换成 `http://<GATEWAY_IP>:18089` 后，将完整创建请求复制给 `manager`。创建请求已要求所有 Worker 使用 `qwenpow`（`copow`/`QwenPaw`）运行时，并由 `manager` 严格串行创建 7 个业务 Worker；创建 Team 时再生成独立 TeamLeader Worker `aegis-leader`。

5. 在 Element Web/Matrix 会话列表中找到名称以 `Team` 开头、对应 `aegisloop-soc` 的 Team 房间。进入房间后，在输入框先 `@<team_leader_name>` 选中带 leader 名字的成员，再把 [at/run_demo_task_message.md](at/run_demo_task_message.md) 中的主任务复制到这条 @ 消息里发送。SOC 任务不要发给 `manager`。

## 后续替换点

| 当前内容 | 后续替换方向 |
| --- | --- |
| HTTP mock 工具网关 | 真实 MCP Server 或 Higress MCP 代理 |
| `scenarios/*.json` | 真实 SIEM/EDR/NDR/AD/审计/情报/工单数据源 |
| 7 个业务 Worker 的内联 AgentSpec/Skill | Nacos AI Registry 中的 Prompt、Skill、AgentSpec、AgentTeam Spec |
| `skills/*/SKILL.md` 评审材料 | 发布到 Nacos AI Registry 或 AgentTeams Skill Registry，由 Worker 按版本/标签动态加载 |
