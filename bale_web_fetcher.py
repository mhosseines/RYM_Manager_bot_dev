"""
bale_web_fetcher.py
─────────────────────────
مثل telegram_web_fetcher.py، ولی صفحه‌ی عمومی بله (ble.ir/s/نام_کانال) رو می‌خونه.
اگه ساختار HTML بله با حدس اولیه فرق داشت، لاگ 0 پیام یافته می‌شه و باید
selectorها رو با هم اصلاح کنیم.

هر پست جدید از همون مسیر همیشگی رد می‌شه:
  normalize → hash → duplicate check → similarity check → pending → admin
"""

import asyncio
import logging
import re

import aiohttp
from bs4 import BeautifulSoup

import database as db

# ── تنظیمات ─────────────────────────────────────────────────────────
FETCH_INTERVAL_MINUTES = 10
REQUEST_TIMEOUT_SECONDS = 20
# ─────────────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}


def extract_username_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


async def fetch_channel_html(session: aiohttp.ClientSession, username: str) -> str | None:
    url = f"https://ble.ir/s/{username}"
    try:
        async with session.get(
            url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
        ) as resp:
            if resp.status != 200:
                logger.warning(f"[{username}] HTTP {resp.status} از ble.ir")
                return None
            return await resp.text()
    except Exception as e:
        logger.error(f"[{username}] خطا در دریافت صفحه: {e}")
        return None


def parse_messages(html: str, username: str) -> list[dict]:
    """
    حدس اولیه: بله بر پایه‌ی همون ساختار تلگرام ساخته شده، پس اول با
    همون کلاس‌های tgme_widget_message امتحان می‌کنیم.
    """
    soup = BeautifulSoup(html, "html.parser")
    messages = []

    wraps = soup.select("div.tgme_widget_message")
    if not wraps:
        logger.warning(
            f"[{username}] هیچ پیامی با selector فعلی پیدا نشد — "
            f"احتمالاً ساختار HTML بله فرق داره. طول HTML دریافتی: {len(html)} کاراکتر."
        )
        return []

    for wrap in wraps:
        post_attr = wrap.get("data-post")
        if not post_attr or "/" not in post_attr:
            continue
        msg_id = post_attr.split("/")[-1]

        text_div = wrap.select_one("div.tgme_widget_message_text")
        text = text_div.get_text("\n", strip=True) if text_div else ""

        photo_url = None
        photo_wrap = wrap.select_one("a.tgme_widget_message_photo_wrap")
        if photo_wrap and photo_wrap.get("style"):
            match = re.search(r"url\('(.+?)'\)", photo_wrap["style"])
            if match:
                photo_url = match.group(1)

        link = f"https://ble.ir/{username}/{msg_id}"

        messages.append({
            "id": msg_id,
            "text": text,
            "photo_url": photo_url,
            "link": link,
        })

    return messages


def build_post_text(source_name: str, msg: dict) -> str:
    parts = []
    if msg["text"]:
        parts.append(msg["text"])
    if msg["photo_url"]:
        parts.append(f"🖼 {msg['photo_url']}")
    parts.append(f"🔗 {msg['link']}")
    return "\n\n".join(parts)


async def process_one_message(source_name: str, msg: dict, notify_callback):
    if await db.is_source_url_seen(msg["link"]):
        return

    text = build_post_text(source_name, msg)
    if not text.strip():
        return

    post_id = await db.add_post(
        content_type="text",
        text=text,
        user_id=None,
        file_id=None,
        source_type="bale_channel",
        source_name=source_name,
        source_url=msg["link"],
    )
    await db.log_action(post_id, "bale_channel_fetched")

    logger.info(f"[{source_name}] پست جدید → #{post_id}: {msg['text'][:60]}")
    await notify_callback(post_id)


async def fetch_all_channels(notify_callback):
    sources = await db.get_active_sources(source_type="bale_channel")

    if not sources:
        logger.info("Bale web fetcher: هیچ کانالی تنظیم نشده.")
        return

    logger.info(f"Bale web fetcher: بررسی {len(sources)} کانال…")

    async with aiohttp.ClientSession() as session:
        for source in sources:
            username = extract_username_from_url(source["url"])
            source_name = source["name"]

            html = await fetch_channel_html(session, username)
            if not html:
                continue

            messages = parse_messages(html, username)
            logger.info(f"[{source_name}] {len(messages)} پست در صفحه یافت شد.")

            for msg in messages:
                try:
                    await process_one_message(source_name, msg, notify_callback)
                except Exception as e:
                    logger.error(f"[{source_name}] خطا در پردازش پست: {e}")

            await asyncio.sleep(2)


async def run_bale_web_fetcher(notify_callback):
    logger.info(
        f"Bale web fetcher شروع شد. هر {FETCH_INTERVAL_MINUTES} دقیقه یک‌بار چک می‌کند."
    )
    while True:
        try:
            await fetch_all_channels(notify_callback)
        except Exception as e:
            logger.error(f"Bale web fetcher error: {e}")

        await asyncio.sleep(FETCH_INTERVAL_MINUTES * 60)