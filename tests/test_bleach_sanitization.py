"""
Unit tests for bleach sanitization used in the backend.

Tests all bleach.clean() configurations used across:
- core/views.py (BroadcastView, PublicLandingLeadCreateView, CrmContactView)
- telegram_bot/handlers_teacher.py (handle_rejection_comment)
- telegram_bot/handlers_manager.py (tasks, menu_tasks, task_set_status, task_filter)
"""

import bleach


# ── Config 1: BroadcastView — Telegram-safe HTML tags ─────

def test_broadcast_sanitize_keeps_safe_tags():
    """BroadcastView: allow b, i, u, s, a, code, pre tags"""
    text = "<b>bold</b> <i>italic</i> <u>underline</u> <s>strike</s> <code>code</code> <pre>pre</pre>"
    result = bleach.clean(text, tags=['b', 'i', 'u', 's', 'a', 'code', 'pre'], attributes={'a': ['href']}, protocols=['http', 'https', 'mailto'], strip=True)
    assert "<b>bold</b>" in result
    assert "<i>italic</i>" in result
    assert "<u>underline</u>" in result
    assert "<s>strike</s>" in result
    assert "<code>code</code>" in result
    assert "<pre>pre</pre>" in result


def test_broadcast_sanitize_strips_dangerous_tags():
    """BroadcastView: strip script, iframe, img, style"""
    text = "<script>alert(1)</script><iframe src='evil'></iframe><img src=x onerror=alert(1)><style>body{color:red}</style>"
    result = bleach.clean(text, tags=['b', 'i', 'u', 's', 'a', 'code', 'pre'], attributes={'a': ['href']}, protocols=['http', 'https', 'mailto'], strip=True)
    assert "<script>" not in result
    assert "<iframe" not in result
    assert "<img" not in result
    assert "<style>" not in result


def test_broadcast_sanitize_allows_safe_a_tag():
    """BroadcastView: allow <a> with href"""
    text = '<a href="https://example.com">link</a>'
    result = bleach.clean(text, tags=['b', 'i', 'u', 's', 'a', 'code', 'pre'], attributes={'a': ['href']}, protocols=['http', 'https', 'mailto'], strip=True)
    assert '<a href="https://example.com">' in result
    assert "link" in result


def test_broadcast_sanitize_strips_event_handlers():
    """BroadcastView: strip onclick, onerror, etc."""
    text = '<a href="https://example.com" onclick="alert(1)">link</a>'
    result = bleach.clean(text, tags=['b', 'i', 'u', 's', 'a', 'code', 'pre'], attributes={'a': ['href']}, protocols=['http', 'https', 'mailto'], strip=True)
    assert "onclick" not in result


def test_broadcast_sanitize_strips_javascript_href():
    """BroadcastView: strip javascript: protocol from href"""
    text = '<a href="javascript:alert(1)">link</a>'
    result = bleach.clean(text, tags=['b', 'i', 'u', 's', 'a', 'code', 'pre'], attributes={'a': ['href']}, protocols=['http', 'https', 'mailto'], strip=True)
    assert "javascript" not in result
    assert "link" in result


def test_broadcast_sanitize_strips_data_href():
    """BroadcastView: strip data: protocol from href"""
    text = '<a href="data:text/html,<script>alert(1)</script>">link</a>'
    result = bleach.clean(text, tags=['b', 'i', 'u', 's', 'a', 'code', 'pre'], attributes={'a': ['href']}, protocols=['http', 'https', 'mailto'], strip=True)
    assert "data:" not in result


def test_broadcast_sanitize_strips_unknown_attributes():
    """BroadcastView: only href allowed on <a>"""
    text = '<a href="https://example.com" target="_blank" rel="noopener">link</a>'
    result = bleach.clean(text, tags=['b', 'i', 'u', 's', 'a', 'code', 'pre'], attributes={'a': ['href']}, protocols=['http', 'https', 'mailto'], strip=True)
    assert "target" not in result
    assert "rel" not in result
    assert "href" in result


def test_broadcast_sanitize_handles_mxss():
    """BroadcastView: resist mutation XSS"""
    text = "<noscript><p title=\"</noscript><img src=x onerror=alert(1)>\">"
    result = bleach.clean(text, tags=['b', 'i', 'u', 's', 'a', 'code', 'pre'], attributes={'a': ['href']}, protocols=['http', 'https', 'mailto'], strip=True)
    assert "onerror" not in result
    assert "<img" not in result


def test_broadcast_sanitize_strips_svg():
    """BroadcastView: strip <svg> with onload"""
    text = '<svg onload="alert(1)">'
    result = bleach.clean(text, tags=['b', 'i', 'u', 's', 'a', 'code', 'pre'], attributes={'a': ['href']}, protocols=['http', 'https', 'mailto'], strip=True)
    assert "<svg" not in result
    assert "onload" not in result


def test_broadcast_sanitize_limits_mailto_protocol():
    """BroadcastView: allow mailto: protocol"""
    text = '<a href="mailto:test@example.com">email</a>'
    result = bleach.clean(text, tags=['b', 'i', 'u', 's', 'a', 'code', 'pre'], attributes={'a': ['href']}, protocols=['http', 'https', 'mailto'], strip=True)
    assert "mailto" in result


# ── Config 2: Text fields — strip all HTML ────────────────

def test_strip_all_html_removes_script():
    """PublicLandingLeadCreateView/CrmContactView: strip script tags"""
    result = bleach.clean("<script>alert(1)</script>John", tags=[], strip=True)
    assert "<script>" not in result
    assert "John" in result


def test_strip_all_html_removes_img():
    """Strip <img> with onerror"""
    result = bleach.clean("<img src=x onerror=alert(1)>Hello", tags=[], strip=True)
    assert "<img" not in result
    assert "onerror" not in result
    assert "Hello" in result


def test_strip_all_html_removes_event_handlers():
    """Strip inline event handlers"""
    result = bleach.clean('<p onclick="alert(1)">text</p>', tags=[], strip=True)
    assert "onclick" not in result
    assert "text" in result


def test_strip_all_html_removes_iframe():
    """Strip iframe tags"""
    result = bleach.clean("<iframe src='https://evil.com'></iframe>safe", tags=[], strip=True)
    assert "<iframe" not in result
    assert "safe" in result


def test_strip_all_html_leaves_plain_text():
    """Plain text should be preserved"""
    result = bleach.clean("Hello, World!", tags=[], strip=True)
    assert result == "Hello, World!"


def test_strip_all_html_leaves_russian_text():
    """Cyrillic text should be preserved"""
    result = bleach.clean("Привет, мир! Салам, дүйнө!", tags=[], strip=True)
    assert "Привет" in result
    assert "Салам" in result


def test_strip_all_html_handles_empty_string():
    """Empty string returns empty"""
    result = bleach.clean("", tags=[], strip=True)
    assert result == ""


def test_strip_all_html_preserves_text_inside_tags():
    """Text content inside stripped HTML tags is preserved as plain text"""
    result = bleach.clean("<script>alert(1)</script>", tags=[], strip=True)
    assert result == "alert(1)"  # text content preserved, tags removed


def test_strip_all_html_removes_style():
    """Strip <style> tags"""
    result = bleach.clean("<style>body{color:red}</style>content", tags=[], strip=True)
    assert "<style>" not in result
    assert "content" in result


def test_strip_all_html_removes_comment():
    """Strip HTML comments"""
    result = bleach.clean("<!-- comment -->visible", tags=[], strip=True)
    assert "comment" not in result
    assert "visible" in result


# ── Config 3: Telegram bot task titles — strip all HTML ──

def test_task_title_sanitize_removes_script():
    """handlers_manager.py: strip <script> from task title"""
    title = "<script>evil()</script>Проверить ДЗ"
    safe = bleach.clean(title, tags=[], strip=True)[:100]
    assert "<script" not in safe
    assert "Проверить ДЗ" in safe


def test_task_title_sanitize_removes_html():
    """handlers_manager.py: strip HTML from task title"""
    title = "<b>bold</b> <i>italic</i> title"
    safe = bleach.clean(title, tags=[], strip=True)[:100]
    assert "<b>" not in safe
    assert "<i>" not in safe
    assert "bold italic title" in safe


def test_task_title_truncates_long():
    """handlers_manager.py: title truncated to 100 chars"""
    title = "A" * 200
    safe = bleach.clean(title, tags=[], strip=True)[:100]
    assert len(safe) == 100


def test_task_description_sanitize():
    """handlers_manager.py: strip HTML from description"""
    desc = "<script>alert(1)</script>описание задачи"
    safe = bleach.clean(desc, tags=[], strip=True)[:150]
    assert "<script" not in safe
    assert "описание задачи" in safe


# ── Config 4: Teacher rejection comment — strip all HTML ─

def test_rejection_comment_sanitize_removes_script():
    """handlers_teacher.py: strip script from rejection comment"""
    comment = "<script>alert(1)</script>Не могу вести эту группу"
    safe = bleach.clean(comment, tags=[], strip=True)[:500]
    assert "<script" not in safe
    assert "Не могу вести эту группу" in safe


def test_rejection_comment_sanitize_removes_phishing_link():
    """handlers_teacher.py: strip <a> phishing links from comment"""
    comment = '<a href="http://evil.com">Нажми сюда</a> для details'
    safe = bleach.clean(comment, tags=[], strip=True)[:500]
    assert "<a " not in safe
    assert "http://evil.com" not in safe
    assert "Нажми сюда для details" in safe


def test_rejection_comment_truncates_long():
    """handlers_teacher.py: comment truncated to 500 chars"""
    comment = "A" * 1000
    safe = bleach.clean(comment, tags=[], strip=True)[:500]
    assert len(safe) == 500


# ── Config 5: PublicLandingLeadCreateView — text fields ──

def test_lead_full_name_sanitize():
    """PublicLandingLeadCreateView: strip HTML from full_name"""
    name = "<b>Иван</b> <script>evil()</script>Петров"
    safe = bleach.clean(name, tags=[], strip=True)[:200]
    assert "<b>" not in safe
    assert "<script" not in safe
    # bleach removes tags but preserves text content — "evil()" is now plain text, safe
    assert "Иван" in safe
    assert "Петров" in safe
    assert "evil()" in safe  # text content preserved, not HTML


def test_lead_course_interest_sanitize():
    """PublicLandingLeadCreateView: strip HTML from course_interest"""
    interest = "<a href='http://evil.com'>Click</a> Английский"
    safe = bleach.clean(interest, tags=[], strip=True)[:200]
    assert "<a " not in safe
    assert "Английский" in safe


def test_lead_comment_sanitize():
    """PublicLandingLeadCreateView: strip HTML from comment"""
    comment = "<script>stealCookies()</script>Хочу изучать Python"
    safe = bleach.clean(comment, tags=[], strip=True)[:1000]
    assert "<script" not in safe
    assert "Хочу изучать Python" in safe
