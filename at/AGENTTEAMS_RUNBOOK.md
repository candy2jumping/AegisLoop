# 使用 AgentTeams 运行 AegisLoop SOC Demo

这份手册面向第一次试运行 demo 的参赛者。运行机器可以是本地 Windows/Mac、Linux 服务器或云主机；mock 工具网关和 AgentTeams 都部署在同一台机器上。

核心流程：

1. 启动 HTTP mock 工具网关（端口 `18089`）。
2. 安装 AgentTeams，并按安装器引导完成 LLM 配置。
3. 找到 Docker Worker 可访问的工具网关地址。
4. 在 `manager` 房间串行创建 7 个业务 Worker，并在创建 Team 时生成独立 TeamLeader Worker `aegis-leader`。
5. 在 Matrix 会话列表中进入名称以 `Team` 开头、对应 `aegisloop-soc` 的 Team 房间，通过 `@<team_leader_name>` 发送 CASE-2001 任务。

## 1. 准备运行机器

需要：

- Docker 或兼容运行时。
- Python 3。
- 一个 AgentTeams 可使用的 LLM API Key。

检查：

```bash
python3 --version
docker --version
```

Windows 可用 `python --version`。如果没有 Docker，按系统查看官方安装文档：

| 系统 | 官方安装入口 |
| --- | --- |
| Mac | https://docs.docker.com/desktop/setup/install/mac-install/ |
| Ubuntu | https://docs.docker.com/engine/install/ubuntu/ |
| Debian | https://docs.docker.com/engine/install/debian/ |
| CentOS | https://docs.docker.com/engine/install/centos/ |
| RHEL | https://docs.docker.com/engine/install/rhel/ |
| 其他 Linux | https://docs.docker.com/engine/install/ |
| Windows | https://docs.docker.com/desktop/setup/install/windows-install/ |
| Linux 免 sudo 后置配置 | https://docs.docker.com/engine/install/linux-postinstall/ |

安装完成后验证：

```bash
docker run hello-world
```

## 2. 启动 Mock 工具网关

在一个终端中启动服务，并保持它运行：

```bash
cd <DEMO_DIR>
python3 tools/mock_tool_server.py --host 0.0.0.0 --port 18089
```

`<DEMO_DIR>` 为本仓库的 `aegisloop-demo` 目录。另开一个终端验证：

```bash
curl http://127.0.0.1:18089/health
curl http://127.0.0.1:18089/scenarios
curl -X POST http://127.0.0.1:18089/tools/lateral_movement_t1021/mock_siem.list_alerts \
  -H 'Content-Type: application/json' \
  -d '{}'
```

可选：确认处置语义可用（写动作仅应由 executor 在闸后调用）：

```bash
curl -X POST http://127.0.0.1:18089/tools/lateral_movement_t1021/mock_contain.isolate_host \
  -H 'Content-Type: application/json' \
  -d '{"host":"finance-ws-17"}'
```

这一步只验证宿主机本机访问。后面还需要验证 Docker 容器访问。

## 3. 安装 AgentTeams

执行安装脚本：

```bash
bash <(curl -sSL https://higress.ai/hiclaw/install.sh)
```

安装器会引导完成语言、安装模式、版本、LLM、API Key、API 联通性测试、Embedding、Manager/Worker 运行时、端口、域名、E2EE、Docker API 安全代理和共享目录等配置。按引导操作即可，关键是看到模型 API 联通性测试通过。

可参考的 demo 样例：

| 引导项 | 样例值 |
| --- | --- |
| 语言 | 中文 |
| 版本 | 最新稳定版，例如 `v1.1.2` |
| LLM | 使用已有 API Key 的模型服务，例如 `qwen3.7-plus` |
| API 联通性 | 必须测试通过 |
| Embedding | 可启用；失败后接受自动禁用也可以 |
| Manager/Worker 运行时 | `qwenpow`（`copow`/`QwenPaw`） |
| Element Web 端口 | 默认 `18088` |
| Matrix E2EE | 建议禁用 |
| Docker API 安全代理 | 建议启用 |
| 共享主机目录 | 可保持默认；本 demo 不依赖共享目录读取文件 |

安装完成后检查：

```bash
docker ps | grep hiclaw
```

打开 Element Web：

```text
http://<AGENTTEAMS_HOST>:18088
```

在运行机器本机访问时通常是：

```text
http://127.0.0.1:18088
```

安装配置通常保存到当前用户 HOME 下的 `hiclaw-manager.env`，后续需要调整模型或端口时从这里排查。

## 4. 确定工具网关地址

Worker 在 Docker 容器中运行，不能直接使用 `http://127.0.0.1:18089` 访问宿主机上的 mock 工具网关。单机 Docker 部署优先使用 `hiclaw-manager` 所在网络的 gateway 地址。

先找到 manager 容器名：

```bash
docker ps --format '{{.Names}}' | grep manager
```

如果容器名是 `hiclaw-manager`，查看 gateway：

```bash
docker inspect -f '{{range .NetworkSettings.Networks}}{{println .Gateway}}{{end}}' hiclaw-manager
```

假设输出是 `172.18.0.1`，则 `<MOCK_TOOL_BASE_URL>` 使用：

```text
http://172.18.0.1:18089
```

从容器内验证：

```bash
docker exec -it hiclaw-manager curl http://172.18.0.1:18089/health
docker exec -it hiclaw-manager curl -X POST http://172.18.0.1:18089/tools/lateral_movement_t1021/mock_siem.list_alerts \
  -H 'Content-Type: application/json' \
  -d '{}'
```

如果 health 返回 `{"ok": true, ...}`，说明后续 Worker 可以访问工具网关。

`host.docker.internal` 只在部分 Docker Desktop 环境可用。如果容器里报 `Could not resolve host: host.docker.internal`，就使用上面的 gateway 地址。

## 5. 创建 Agent 和 Team

进入 Element Web 的 `manager` 房间。

打开 [create_agents_messages.md](create_agents_messages.md)，先把文件中的 `http://172.18.0.1:18089` 全部替换为第 4 步确认的地址（若 gateway 恰好是 `172.18.0.1` 则可不动）。

然后将 [create_agents_messages.md](create_agents_messages.md) 中“复制到 Manager 的完整创建请求”整段发送给 `manager`。这段请求已经包含 7 个业务 Worker 和 1 个 Team 的完整定义，并明确要求：

1. 所有 Worker 使用 `qwenpow`（`copow`/`QwenPaw`）运行时。
2. `manager` 必须逐个创建 Worker，不能并行创建。
3. 业务 Worker 顺序：`triage → hunter → correlator → verdict → planner → executor → closer`。
4. 必须确认前一个 Worker 创建成功且正常运行后，再创建下一个 Worker。
5. 创建 Team 时必须生成新的独立 Worker `aegis-leader` 作为 TeamLeader，不能把 7 个业务 Worker 中的任何一个直接指定为 leader。

Worker 初始化会拉起运行时并写入依赖，低规格机器上并发创建可能造成高 I/O 消耗甚至阻塞。因此不要手动把 Worker 创建任务拆开并并行发送。

注意：

- `manager` 只负责创建和管理。
- SOC 任务后续发给 Matrix 会话列表中名称以 `Team` 开头、对应 `aegisloop-soc` 的 Team 房间，并在消息里 `@<team_leader_name>`，不发给 `manager`。
- 7 个业务 Worker 的 AgentSpec、Skill 和工具契约已经内联在创建消息中。
- Worker 不需要读取宿主机上的 `agents/...` 或 `skills/*/SKILL.md` 文件。
- `skills/*/SKILL.md` 主要用于评审、PPT/文档追溯和后续 Registry 替换。
- Human：`soc-lead` 负责 L2/L4 / Tier-0 审批语义。

## 6. 发送 SOC 任务

打开 [run_demo_task_message.md](run_demo_task_message.md)。

在 Element Web/Matrix 会话列表中找到名称以 `Team` 开头、对应 `aegisloop-soc` 的 Team 房间。通常 `manager` 在创建完成摘要里会告诉你 Team 房间名称和 `team_leader_name`。

进入 Team 房间后，在输入框先输入并选中 leader mention：

```text
@<team_leader_name>
```

然后把主任务（CASE-2001 / `lateral_movement_t1021`）复制到这条 @ 消息里发送。一次只发一则 Case，避免并发调度干扰工具状态。

如果你只看到 `manager` 房间，可以先问：

```text
aegisloop-soc 对应的 Team 房间在哪里？请告诉我 Matrix 会话列表中名称以 Team 开头的房间名称，以及需要 @ 的 team_leader_name（应是 aegis-leader）。
```

任务消息只包含弱信号现象和少量初始告警。完整证据、关联、裁决与处置应由 Agent 通过 HTTP mock 工具网关主动查询。

若进入审批待决，用 [run_demo_task_message.md](run_demo_task_message.md) 中的 `soc-lead` 审批短消息回复。

## 7. 判断是否跑通

`CASE-2001 / lateral_movement_t1021` 应包含：

| 检查项 | 期望信号 |
| --- | --- |
| 分诊 | 财务终端 SMB→域控 + lsass 访问弱信号升格为 Case |
| 取证 | `procdump64.exe -ma lsass.exe`、LSASS `0x1F0FFF`、lsass.dmp 已删记入 gaps |
| 关联 | VPN/异地 IP `203.0.113.78`、PsExec→`report-srv-15`、C2、report_reader 拖库偏离基线 |
| 裁决 | claim 指向 T1003→T1021→T1078；H1 高置信；证据可回执 |
| 方案 | isolate_host=L4 人审；block_ip=L2 审批；block_domain=L3 仅建议；hits_tier0 升 L4；泄露触发合规 |
| 闸控 | ARG/Blast 结果可见；Worker 未直 @executor；仅 aegis-leader 放行 |
| 执行 | mock_contain / ticket 写动作有回执；高危等待 soc-lead |
| 收尾 | residual-verify、TEL pack、LESSON-2001 proposed、Case→CLOSED |

如果团队要求你人工提供完整 SIEM/EDR/NDR 证据，可以提醒：

```text
请通过已配置的 HTTP mock 工具网关主动查询，不要让我人工收集完整证据。
```

## 8. 排障备忘

| 现象 | 排查 |
| --- | --- |
| Worker 调工具失败 / connection refused | 确认 mock 监听 `0.0.0.0:18089`；用 gateway IP 而非 `127.0.0.1`；在 manager 容器内 curl health |
| `host.docker.internal` 解析失败 | 改用 `docker inspect` 得到的 gateway，例如 `http://172.18.0.1:18089` |
| 创建卡住或容器频繁重启 | 确认串行创建；降低并行；检查磁盘/I/O；确认运行时为 qwenpow |
| Team 房间找不到 | 问 manager 要 `aegisloop-soc` 对应 Team 房间名；会话列表中名称通常以 `Team` 开头 |
| 任务发给 manager 无业务推进 | 改发到 Team 房间并 `@aegis-leader` |
| 业务 Worker 试图 @executor | 提醒 Write Zone：仅 aegis-leader 闸后可 @executor |
| 审批卡住 | 用 `soc-lead` 审批短消息 `decision: approve` |
| 状态迁移被拒 | 检查 `mock_ticket.update_case_status` 是否按主链推进（见 `tools/mock_tools.py`） |
| scenario 404 | `scenario_id` 必须是 `lateral_movement_t1021`；先 curl `/scenarios` |

## 后续替换点

| 当前内容 | 后续替换方向 |
| --- | --- |
| HTTP mock 工具网关 | 真实 MCP Server 或 Higress MCP 代理 |
| `scenarios/*.json` | 真实 SIEM/EDR/NDR/AD/DB 审计/情报/工单数据源 |
| `at/create_agents_messages.md` 中 7 个业务 Worker 的内联 AgentSpec/Skill | Nacos AI Registry 中的 Prompt、Skill、AgentSpec、AgentTeam Spec |
| `skills/*/SKILL.md` 评审材料 | 发布到 Nacos AI Registry 或 AgentTeams Skill Registry，由 Worker 按版本/标签动态加载 |
