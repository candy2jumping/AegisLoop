# 离线原型 B 线处置闭环验证证据（补充材料）

> **重要说明：本目录下的日志来自本地 Python 离线原型（`goai-agent-infra` 仓库的 `main.py`），**
> **不是 AgentTeams/HiClaw 平台的实跑记录。** 平台实跑证据见上级 `../evidence/` 目录
> （`room-transcript.json` 等，覆盖 A 线研判链）。本目录用于**补充证明 B 线处置闭环的逻辑已跑通**，
> 因为平台侧 B 线实跑待补充（需 Docker + LLM API Key 环境）。

## 内容

| 文件 | 场景 | 证明的 B 线动作 |
|---|---|---|
| `run_security_ir.log` | security_ir / lateral_movement | 人审闸 `AWAITING_APPROVAL` → 执行 `isolate_host`(6)/`block_ip`(3) → 回滚 `rollback`(3) → 合规 `compliance`(2) → 收尾 `lesson`(2) → `resolved=true` |
| `run_ecommerce_promo.log` | ecommerce_promo / promo_spike | 段级 `scale_out` 扩容经人审放行 → 收尾闭环 → `resolved=true` |

## 如何复现

```bash
# 依赖：Python 3.13 + pyyaml（pip install pyyaml）
python main.py --scenario security_ir   --attack lateral_movement
python main.py --scenario ecommerce_promo --attack promo_spike
```

输出为确定性逻辑原型（不含 LLM 推理），用于验证五机制（ECP/ARG/TEL/UDB/HD-Loop）
与 Write Zone 状态机在处置闭环中的行为，不替代平台 LLM 实跑。
