# Public Release Readiness Gate

本文件检查仓库公开发布和论文 artifact 附件的基础卫生状态，重点是 API key 泄露、`.env` 管理、复现入口和开源元数据。它只扫描 Git 已跟踪文件，不读取或打印 `.env` 内容。

## 总览

- Blockers: 0
- Major warnings: 0
- Minor warnings: 1
- Safe for public artifact release: True

## 检查明细

| Check | Category | Severity | Pass | Status | Evidence |
| --- | --- | --- | --- | --- | --- |
| tracked_secret_scan | security | blocker | True | pass | no tracked secret-like lines found |
| env_file_not_tracked | security | blocker | True | pass | .env tracked=False |
| gitignore_covers_env | security | major | True | pass | .gitignore contains `.env` |
| env_example_uses_placeholders | reproducibility | major | True | pass | .env.example has provider placeholders |
| readme_links_submission_gate | paper_artifact | major | True | pass | README links submission readiness gate |
| license_file_present | open_source | minor | False | minor | license files=none |

## 当前动作

- `license_file_present`：正式开源前补充 LICENSE；内部实验仓库可暂缓。

## 论文使用判断

- 若 blocker=0，可以把当前仓库作为内部复现 artifact 或公开仓库继续整理。
- 若要匿名投稿，仍需要根据会议要求移除作者、账号、仓库 URL 等身份信息；该检查不自动匿名化论文文本。
