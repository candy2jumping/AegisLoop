# A 线研判链手跑报告 · CASE-2001

- 场景：lateral_movement_t1021（T1003 → T1021 → T1078）
- 时间：09:01 收到弱信号 → 09:05 出裁决结论（模拟）
- 说明：本报告为数据链路手跑，展示各 Agent 查询、发现与产出

## ① 分诊 triage
- 收到弱信号：弱信号：财务终端 10.20.3.17 在 02:09 向域控 10.0.0.8 发起 SMB 连接（ADMIN$），且该主机 02:06 出现针对 lsass.exe 的异常进程访问。单条不够立案，跨源同时出现则建议升格调查。
- 查询 mock_siem.list_alerts：命中 6 条可疑记录
  - 02:03 VPN 登录成功，IP 首次出现
  - 02:09 财务终端访问域控管理共享
  - 02:09 新服务安装（PsExec 特征）
  - 02:10 网络登录（PsExec 会话）
  - 02:07 计划任务创建（伪装系统更新）
- 建单：CASE-2001（状态 NEW）
- **产出 事件简报**：claim=疑似横向移动+凭据访问，优先级 high，涉及 zhang-san / 10.20.3.17 / 10.2.3.15

## ② 取证 hunter
- 查询 mock_edr.process_tree(10.20.3.17)：5 条；process_access(lsass)：1 条；file_events：1 条
  - lsass 访问 GrantedAccess=0x1F0FFF
- 固证快照：2 条证据已存哈希
- **产出 证据快照**：claim=T1003 凭据转储成立；gaps：lsass.dmp 已删除

## ③ 关联 correlator
- mock_ndr.flows：5 条（含到 203.0.113.78:443 的 C2 回连）
- mock_ad.auth_log(zhang-san)：4 条（02:03 VPN 登录，IP 首次出现）
- mock_intel.lookup(203.0.113.78)：命中 C2，置信度 0.87
- mock_dbaudit：users 表查询日志 4 条；基线 180 行/天，实际 3,600,000 行
- **产出 实体图**：外部 IP 203.0.113.78 → zhang-san → 财务终端 → 报表服务器 → orders 库；可达性成立

## ④ 裁决 verdict
- HD-Loop 假设竞争：H1=0.87 / H2=0.09 / H3=0.04

```json
{
  "root_cause": "attack",
  "claim": "外部入侵：T1003 凭据窃取 → T1021 横向移动 → T1078 身份滥用拖库",
  "confidence": 0.87,
  "claim_ref": "",
  "grade": "trusted",
  "hypotheses": [
    {
      "id": "H1",
      "type": "attack",
      "desc": "真实外部攻击",
      "confidence": 0.87
    },
    {
      "id": "H2",
      "type": "misop",
      "desc": "运维误操作",
      "confidence": 0.09
    },
    {
      "id": "H3",
      "type": "drill",
      "desc": "红队演练",
      "confidence": 0.04
    }
  ],
  "evidence": [
    {
      "id": "edr:proc_procdump_020607",
      "strength": "strong",
      "ref": "mock_evidence"
    },
    {
      "id": "ndr:flow_c2_021022",
      "strength": "strong",
      "ref": "mock_ndr"
    },
    {
      "id": "dbaudit:query_users_021805",
      "strength": "strong",
      "ref": "mock_dbaudit"
    }
  ],
  "contradicting_evidence": [],
  "gaps": [
    "报表服务器无进程级网络日志",
    "lsass.dmp 已删除"
  ],
  "provenance": {
    "agent": "verdict",
    "ts": "2026-07-28T09:05:00+08:00"
  }
}
```

## 附：Trace 调用记录 12 条
- mock_siem.get_seed_signal args={}
- mock_siem.list_alerts args={'severity': None}
- mock_ticket.create_case args={'seed': None}
- mock_edr.process_tree args={'host': '10.20.3.17', 'since': None, 'until': None}
- mock_edr.process_access args={'target': 'lsass.exe', 'host': None}
- mock_edr.file_events args={'host': '10.20.3.17'}
- mock_evidence.snapshot args={'refs': ['edr:proc_procdump_020607', 'edr:access_lsass_020608']}
- mock_ndr.flows args={'src': None, 'dst': None, 'port': None, 'since': '2026-07-28T02:00:00+08:00', 'until': '2026-07-28T09:00:00+08:00'}
- mock_ad.auth_log args={'user': 'zhang-san', 'ip': None, 'since': None, 'until': None}
- mock_intel.lookup args={'value': '203.0.113.78'}
- mock_dbaudit.query_log args={'user': 'report_reader', 'table': None, 'since': None, 'until': None}
- mock_dbaudit.baseline args={'user': 'report_reader', 'table': 'users'}