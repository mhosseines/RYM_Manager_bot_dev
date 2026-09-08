import asyncio

from core.bot_instance import bot, dp
from database import init_db
from database.schema import create_tables
from database.migrations import run_migrations
from handlers import admin, channels, moderation, user
from services.bale_web_fetcher import run_bale_web_fetcher
from services.notifier import notify_post_to_admins
from services.rss_fetcher import run_rss_fetcher
from services.telegram_web_fetcher import run_telegram_web_fetcher


dp.include_router(admin.router)
dp.include_router(channels.router)
dp.include_router(moderation.router)
dp.include_router(user.router)


async def main():
    await init_db()
    await create_tables()
    await run_migrations()
    await asyncio.gather(
        dp.start_polling(bot),
        run_rss_fetcher(notify_callback=notify_post_to_admins),
        run_telegram_web_fetcher(notify_callback=notify_post_to_admins),
        run_bale_web_fetcher(notify_callback=notify_post_to_admins),
    )


if __name__ == "__main__":
    asyncio.run(main())