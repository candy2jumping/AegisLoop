# LESSON-2001

- **Case**: CASE-2001
- **trace_id**: `tr_case2001_demo`
- **Trigger**: 财务终端向域控 SMB + lsass 访问
- **ATT&CK**: T1003 → T1021 → T1078
- **rule_suggestion**: 同主机凭据访问 + 域控 SMB → 自动升格 Case 并优先拉取 EDR 进程树；单账号单表查询量偏离历史基线 10 倍以上 → 触发异常告警
- **containment_hint**: L4 isolate_host (soc-lead); L2 block_ip / disable_account (soc-lead); L3 block_domain suggest_only
- **Status**: proposed（需 soc-lead 批准后 active）
