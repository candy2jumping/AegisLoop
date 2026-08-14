# Element 群聊实跑记录 · CASE-2001（A 线首跑）

- 日期：2026-08-07
- 环境：HiClaw（Element Web `http://127.0.0.1:18088`），团队 `aegis-loop`
- 团队构成：aegis-leader（总控）+ triage（分诊）+ hunter（取证）+ correlator（关联）+ verdict（裁决）
- 剧本：`lateral_movement_t1021`（T1003 凭据窃取 → T1021 横向移动 → T1078 身份滥用拖库）
- 工具调用：83 次（见 `element-live-run-trace.json`）

## 实跑过程（群聊接力）

| 环节 | Agent | 产出 | 案件状态 |
| --- | --- | --- | --- |
| 1 分诊 | triage | 事件简报 ECP（case_id、claim、evidence refs、gaps） | NEW → TRIAGED |
| 2 取证 | hunter | 证据快照（snapshot_id、哈希、T1003 成立） | → INVESTIGATING |
| 3 关联 | correlator | 实体图（nodes、ATT&CK 映射、identityReachability） | → VERDICT_PENDING |
| 4 裁决 | verdict | 裁决结论（H1 真实攻击 0.90 / H2 0.07 / H3 0.03） | → PLANNED（移交 B 线） |

总控（aegis-leader）按 DAG 逐环节派发、逐份验收 ECP，最终完成项目归档并向管理员汇报。

## 四项框架能力验证

1. **Todo 追踪**：总控以 DAG 项目（分诊 → 取证 → 关联 → 裁决）跟踪四个子任务，房间内可见任务时间线。
2. **心跳**：总控配置 30 分钟心跳，团队 Leader 自动汇报进度。
3. **状态机**：案件状态全程推进 NEW → TRIAGED → INVESTIGATING → VERDICT_PENDING → PLANNED，非法迁移被 mock 网关拒绝。
4. **记忆/文件传输**：ECP 经共享文件柜（MinIO `shared/`）传递；裁决发现本地结论被覆盖后，从文件柜恢复了完整版 `result.md`（共享存储兜底生效）。

## 运行证据位置

- 群聊转写：Element 团队房间（aegis-loop）与总控 DM
- 最终结论：MinIO `shared/projects/aegis-case2001-20260807-114653/result.md`
- 工具调用流水：`element-live-run-trace.json`（83 条）
