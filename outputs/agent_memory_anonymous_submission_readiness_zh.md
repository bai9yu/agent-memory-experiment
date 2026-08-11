# Anonymous Submission Readiness Audit

本文件检查当前补充材料候选是否适合匿名投稿。它只扫描 supplementary package manifest 中 `include_in_current_supplement=True` 的 artifact，不扫描内部审查 gate 或本地中间文件。

## 总览

- Manifest source: `outputs/agent_memory_supplementary_package_manifest.csv`
- Checks: 5
- Blockers: 0
- Anonymous package ready: True

## 检查明细

| Check | Category | Status | Evidence | Action |
| --- | --- | --- | --- | --- |
| manifest_exists | input | pass | manifest_rows=30, include_rows=12 | 先生成 supplementary package manifest。 |
| blocked_artifacts_excluded | claim_boundary | pass | blocked_artifacts_included=0 | 关闭外部 embedding / 人审 blocker 前，不要把 blocked artifact 放入 supplement。 |
| internal_gates_not_in_supplement | packaging_boundary | pass | internal_gate_artifacts_included=0 | 将 internal_review_gate 保留在仓库/rebuttal 材料中，不作为匿名 supplement 主包。 |
| included_files_exist | file_integrity | pass | missing= | 修复 manifest 中指向的缺失 artifact。 |
| included_files_anonymous | anonymization | pass | no identity-like findings in included artifacts | 匿名投稿前移除作者路径、仓库 URL、邮箱、API key 赋值和本地 Codex 路径。 |

## 使用边界

- 该审计只能检查当前 artifact 文本中常见身份线索；最终仍需按目标会议模板检查作者栏、致谢、补充材料封面和文件元数据。
- `Anonymous package ready=True` 不代表实验 blocker 已解除，只代表当前可纳入 supplement 的文件未发现常见身份泄露。
- 若目标会议允许非匿名仓库，本审计仍可作为公开发布前的路径/身份卫生检查。
