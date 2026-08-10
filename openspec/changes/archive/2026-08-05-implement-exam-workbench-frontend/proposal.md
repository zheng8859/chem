## Why

Phase 3 REST API（2026-08-04）已完成后端全部 50+ 端点，覆盖出题、题库、考试、审核、知识点等全部业务域。但前端仅有静态原型 `exam-v2.html`（60 行 vanilla JS，硬编码 3 张 mock 卡片），无法调用任何后端 API。教师实际上无法使用出题工作台。本变更将原型升级为功能完整的前端页面，打通"前端 → API → 数据库"全链路。

## What Changes

- 将 `exam-v2.html` 从 vanilla JS 静态原型重写为 **Vue 3 CDN** 单页应用
- 所有 4 个 Tab 从 mock 数据切换为后端 API 调用（`/api/v1/` 路径）
- Tab 1 实现三种出题模式完整闭环：AI 生成（配置→生成→审核展示→收藏/加入考试）、手动录入（表单→提交）、OCR 导入（上传→预览→确认入库）
- 接入 KaTeX + mhchem CDN，支持 `$...$` 和 `\ce{...}` 双语法化学式渲染
- 新增弹窗系统（确认/输入/选择/预览/管理/蓝本题浏览 6 种类型）
- 新增全组件状态处理（加载态骨架屏、空态引导、错误态重试）
- 题库管理 Tab 支持滚动加载分页、真题库 Tab 支持关键词搜索 + 地区/年份筛选
- 考试列表 Tab 支持创建考试、发布、状态流转展示
- 保留原型全部 CSS 设计变量（Oxford Blue / Teal / Warm Paper / 审核徽章色），与 36 号设计系统对齐

## Capabilities

### New Capabilities
- `exam-workbench-frontend`: 出题工作台前端页面 — 四 Tab（出题工作台/题库管理/历史真题库/考试列表），AI 生成/手动录入/OCR 导入三种出题模式，KaTeX 化学式渲染，审核徽章展示，弹窗系统，全状态处理

### Modified Capabilities
<!-- 纯前端变更，不修改任何后端 spec 层行为 -->

## Impact

- `chemai-backend/frontend/pages/exam-v2.html` — 完全重写（原型 → Vue 3 SPA），预计 1500-2000 行
- 零后端变更 — 所有 API 已在 Phase 3 就绪
- 零数据库变更
- 新增 CDN 依赖：Vue 3、KaTeX + mhchem
