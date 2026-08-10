import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
import database as db

# تنظیمات لاگ
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# اطلاعات حساب (API ID و API Hash را از سایت my.telegram.org دریافت کنید)
API_ID = 1234567  # جایگزین کنید با API_ID خودتان
API_HASH = "YOUR_API_HASH"  # جایگزین کنید با API_HASH خودتان
SESSION_NAME = "channel_listener_session"

app = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH)


def extract_content_and_media(message: Message):
    """استخراج نوع محتوا، متن/کپشن و file_id از پیام تلگرام"""
    text = message.caption or message.text or ""
    file_id = None
    content_type = "text"

    if message.photo:
        content_type = "photo"
        file_id = message.photo.file_id
    elif message.video:
        content_type = "video"
        file_id = message.video.file_id
    elif message.document:
        content_type = "document"
        file_id = message.document.file_id
    elif message.animation:
        content_type = "animation"
        file_id = message.animation.file_id
    elif message.audio:
        content_type = "audio"
        file_id = message.audio.file_id
    elif message.voice:
        content_type = "voice"
        file_id = message.voice.file_id

    return content_type, text, file_id


@app.on_message(filters.channel)
async def handle_channel_post(client: Client, message: Message):
    """شنود زنده پیام‌های کانال‌ها"""
    try:
        # دریافت لیست سورس‌های فعال کانال از دیتابیس
        active_sources = await db.get_active_sources(source_type="telegram_channel")
        if not active_sources:
            return

        active_urls = [s["url"].strip().lower() for s in active_sources]

        chat_username = message.chat.username
        chat_id = message.chat.id

        # ساخت لینک یکتا برای پست جهت جلوگیری از ذخیره تکراری
        if chat_username:
            source_url = f"https://t.me/{chat_username}/{message.id}"
            channel_identifier = f"@{chat_username}"
        else:
            clean_chat_id = str(chat_id).replace("-100", "")
            source_url = f"https://t.me/c/{clean_chat_id}/{message.id}"
            channel_identifier = str(chat_id)

        # بررسی اینکه آیا کانال فرستنده جزو سورس‌های ثبت‌شده ما هست یا خیر
        is_target_channel = any(
            channel_identifier.lower() in url or str(chat_id) in url for url in active_urls
        )

        if not is_target_channel:
            return

        # چک کردن تکراری بودن در دیتابیس
        if await db.is_source_url_seen(source_url):
            logger.info(f"پست تکراری نادیده گرفته شد: {source_url}")
            return

        content_type, text, file_id = extract_content_and_media(message)

        if not text and not file_id:
            return

        source_name = message.chat.title or channel_identifier

        # ذخیره پست جدید در دیتابیس
        post_id = await db.add_post(
            content_type=content_type,
            text=text,
            user_id=None,
            file_id=file_id,
            source_type="telegram_channel",
            source_name=source_name,
            source_url=source_url,
            channel_msg_id=message.id,
        )

        await db.log_action(post_id, "telegram_channel_fetched")
        logger.info(f"پست جدید از کانال [{source_name}] با شناسه DB #{post_id} ثبت شد.")

    except Exception as e:
        logger.error(f"خطا در پردازش پیام کانال: {e}")


async def fetch_recent_posts_for_all_sources(limit_per_channel: int = 10):
    """بررسی و دریافت آخرین پست‌های کانال‌ها (مثلاً هنگام استارت)"""
    active_sources = await db.get_active_sources(source_type="telegram_channel")

    for source in active_sources:
        try:
            channel_url = source["url"]
            source_name = source["name"]
            logger.info(f"در حال چک کردن پست‌های اخیر کانال: {source_name} ({channel_url})")

            chat = await app.get_chat(channel_url)

            async for message in app.get_chat_history(chat.id, limit=limit_per_channel):
                if message.empty or message.service:
                    continue

                if chat.username:
                    source_url = f"https://t.me/{chat.username}/{message.id}"
                else:
                    clean_chat_id = str(chat.id).replace("-100", "")
                    source_url = f"https://t.me/c/{clean_chat_id}/{message.id}"

                if await db.is_source_url_seen(source_url):
                    continue

                content_type, text, file_id = extract_content_and_media(message)

                if not text and not file_id:
                    continue

                post_id = await db.add_post(
                    content_type=content_type,
                    text=text,
                    user_id=None,
                    file_id=file_id,
                    source_type="telegram_channel",
                    source_name=source_name,
                    source_url=source_url,
                    channel_msg_id=message.id,
                )

                await db.log_action(post_id, "telegram_channel_fetched")
                logger.info(f"پست قدیمی دریافت و ذخیره شد: ID #{post_id} از {source_name}")

        except Exception as e:
            logger.error(f"خطا در دریافت پست‌های کانال {source['name']}: {e}")


if __name__ == "__main__":
    print("در حال ساخت/بررسی فایل دیتابیس...")
    asyncio.run(db.init_db())
    print("شنود کانال‌های تلگرام روشن شد...")
    app.run()