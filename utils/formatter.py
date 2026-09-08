"""
formatter.py
─────────────────────────
قالب‌بندی نهایی متن قبل از انتشار در کانال RYM.
این ماژول فقط زمان «انتشار در کانال» اجرا می‌شه، نه زمان ذخیره در دیتابیس —
یعنی تشخیص تکراری بودن (duplicate/similarity) همچنان روی متن خام کار می‌کنه
و این قالب‌بندی روش تاثیری نمی‌ذاره.
"""

import re

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002B00-\U00002BFF"
    "\uFE0F"
    "]+",
    flags=re.UNICODE,
)

def strip_emojis(text: str) -> str:
    if not text:
        return ""
    return EMOJI_PATTERN.sub("", text)

def strip_source_signatures(text: str) -> str:
    """حذف امضا، لینک کانال مبدأ، و دعوت‌به‌عضویت از متن."""
    if not text:
        return ""

    lines = text.split("\n")
    cleaned = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            cleaned.append(line)
            continue

        # فقط @username
        if re.fullmatch(r"@[\w\d_]+", stripped):
            continue

        # فقط لینک به یک کانال تلگرام یا بله (نه لینک خبر خارجی مثل RSS)
        if re.fullmatch(r"(https?://)?(t\.me|ble\.ir)/[\w\d_/]+", stripped):
            continue

        # دعوت به عضویت رایج
        if re.search(
            r"(کانال ما|عضو (کانال )?شوید|جوین (کانال )?شوید|فالو کنید|follow us|join (our|the) channel)",
            stripped, re.IGNORECASE,
        ):
            continue

        cleaned.append(line)

    result = "\n".join(cleaned).strip()
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result


def format_for_channel(text: str, brand_tag: str = "") -> str:
    """متن نهایی آماده‌ی انتشار در کانال را می‌سازد."""
    body = strip_source_signatures(text)
    body = strip_emojis(body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()

    parts = []
    if body:
        parts.append(f"🔴 {body}")   # ← فقط یک 🔴 در ابتدای متن

    if brand_tag:
        parts.append(brand_tag)   # brand_tag هم دیگه بدون 🔻 اضافه میشه چون خودش ممکنه emoji-free باشه

    return "\n\n".join(parts).strip()