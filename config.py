import os
from dotenv import load_dotenv

load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS = [
    int(x)
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip()
]


CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))

BALE_BOT_TOKEN = os.getenv("BALE_BOT_TOKEN")
BALE_CHANNEL_ID = os.getenv("BALE_CHANNEL_ID")


BRAND_TAG = os.getenv(
    "BRAND_TAG",
    "#RYM"
)


DATABASE_NAME = os.getenv(
    "DATABASE_NAME",
    "posts.db"
)


MAX_POST_LENGTH = int(
    os.getenv(
        "MAX_POST_LENGTH",
        "4000"
    )
)


PENDING_LIMIT = int(
    os.getenv(
        "PENDING_LIMIT",
        "20"
    )
)


RSS_INTERVAL = int(
    os.getenv(
        "RSS_INTERVAL",
        "300"
    )
)