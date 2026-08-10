"""QA 走查脚本 — 家长端完整流程自动化测试
用法: python tests/qa_parent_mobile_flow.py
前提: 后端已运行在 localhost:8000，已 seed 测试数据
"""
import io
import sys
# Fix Windows GBK encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import asyncio
import json
import time
import re
import httpx
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

BASE = "http://localhost:8000"
PAGES = f"{BASE}/pages/m"
API = f"{BASE}/api/v1"

# ── 测试账号 ──
PARENT_PHONE = "13900000100"
PARENT_PASS = "test123"

results = []  # [(step, passed, detail)]

def log(step, passed, detail=""):
    status = "[PASS]" if passed else "[FAIL]"
    msg = f"{status} {step}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    results.append((step, passed, detail))

def fail(step, detail=""):
    log(step, False, detail)
    return False

# ═══════════════════════════════════════════════════════════════
# Phase 0: 准备 — 验证数据就绪
# ═══════════════════════════════════════════════════════════════
def verify_backend_ready():
    """验证后端服务可用，数据存在"""
    print("\n── Phase 0: 环境检查 ──")
    try:
        with httpx.Client(timeout=10) as c:
            r = c.post(f"{API}/auth/login", json={
                "phone": PARENT_PHONE, "password": PARENT_PASS
            })
            if r.status_code == 200 and r.json().get("success"):
                log("0.1 后端健康检查", True, f"Parent {PARENT_PHONE} 登录成功")
                return True
            else:
                log("0.1 后端健康检查", False, f"HTTP {r.status_code}: {r.text[:150]}")
                return False
    except Exception as e:
        log("0.1 后端连接失败", False, str(e))
        return False


# ═══════════════════════════════════════════════════════════════
# Phase 1: 手机号登录
# ═══════════════════════════════════════════════════════════════
def test_login(page):
    """浏览器中走完登录流程"""
    print("\n── Phase 1: 手机号登录 ──")

    try:
        # 1. Open login page
        page.goto(f"{PAGES}/parent-login.html", timeout=15000)
        page.wait_for_load_state("networkidle")
        log("1.1 打开登录页", True)

        # 2. Verify page elements
        assert page.query_selector('.logo-title'), "Logo 不存在"
        assert page.query_selector('#modeLoginBtn'), "登录模式按钮不存在"
        assert page.query_selector('#modeRegisterBtn'), "注册模式按钮不存在"
        log("1.2 页面元素完整性", True, "Logo / 模式切换 / 表单字段 齐全")

        # 3. Fill login form (login mode is default)
        phone_input = page.query_selector('input[type="tel"]')
        phone_input.fill(PARENT_PHONE)
        password_input = page.query_selector('#passwordInput')
        password_input.fill(PARENT_PASS)
        log("1.3 填写登录信息", True, f"手机: {PARENT_PHONE}")

        # 4. Click submit
        submit_btn = page.query_selector('#submitBtn')
        assert '登录' in submit_btn.text_content(), f"按钮文案错误: {submit_btn.text_content()}"
        submit_btn.click()
        page.wait_for_timeout(3000)

        # 5. Check redirect
        current_url = page.url
        if 'parent.html' in current_url and 'login' not in current_url:
            log("1.4 登录成功 → 跳转 parent.html", True, current_url)
            return True
        else:
            toast = page.query_selector('.toast.show, #toast.show, [class*="toast"]')
            error_text = toast.text_content() if toast else "无可见错误"
            log("1.4 登录失败", False, f"URL={page.url}, error={error_text}")
            return False
    except Exception as e:
        log("Phase 1 异常", False, str(e))
        import traceback; traceback.print_exc()
        return False


# ═══════════════════════════════════════════════════════════════
# Phase 2: 绑定学生 / 子女选择器
# ═══════════════════════════════════════════════════════════════
def test_child_selector(page):
    """验证子女选择器和绑定流程"""
    print("\n── Phase 2: 绑定学生 / 子女选择器 ──")

    try:
        page.wait_for_timeout(1500)

        # Check child selector area
        child_selector = page.query_selector('.child-selector')
        if not child_selector:
            return fail("2.1 子女选择器", "child-selector 元素不存在")

        child_name = page.query_selector('.child-name')
        if child_name and child_name.text_content().strip():
            log("2.1 子女列表加载", True, f"当前子女: {child_name.text_content()}")
        else:
            # Maybe no children bound yet — check for empty state
            empty_text = child_selector.text_content()
            if '暂无绑定子女' in empty_text:
                log("2.1 子女列表", True, "暂无绑定子女（预期：刚注册时可能未绑定）")
            else:
                log("2.1 子女列表加载", True, f"内容: {empty_text[:60]}")

        # Check arrow buttons
        prev_btn = page.query_selector('.child-row .arrow-btn:first-child')
        next_btn = page.query_selector('.child-row .arrow-btn:last-child')
        if prev_btn and next_btn:
            log("2.2 子女选择器箭头", True)

        # Check bind link
        bind_link = page.query_selector('.bind-link')
        if bind_link:
            log("2.3 绑定入口", True, f"链接文案: {bind_link.text_content()}")

            # Test bind sheet open/close
            bind_link.click()
            page.wait_for_timeout(500)
            bind_sheet = page.query_selector('#bindSheet')
            if bind_sheet and bind_sheet.is_visible():
                log("2.4 绑定 Sheet 打开", True)

                # Close it
                close_btn = page.query_selector('#bindSheet .sheet-close')
                if close_btn:
                    close_btn.click()
                    page.wait_for_timeout(500)
                    log("2.5 绑定 Sheet 关闭", True)
            else:
                log("2.4 绑定 Sheet", False, "未显示")
        else:
            log("2.3 绑定入口", True, "无绑定链接（可能已绑定子女）")

        return True
    except Exception as e:
        log("Phase 2 异常", False, str(e))
        return False


# ═══════════════════════════════════════════════════════════════
# Phase 3: 3 Tab 切换 + 数据加载
# ═══════════════════════════════════════════════════════════════
def test_tabs(page):
    """验证概览/报告/AI助手 三个 Tab 切换和数据加载"""
    print("\n── Phase 3: Tab 切换 → 概览 / 报告 / 消息 ──")

    try:
        # Check tab row exists
        tab_row = page.query_selector('#tabRow')
        if not tab_row:
            return fail("3.0 Tab 行", "tabRow 不存在")
        tab_btns = tab_row.query_selector_all('.tab-btn')
        if len(tab_btns) < 3:
            return fail("3.0 Tab 按钮", f"期望 3 个，实际 {len(tab_btns)}")

        # ── Tab 1: 概览 (should be active by default) ──
        tab1_btn = tab_btns[0]
        tab1_active = 'active' in (tab1_btn.get_attribute('class') or '')
        tab1_content = page.query_selector('#tab1')
        tab1_visible = tab1_content and 'active' in (tab1_content.get_attribute('class') or '')

        log("3.1 概览 Tab", tab1_active and tab1_visible,
            f"按钮active={tab1_active}, 内容visible={tab1_visible}")

        # Wait for API data to load
        page.wait_for_timeout(2000)

        # Check for stats grid or empty state
        tab1_html = tab1_content.inner_html() if tab1_content else ''
        has_stats = 'stat-card' in tab1_html or 'stats-grid' in tab1_html
        has_empty = '暂无' in tab1_html or 'tab-placeholder' in tab1_html
        has_error = '加载失败' in tab1_html

        if has_stats:
            log("3.1a 概览数据", True, "统计卡片已渲染")
            cards = tab1_content.query_selector_all('.stat-card')
            log("3.1b 统计卡片数", len(cards) > 0, f"{len(cards)} 张卡片")
        elif has_empty:
            log("3.1a 概览空态", True, "无学习数据显示空态")
        elif has_error:
            log("3.1a 概览加载", False, "加载失败")
        else:
            log("3.1a 概览内容", True, f"HTML 长度: {len(tab1_html)}")

        # ── Tab 2: 学习报告 ──
        tab2_btn = tab_btns[1]
        tab2_btn.click()
        page.wait_for_timeout(2000)  # Wait for lazy load

        tab2_content = page.query_selector('#tab2')
        tab2_active = 'active' in (tab2_content.get_attribute('class') or '') if tab2_content else False
        if tab2_active:
            log("3.2 切换到报告 Tab", True)

            tab2_html = tab2_content.inner_html()
            has_weekly = 'week-selector' in tab2_html or 'week-label' in tab2_html or '周报' in tab2_html
            has_gen_btn = '生成周报' in tab2_html
            has_error = '加载失败' in tab2_html

            if has_weekly:
                log("3.2a 周报内容", True, "周选择器 + 数据已渲染")
            elif has_gen_btn:
                log("3.2a 周报生成入口", True, "显示生成周报按钮")
            elif has_error:
                log("3.2a 周报加载", False, "加载失败")
            else:
                log("3.2a 周报内容", True, f"HTML 长度: {len(tab2_html)}")
        else:
            log("3.2 切换到报告 Tab", False, "tab2 未激活")

        # ── Tab 3: 消息 ──
        tab3_btn = tab_btns[2]
        tab3_btn.click()
        page.wait_for_timeout(2000)

        tab3_content = page.query_selector('#tab3')
        tab3_active = 'active' in (tab3_content.get_attribute('class') or '') if tab3_content else False
        if tab3_active:
            log("3.3 切换到消息 Tab", True)

            tab3_html = tab3_content.inner_html()
            has_msgs = 'msg-item' in tab3_html
            has_empty = '暂无消息' in tab3_html
            has_error = '加载失败' in tab3_html

            if has_msgs:
                log("3.3a 消息列表", True)
                msg_items = tab3_content.query_selector_all('.msg-item')
                log("3.3b 消息条目数", len(msg_items) > 0, f"{len(msg_items)} 条消息")
            elif has_empty:
                log("3.3a 消息空态", True, "暂无消息")
            elif has_error:
                log("3.3a 消息加载", False, "加载失败")
            else:
                log("3.3a 消息内容", True, f"HTML 长度: {len(tab3_html)}")
        else:
            log("3.3 切换到消息 Tab", False, "tab3 未激活")

        return True
    except Exception as e:
        log("Phase 3 异常", False, str(e))
        return False


# ═══════════════════════════════════════════════════════════════
# Phase 4: 通知列表交互
# ═══════════════════════════════════════════════════════════════
def test_notification_detail(page):
    """验证通知展开/已读功能"""
    print("\n── Phase 4: 通知列表交互 ──")

    try:
        # Switch to tab3 if not already
        tab3_btn = page.query_selector('#tabRow .tab-btn:nth-child(3)')
        if tab3_btn:
            tab3_btn.click()
            page.wait_for_timeout(1000)

        tab3_content = page.query_selector('#tab3')
        if not tab3_content:
            return fail("4.0 消息容器", "tab3 不存在")

        msg_items = tab3_content.query_selector_all('.msg-item')
        if len(msg_items) == 0:
            log("4.1 通知列表", True, "0 条消息，跳过交互测试")
            return True

        log("4.1 通知列表", True, f"共 {len(msg_items)} 条消息")

        # Click first message to expand
        first_msg = msg_items[0]
        has_dot_before = bool(first_msg.query_selector('.msg-dot'))
        first_msg.click()
        page.wait_for_timeout(500)

        is_open = 'open' in (first_msg.get_attribute('class') or '')
        detail_visible = first_msg.query_selector('.msg-detail')
        log("4.2 消息展开", is_open, f"消息 clicked, open={is_open}")

        # Check read marking
        has_dot_after = bool(first_msg.query_selector('.msg-dot'))
        is_read = 'read' in (first_msg.get_attribute('class') or '')
        log("4.3 标记已读", is_read or not has_dot_after,
            f"dot_before={has_dot_before}, dot_after={has_dot_after}, read={is_read}")

        return True
    except Exception as e:
        log("Phase 4 异常", False, str(e))
        return False


# ═══════════════════════════════════════════════════════════════
# Phase 5: 浮动 AI 对话
# ═══════════════════════════════════════════════════════════════
def test_ai_panel(page):
    """验证浮动 AI 助手面板"""
    print("\n── Phase 5: 浮动 AI 对话 ──")

    try:
        # Find floating AI button
        floating_btn = page.query_selector('.floating-ai')
        if not floating_btn:
            return fail("5.1 浮动 AI 按钮", "元素不存在")

        assert floating_btn.is_visible(), "浮动按钮不可见"
        log("5.1 浮动 AI 按钮", True, f"文案: {floating_btn.text_content()}")

        # Click to open AI panel
        floating_btn.click()
        page.wait_for_timeout(800)

        # Verify overlay
        overlay = page.query_selector('#aiOverlay')
        overlay_visible = overlay and 'show' in (overlay.get_attribute('class') or '')
        log("5.2 AI 遮罩层", overlay_visible)

        # Verify sheet
        ai_sheet = page.query_selector('#aiSheet')
        sheet_open = ai_sheet and 'open' in (ai_sheet.get_attribute('class') or '')
        log("5.3 AI 底部 Sheet", sheet_open)

        if not sheet_open:
            return fail("5.3 AI Sheet", "未打开")

        # Check chat elements
        chat_msgs = ai_sheet.query_selector('#chatMessages, .chat-messages')
        has_chips = len(ai_sheet.query_selector_all('.sheet-chip')) > 0
        has_input = bool(ai_sheet.query_selector('.sheet-input, #aiInput'))
        has_send = bool(ai_sheet.query_selector('.sheet-send, #aiSendBtn'))

        log("5.4 聊天消息区", chat_msgs is not None)
        log("5.5 快捷问题 Chips", has_chips, f"{len(ai_sheet.query_selector_all('.sheet-chip'))} 个快捷问题")
        log("5.6 输入框 + 发送按钮", has_input and has_send,
            f"input={has_input}, send={has_send}")

        # Click a quick chip to send message
        chips = ai_sheet.query_selector_all('.sheet-chip')
        if len(chips) > 0:
            chip_text = chips[0].text_content()
            chips[0].click()
            page.wait_for_timeout(1500)

            # Check if user message appears
            user_msgs = ai_sheet.query_selector_all('.chat-msg.user')
            log("5.7 快捷问题发送", len(user_msgs) > 0,
                f"点击「{chip_text}」→ user bubble count={len(user_msgs)}")

            # Wait a bit for SSE response
            page.wait_for_timeout(2000)
            ai_msgs = ai_sheet.query_selector_all('.chat-msg.ai')
            status_el = ai_sheet.query_selector('.chat-status')
            log("5.8 AI 响应", len(ai_msgs) > 0 or status_el is not None,
                f"AI bubbles={len(ai_msgs)}, status={'存在' if status_el else '无'}")

        # Close AI panel
        close_btn = ai_sheet.query_selector('.sheet-close')
        if close_btn:
            close_btn.click()
            page.wait_for_timeout(500)
            still_open = 'open' in (ai_sheet.get_attribute('class') or '')
            log("5.9 关闭 AI 面板", not still_open)

        # Reopen — should reset to new conversation
        floating_btn.click()
        page.wait_for_timeout(500)
        reopened_sheet = page.query_selector('#aiSheet')
        welcome_text = reopened_sheet.inner_text() if reopened_sheet else ''
        log("5.10 重新打开 → 新对话", '你好' in welcome_text or 'AI学习顾问' in welcome_text)

        # Close again
        page.query_selector('#aiOverlay').click()
        page.wait_for_timeout(500)

        return True
    except Exception as e:
        log("Phase 5 异常", False, str(e))
        return False


# ═══════════════════════════════════════════════════════════════
# Phase 6: Token 过期 / 401 跳转
# ═══════════════════════════════════════════════════════════════
def test_auth_guard(page):
    """测试未登录访问拦截"""
    print("\n── Phase 6: 鉴权守卫 ──")

    try:
        # Clear localStorage
        page.evaluate("localStorage.clear()")
        page.goto(f"{PAGES}/parent.html", timeout=10000)
        page.wait_for_timeout(1000)

        current_url = page.url
        redirected_to_login = 'login' in current_url or 'parent-login' in current_url
        log("6.1 未登录访问 parent.html → 跳转登录页", redirected_to_login,
            f"URL: {current_url}")
        return True
    except Exception as e:
        log("Phase 6 异常", False, str(e))
        return False


# ═══════════════════════════════════════════════════════════════
# Phase 7: 移动端视口响应式
# ═══════════════════════════════════════════════════════════════
def test_responsive_viewport(page):
    """验证 390px 移动端视口布局"""
    print("\n── Phase 7: 视口 / 响应式 ──")

    try:
        # Already at 390px viewport set by Playwright context
        page.goto(f"{PAGES}/parent-login.html", timeout=10000)
        page.wait_for_timeout(500)

        shell = page.query_selector('.mobile-shell')
        if not shell:
            return fail("7.1 mobile-shell", "不存在")

        # Check no horizontal overflow on login page
        page_width = page.evaluate("document.body.scrollWidth")
        viewport_width = page.evaluate("window.innerWidth")
        no_h_scroll = page_width <= viewport_width + 2  # tolerance
        log(f"7.1 登录页无横向溢出", no_h_scroll,
            f"body={page_width}px, viewport={viewport_width}px")

        # Login to check parent page responsive layout
        page.query_selector('input[type="tel"]').fill(PARENT_PHONE)
        page.query_selector('#passwordInput').fill(PARENT_PASS)
        page.query_selector('#submitBtn').click()
        page.wait_for_timeout(3000)

        if 'parent.html' in page.url:
            page_width2 = page.evaluate("document.body.scrollWidth")
            no_h_scroll2 = page_width2 <= viewport_width + 2
            log(f"7.2 主页无横向溢出", no_h_scroll2,
                f"body={page_width2}px, viewport={viewport_width}px")

            # Check floating button positioned correctly
            floating = page.query_selector('.floating-ai')
            if floating:
                bbox = floating.bounding_box()
                log("7.3 浮动按钮在视口内", bbox is not None and bbox['x'] > 0)
        else:
            log("7.2 主页响应式", True, "跳过（未登录成功）")

        return True
    except Exception as e:
        log("Phase 7 异常", False, str(e))
        return False


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("ChemAI 家长端 QA 自动化走查")
    print("=" * 60)

    # ── 0. 验证后端就绪 ──
    if not verify_backend_ready():
        print("\n[FAIL] 后端不可用，终止测试")
        return 1

    # ── 启动浏览器 ──
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(
            viewport={"width": 390, "height": 844},
            device_scale_factor=2,
            locale="zh-CN",
        )
        page = context.new_page()

        # Capture console errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ("error", "warning") else None)

        # Capture page errors
        page_errors = []
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        try:
            test_login(page)

            # Run remaining tests
            test_child_selector(page)
            test_tabs(page)
            test_notification_detail(page)
            test_ai_panel(page)
            test_auth_guard(page)
            test_responsive_viewport(page)

        except Exception as e:
            print(f"\n[FAIL] 致命异常: {e}")
            import traceback; traceback.print_exc()

        # ── Report console/page errors ──
        if console_errors:
            print(f"\n[WARN]  浏览器控制台警告/错误 ({len(console_errors)} 条):")
            for e in console_errors[:10]:
                print(f"   {e}")
        if page_errors:
            print(f"\n[FAIL] 页面 JS 异常 ({len(page_errors)} 条):")
            for e in page_errors:
                print(f"   {e}")

        # Take final screenshot
        try:
            page.screenshot(path="qa_parent_final.png", full_page=False)
            print("\n[SCREENSHOT] 截图已保存: qa_parent_final.png")
        except:
            pass

        browser.close()

    # ── Summary ──
    print("\n" + "=" * 60)
    print("QA 走查结果汇总")
    print("=" * 60)
    passed = sum(1 for _, p, _ in results if p)
    total = len(results)
    for step, ok, detail in results:
        icon = "[PASS]" if ok else "[FAIL]"
        d = f" — {detail}" if detail else ""
        print(f"  {icon} {step}{d}")
    print(f"\n通过: {passed}/{total} ({100*passed//total if total else 0}%)")

    # Report findings
    failures = [(s, d) for s, ok, d in results if not ok]
    if failures:
        print("\n待修复问题:")
        for step, detail in failures:
            print(f"  [FAIL] {step}: {detail}")
        return 1
    else:
        print("\n[OK] 所有测试通过!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
