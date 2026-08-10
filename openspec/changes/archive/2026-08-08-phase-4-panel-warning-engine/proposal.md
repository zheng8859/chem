## Why

教师缺乏一个聚合视图来快速掌握全班学情——谁在退步、哪个知识点全班薄弱、障碍类型分布如何。同时，系统缺少自动化的异常检测机制，无法在学生出现成绩下滑、长期未练习或障碍类型突变时主动告警。本变更为 Phase 4 核心功能，在已有的考试、练习、诊断数据基础上，构建学情面板 API 与预警引擎。

## What Changes

- **新增学情面板 API（7 端点）**：班级聚合视图（加权均分、知识点错误率 Top 5、障碍类型分布、进步/退步 Top 3、重点关注学生）、学生详情抽屉、知识点/障碍维度展开、考试趋势
- **新增预警引擎 API（5 端点）**：四类自动检测规则（连续未登录、成绩下滑、高错误率、新障碍出现）、三级严重度、完整生命周期管理（pending → processing → resolved / dismissed）
- **新增 `BarrierProfileHistory` 模型**：追踪学生障碍画像的历史快照，用于 `new_barrier` 检测的基线对比
- **丰富 `WarningLog` 模型**：增加 title、data（JSON 快照）、status、processed_by、processed_at、note 六个字段
- **新增 APScheduler 定时任务**：每天 00:00（Asia/Shanghai）执行预警检测
- **新增 `EarlyWarningService`**：四类检测规则的纯函数实现
- **新增 `PanelService`**：按需实时聚合的班级学情计算（加权指数衰减公式）

## Capabilities

### New Capabilities
- `learning-panel`: 教师端学情面板聚合 API——班级概览、学生详情、知识点/障碍维度展开、考试趋势、重点关注学生列表
- `warning-engine`: 四规则预警检测引擎——连续未登录、成绩下滑、高错误率、新障碍出现，含三级严重度和生命周期管理

### Modified Capabilities
<!-- 本次为全新能力，不修改现有 spec 级行为 -->

## Impact

- **新增文件**：`app/services/panel_service.py`、`app/services/early_warning_service.py`、`app/api/v1/panel.py`、`app/api/v1/warning.py`、`app/models/barrier_profile_history.py`
- **修改文件**：`app/models/diagnosis.py`（丰富 WarningLog）、`app/infrastructure/scheduler.py`（新增 cron）、`app/main.py`（注册新路由）
- **数据库迁移**：新增 `BarrierProfileHistory` 表、WarningLog 新增 6 列（Alembic 迁移）
- **依赖**：依赖现有 `ExamRecord`、`PracticeSession`、`Student`、`StudentAnswer` 模型的数据。预警检测 `score_drop` 仅取 `ExamRecord`，不取练习数据。
