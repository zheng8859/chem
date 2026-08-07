## Why

Phase 2 已完成 27 张数据模型表 + JWT 认证 + RBAC 权限中间件，但 `app/api/v1/` 下仅有 `auth.py` 提供登录/注册/刷新端点。前端原型和 Agent 工具层都无法访问数据。本变更补齐全部 REST API 端点，使上层（前端、Agent 工具、MCP Server）有完整的接口可调。

## What Changes

- 新增 7 个 API 路由模块，覆盖全部 27 张表的 CRUD 及业务操作
- 所有端点挂载在 `/api/v1/` 前缀下，统一使用 `require_permission` 做 RBAC 控制
- 请求/响应模型复用 `app/schemas/` 已有 Pydantic 定义，缺漏处补齐
- 实现多租户数据隔离：所有查询沿 school→grade→class 组织链路过滤
- 按 FastAPI 最佳实践组织：router → service → model，保持薄路由层 + 业务逻辑在 service

## Capabilities

### New Capabilities
- `org-api`: 学校、年级、班级的 CRUD 端点，含组织链查询
- `user-api`: 教师入驻审批、学生/家长管理、任课关系绑定、账户管理
- `teaching-api`: 考试记录、题目、学生作答的 CRUD 及批改操作
- `diagnosis-api`: 障碍配置、知识点管理、复习任务、复习历史、预警日志
- `homework-api`: 亲子绑定（含绑定码）、家长通知
- `ocr-api`: 上传会话、OCR 任务、答题卡提交记录的查询与管理
- `question-bank-api`: 题库文件夹管理、题目集-题目关联、历年真题查询

### Modified Capabilities
<!-- No existing specs to modify -->

## Impact

- `app/api/v1/` — 新增 7 个路由文件 + `__init__.py` 路由器聚合
- `app/api/deps.py` — 可能新增分页、排序等通用依赖
- `app/services/` — 每个模块新增对应 service 文件（如 `org_service.py`）
- `app/schemas/` — 已有 10 个文件，按需补充分页响应、列表筛选等通用 schema
- `app/main.py` — 注册新路由（在现有 `auth.router` 基础上追加）
- 零数据库变更 — Phase 2 migration 已就绪
