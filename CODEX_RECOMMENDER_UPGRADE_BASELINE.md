# SoundMind 推荐系统升级基线记录

记录时间：2026-06-18

## Git 状态

- 当前目录是 Git 仓库。
- 当前分支：`main`
- 工作区存在大量未提交修改。
- 尝试创建 `codex/recommender-system-full-upgrade` 分支失败：无法创建 `.git/refs/heads/codex/...`。
- 尝试创建 `codex-recommender-system-full-upgrade` 分支失败：无法写入 `.git/refs/heads/...lock`。

## 安全策略

- 不清理、不覆盖现有未提交修改。
- 不删除核心业务代码。
- 不执行大规模无关重构。
- 后续修改限定在推荐系统、推荐接口、模型评估、管理员模型页和相关文档范围内。

## 技术栈基线

- 后端：Flask + SQLite + Python 推荐模型。
- 前端：Vue 3 + Vite。
- 推荐模型：ItemCF、UserCF、SVD、Song2Vec、Sequence、Hybrid。
- 数据源：本地 SQLite 与 iTunes 试听数据。
