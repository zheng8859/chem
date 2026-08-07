## Context

当前 `exam-v2.html` 为 vanilla JS 静态原型（60 行脚本，3 道硬编码 mock 题）。Phase 3 后端 API（2026-08-04）已就绪全部 50+ 端点。需将原型升级为功能完整的 Vue 3 CDN 单页应用，对接后端 API，实现 4 Tab × 3 Mode 的完整交互闭环。

技术约束：零构建步骤 — 无 npm/webpack/vite，所有依赖通过 CDN 加载。

## Goals / Non-Goals

**Goals:**
- 4 个 Tab 全部切换为真实 API 调用（替换 mock 数据）
- Tab 1 三种出题模式完整闭环（含 KaTeX 渲染 + 审核徽章）
- 弹窗系统（6 种类型）覆盖增删查改确认场景
- 全组件状态处理（加载/空态/错误）
- 保留原型 CSS 设计变量，与 36 号设计系统一致

**Non-Goals:**
- WebSocket/SSE 实时推送（Phase 4 Agent 系统范围）
- 试卷 Word/PDF 导出前端实现（调用后端导出 API 下载文件即可）
- Vue Router（单文件四 Tab，不需要 URL 路由）
- 响应式移动端适配（教师端 1280px+ 桌面视口）
- i18n 国际化（仅中文）

## Decisions

### 1. Vue 3 CDN 全局构建 (`vue.global.prod.js`)

**选择:** Vue 3 CDN 全局构建（`Vue.createApp`），所有组件通过 `app.component()` 注册或内联 `template`。

**理由:** 25 号文档明确指定 Vue 3 CDN 架构。Tab 1 出题工作台有复杂的响应式状态（3 种 mode 切换、多选 chip + 数量、生成/审核多阶段、弹窗系统），vanilla JS 手动 DOM 同步会变成面条代码。Vue 3 的 `reactive()`、`v-for`、`v-if`、`v-model` 原生解决这些需求。

**替代方案:** Vanilla JS 扩展原型 — 拒绝，状态管理复杂度过高，预计 800+ 行手动 DOM 操作。

### 2. 单文件架构 + 模块化 JS 组织

**选择:** 单一 `exam-v2.html` 文件，CSS 保留 `<style>` 块，JS 在 `<script>` 中组织为：CDN 加载 → API 层 → 组件定义 → 状态管理 → 应用挂载。

**理由:** 零构建约束意味着不能拆 `.vue` 单文件组件。将所有代码集中在单文件内虽然文件较大（预计 1500-2000 行），但避免了 ES modules 的 CORS/file:// 问题和构建工具链。

**文件内部组织:**
```
<style>   保留原型全部 CSS（约 400 行，基本不动）
<script src="vue CDN">
<script src="KaTeX + mhchem CDN">
<script>
  // 1. API layer — fetch 封装
  // 2. State — Vue reactive()
  // 3. Components — app.component() × N
  // 4. App mount — createApp()
</script>
```

### 3. API 层：轻量 fetch 封装

**选择:** 前端 API 路径使用后端实际路径（`/api/v1/...`），在 JS 中定义为常量对象。封装一个 `api` 模块处理 JSON 解析、错误统一处理和 auth token 注入。

```javascript
const api = {
  base: '/api/v1',
  async get(path, params) { ... },   // GET + query string
  async post(path, body) { ... },    // POST + JSON body
  async patch(path, body) { ... },   // PATCH
  async del(path) { ... },           // DELETE
}
```

**错误处理:** 统一捕获 HTTP 异常，4xx 返回后端中文错误消息，5xx 返回通用"服务器错误，请重试"。网络超时 30s 后自动 reject。

**Auth:** 从 `localStorage` 读取 JWT access_token，注入 `Authorization: Bearer <token>` 请求头。

### 4. KaTeX 渲染策略：双语法 + 自定义指令

**选择:** 加载 KaTeX + mhchem CDN，编写 Vue 自定义指令 `v-katex` 自动扫描元素文本中的 `$...$` 和 `\ce{...}` 并渲染。

**渲染流程:**
1. 元素挂载后，扫描 `textContent`
2. 正则提取 `$...$` 包裹的公式，调用 `katex.renderToString()` 替换
3. `\ce{...}` 通过 mhchem 扩展自动识别（KaTeX 配置中启用 mhchem）
4. 渲染为 HTML 后通过 `v-html` 或 DOM 替换输出

**为什么自定义指令而非组件:** 题目内容来自 API 的 content 字段，是混合了中文和 LaTeX 的自由文本。`v-katex` 指令让渲染逻辑对任意包含 LaTeX 的 DOM 元素通用。

### 5. 四 Tab 结构：`v-show` 而非 `<component :is>`

**选择:** 四个 Tab 面板用 `v-show` 切换（全程保持 DOM），不用动态组件。

**理由:** Tab 间需要共享数据（如 Tab 1 生成的题目出现在 Tab 2、Tab 3 选择的蓝本题传入 Tab 1）。保持所有面板的 DOM 存活意味着表单状态不会因切换 Tab 丢失。四 Tab 的 DOM 总量可控（非无限列表），性能影响可忽略。

### 6. 题型选择器：多选 chip + 数量微调

**选择:** 题型 chip 为多选模式（点击切换选中态），选中后 chip 右侧出现数量微调控件（`-` / `数字` / `+`）。未选中的题型不发送到 API。

**替代方案:** 单选 chip（原型的做法）— 拒绝，25 号文档明确要求多选题型，一次可出多种题。

### 7. 弹窗系统：Teleport + 全局状态

**选择:** 使用 Vue 3 `<Teleport to="body">` 将弹窗渲染到 body 层，全局 `modal` 响应式对象管理弹窗状态：

```javascript
const modal = reactive({
  type: null,        // 'confirm' | 'prompt' | 'select' | 'preview' | 'manage' | 'variant-browser'
  visible: false,
  title: '',
  props: {},         // 传递给弹窗的数据
  resolve: null,     // Promise resolve
})
```

**使用模式:** `const result = await showModal('confirm', { title: '删除确认', message: '...' })` — 返回 Promise，弹窗关闭时 resolve。

### 8. 分页策略：按场景选择

**选择:**
- 题库文件夹列表：滚动加载（`IntersectionObserver` 监听底部哨兵元素，触底 `offset += limit`）
- 历史真题列表：滚动加载（同上）
- 考试列表：传统分页（数据量小，预计 <50 条）
- 生成题目结果：不分页，一次性展示

**理由:** 题库和真题属于浏览探索型交互，滚动加载体验流畅，避免翻页打断浏览节奏。考试列表数据量小，传统分页更清晰。

### 9. 状态处理：三态统一模式

**选择:** 每个数据组件套用统一三态模板：

```html
<div v-if="loading">骨架屏</div>
<div v-else-if="error">{{ error }} <button @click="retry">重试</button></div>
<div v-else-if="!items.length">空态引导</div>
<div v-else>正常内容</div>
```

加载态判定：请求发出后 200ms 内不显示骨架屏（避免闪烁），超过 200ms 显示。

## Risks / Trade-offs

- **[Risk] 单文件过大（>1500 行）** → Mitigation: JS 区域用清晰注释分隔模块（API / State / Components / Mount），逻辑分组明确，非面条代码
- **[Risk] KaTeX 渲染性能** → Mitigation: 使用 `v-katex` 指令仅在元素挂载时渲染一次，非实时轮询。题目卡片数量 ≤20，单次渲染可接受
- **[Risk] ChromaDB / LLM 不可用导致生成失败** → Mitigation: 错误态设计中已有的重试按钮 + Toast 错误描述
- **[Risk] JWT token 过期** → Mitigation: API 层拦截 401，尝试 refresh token，失败则跳转登录页
- **[Trade-off] 不拆多文件 vs 单文件可维护性** → 单文件是零构建约束下的务实选择。如果未来 JS 逻辑持续膨胀，可迁移到 ES modules + 简单打包
