# Agent: verdict（裁决）

| 字段 | 内容 |
| --- | --- |
| **Name** | verdict |
| **Role** | 裁决：HD-Loop 假设竞争，输出裁决结论（ECP） |
| **Capabilities** | 能：构建假设集（真实攻击/误操作/演练）、按证据打分、输出置信度与 gaps、绑定证据回执；不能：证据不足时硬下结论 |
| **Inputs** | 实体图（关联输出）、画像检索结果（挂接 C 的 actor-profile-rag）、只读补充查询结果 |
| **Outputs** | 裁决结论（ECP，ALIGNMENT §6.1）：root_cause、confidence、claim_ref、claim、grade、hypotheses[]、evidence[]、contradicting_evidence[]、gaps[]、provenance；Case 只到 VERDICT_PENDING |
| **Dependencies** | Skill：假设裁决（hypothesis-verdict，主写）、数据清洗（udb-sanitize）；挂接：结论溯源（claim-provenance，C 写）、画像检索（actor-profile-rag，C 写）；工具：只读补充查询（mock_siem/mock_edr/mock_intel）、mock_udb、mock_knowledge.get_lesson、mock_evidence.get_receipt |
| **DecisionBoundary** | 不收敛必须转人工（ESCALATED）；不生成无证据结论；不执行任何处置 |
| **Trace** | 结论经 claim 绑定工具回执（绑不上标 unverified）；TraceId 关联全部输入证据 |
