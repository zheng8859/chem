## Context

参见 proposal.md - Why。后端 12 个 API 端点已全部就绪（1178 tests passing）。前端原型（practice.html / review.html / wrong.html）是 7/31 创建的纯静态 mockup，需要最小改动改造为真实 API 驱动的页面。架构约束：多页模式（不引入 SPA）、CSS 保持内联、现有 HTML 骨架不变。

## Goals / Non-Goals

**Goals:**
- 4 个 HTML 页面对接 12 个 API 端点，覆盖练习 → 判分 → 错题 → 复习全链路
- 共享 `api-client.js` 和 `auth.js`，消除代码重复
- KaTeX + mhchem 化学式渲染
- 每个数据场景覆盖加载 / 空 / 错误三种状态

**Non-Goals:**
- SPA 框架（不做 Vue Router / 组件化重构）
- CSS 抽取（保持内联 style）
- 后端 API 修改（只消费已有端点）
- 练习效果追踪页（effect API 已有但非核心流程，本次通过"我的"页间接展示）

## Decisions

### D1: 多页 + 页内 View 切换

每个 HTML 是一个独立入口，页内业务通过 JS 切换 view（隐藏/显示 div）。跨页传参通过 URL query string。

**替代方案**: Vue 3 SPA → 否决，对现有原型改动过大。
**替代方案**: 纯多页无 view 切换（如 3 个独立 HTML 分别做 list/quiz/result）→ 否决，答题状态（selected answers map）跨页传递复杂。

### D2: 共享 JS 模块

抽取两个共享文件：
- `frontend/js/auth.js` — `getToken()`, `getCurrentUser()`, `redirectToLogin()`, 从 localStorage 读取 JWT
- `frontend/js/api-client.js` — `apiGet(url, params)`, `apiPost(url, body)` 封装 fetch，自动注入 `Authorization: Bearer <token>` 头，统一处理 401 和错误

每个 HTML 通过 `<script src="../../js/auth.js"></script>` 引入。

**替代方案**: 每个 HTML 自己写 fetch 逻辑 → 否决，4 个文件 × ~30 行重复 = 120 行重复。

### D3: 状态管理

每个页面用 Plain Old JavaScript Object (POJO) 管理状态：
```js
var state = {
  tasks: { pending: [], completed: [] },  // practice.html
  currentQuestionIndex: 0,
  answers: {},          // { questionId: selectedAnswer }
  loading: { tasks: false, submit: false },
  error: null
};
```

不需要 Redux/Vuex/Pinia，每个页面的状态域不超过 10 个字段。

### D4: KaTeX 渲染函数

在 `api-client.js` 中提供 `renderLatex(containerEl)` 工具函数，遍历 `[data-latex]` 属性或 `$...$` 正则匹配，交给 KaTeX + mhchem 渲染。KaTeX 通过 CDN 加载：
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16/dist/katex.min.js"></script>
```

### D5: 变式题训练独立页

`variant.html` 作为独立页面，从 URL `?question_id=xxx&count=3` 读取参数。训练完成后通过 `history.back()` 返回错题本。

**替代方案**: 在 wrong.html 内新增 view → 否决，wrong.html 已有 200+ 行代码，混合训练流程会让文件过于臃肿（预计 400+ 行）。

### D6: 复习中心入口

不修改现有 TabBar（保持 4 个：AI助教/练习/错题/我的）。review.html 通过"我的"页内的"复习中心"子入口进入。review.html 是一个独立页，但不在 TabBar 增加第 5 个入口。

**替代方案**: TabBar 加第 5 个"复习" tab → 否决，设计规格（文档40）明确 TabBar 为 4 个 tab。

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| KaTeX CDN 加载失败 → 化学式无法渲染 | 降级方案：`<span>` 显示原始 LaTeX 文本，不阻断裂页功能 |
| API 字段名与原型硬编码不一致（蛇形 vs 驼峰） | 读取真实 API schema 文档对齐字段名 |
| 变式题 LLM 生成耗时（3-10s），学生等待 | 生成中展示 loading 状态 + 预计等待提示 |
| review.html 入口隐蔽（在"我的"页 → 二级页）| 在"我的"页复习中心入口展示角标数字（待复习数量） |

## Open Questions

- 变式题生成完成后的"学习建议"文案是否需要后端返回（当前 API 返回原始数据，前端自行按正确率分级展示）
- 错题本的翻页是否用无限滚动还是"加载更多"按钮（初步用无限滚动，若性能问题改为按钮）
