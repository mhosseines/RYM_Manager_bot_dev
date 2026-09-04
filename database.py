import hashlib
import re
import aiosqlite
from datetime import datetime, date

import logging
logger = logging.getLogger(__name__)

DB_NAME = "posts.db"


# ────────────────────────────────────────────
# TEXT UTILITIES
# ────────────────────────────────────────────

def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def make_hash(normalized_text: str) -> str:
    return hashlib.md5(normalized_text.encode("utf-8")).hexdigest()


def compute_similarity(text_a: str, text_b: str) -> float:
    if not text_a or not text_b:
        return 0.0

    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
        "for", "of", "with", "by", "from", "is", "it", "this", "that",
        "was", "are", "be", "as", "so", "we", "he", "she", "they",
        "his", "her", "our", "its", "not", "no", "up", "out", "if", "do",
        "did", "has", "had", "have", "can", "will", "just", "been", "also",
        "than", "then", "when", "what", "which", "who", "how", "all", "each"
    }

    words_a = set(text_a.split()) - stop_words
    words_b = set(text_b.split()) - stop_words

    if not words_a or not words_b:
        return 0.0

    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


# ────────────────────────────────────────────
# DATABASE SETUP — safe migration
# ────────────────────────────────────────────

async def _migrate_posts_user_id_nullable(db: aiosqlite.Connection):
    """
    نسخه‌های قدیمی این پروژه جدول posts رو با user_id NOT NULL ساخته بودن.
    چون RSS و کانال‌های تلگرام user_id ندارن (None هستن)، این تابع
    قید NOT NULL رو با بازسازی امن جدول (بدون از دست رفتن هیچ داده‌ای) برمی‌داره.
    اگر جدول از قبل درست باشه، این تابع کاری انجام نمی‌ده.
    """
    cursor = await db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='posts'"
    )
    if not await cursor.fetchone():
        return  # جدول هنوز ساخته نشده

    cursor = await db.execute("PRAGMA table_info(posts)")
    columns = await cursor.fetchall()
    user_id_col = next((c for c in columns if c[1] == "user_id"), None)

    if not user_id_col or user_id_col[3] != 1:
        return  # از قبل nullable هست

    logger.info("Migrating posts table: در حال حذف قید NOT NULL از user_id…")

    col_names = [c[1] for c in columns]

    await db.execute("ALTER TABLE posts RENAME TO posts_old_migration")

    col_defs = []
    for c in columns:
        name, col_type = c[1], (c[2] or "TEXT")
        if name == "id":
            col_defs.append("id INTEGER PRIMARY KEY AUTOINCREMENT")
        elif name == "status":
            col_defs.append("status TEXT DEFAULT 'pending'")
        else:
            col_defs.append(f"{name} {col_type}")   # بدون NOT NULL

    await db.execute(f"CREATE TABLE posts ({', '.join(col_defs)})")

    col_list = ", ".join(col_names)
    await db.execute(
        f"INSERT INTO posts ({col_list}) SELECT {col_list} FROM posts_old_migration"
    )
    await db.execute("DROP TABLE posts_old_migration")
    await db.commit()

    logger.info("✅ Migration انجام شد. همه‌ی پست‌های قبلی حفظ شدند.")

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:

        await _migrate_posts_user_id_nullable(db)

        # posts
        await db.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id          INTEGER,
                content_type     TEXT NOT NULL,
                text             TEXT,
                file_id          TEXT,
                status           TEXT DEFAULT 'pending'
            )
        """)

        # sources (RSS feeds and Telegram Channels)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                name     TEXT NOT NULL,
                type     TEXT NOT NULL DEFAULT 'rss',
                url      TEXT NOT NULL UNIQUE,
                active   INTEGER NOT NULL DEFAULT 1,
                priority INTEGER NOT NULL DEFAULT 5
            )
        """)

        # logs
        await db.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id   INTEGER NOT NULL,
                action    TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)

        # blocked users
        await db.execute("""
            CREATE TABLE IF NOT EXISTS blocked_users (
                user_id    INTEGER PRIMARY KEY,
                reason     TEXT,
                blocked_at TEXT NOT NULL
            )
        """)

        await db.commit()

        # Safe column migrations — never deletes data
        new_columns = [
            ("normalized_text", "TEXT"),
            ("hash",            "TEXT"),
            ("similarity_flag", "TEXT"),
            ("similar_post_id", "INTEGER"),
            ("channel_msg_id",  "INTEGER"),
            ("source_type",     "TEXT DEFAULT 'user'"),
            ("source_name",     "TEXT"),
            ("source_url",      "TEXT"),
            ("created_at",      "TEXT"),
        ]
        for col_name, col_definition in new_columns:
            try:
                await db.execute(
                    f"ALTER TABLE posts ADD COLUMN {col_name} {col_definition}"
                )
                await db.commit()
            except Exception:
                pass


# ────────────────────────────────────────────
# BLOCKED USERS
# ────────────────────────────────────────────

async def block_user(user_id: int, reason: str = ""):
    """Add a user to the blocked list."""
    blocked_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO blocked_users (user_id, reason, blocked_at) VALUES (?, ?, ?)",
            (user_id, reason, blocked_at)
        )
        await db.commit()


async def unblock_user(user_id: int):
    """Remove a user from the blocked list."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM blocked_users WHERE user_id = ?", (user_id,)
        )
        await db.commit()


async def is_user_blocked(user_id: int) -> bool:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT user_id FROM blocked_users WHERE user_id = ?", (user_id,)
        )
        return await cursor.fetchone() is not None


# ────────────────────────────────────────────
# RATE LIMITING — 1 submission per minute per user
# ────────────────────────────────────────────

RATE_LIMIT_SECONDS = 60
_last_submission: dict[int, datetime] = {}


def check_rate_limit(user_id: int) -> int:
    now = datetime.utcnow()
    last = _last_submission.get(user_id)

    if last is None:
        return 0

    elapsed = (now - last).total_seconds()
    remaining = RATE_LIMIT_SECONDS - elapsed

    return max(0, int(remaining))


def record_submission(user_id: int):
    _last_submission[user_id] = datetime.utcnow()


# ────────────────────────────────────────────
# SOURCES
# ────────────────────────────────────────────

async def add_source(name: str, url: str, priority: int = 5, source_type: str = "rss") -> int:
    """Add a source (RSS or telegram_channel)."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT OR IGNORE INTO sources (name, type, url, active, priority) VALUES (?, ?, ?, 1, ?)",
            (name, source_type, url, priority)
        )
        await db.commit()
        return cursor.lastrowid


async def get_active_sources(source_type: str = None):
    """Get active sources. Optionally filter by type ('rss' or 'telegram_channel')."""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        if source_type:
            cursor = await db.execute(
                "SELECT * FROM sources WHERE active = 1 AND type = ? ORDER BY priority ASC",
                (source_type,)
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM sources WHERE active = 1 ORDER BY priority ASC"
            )
        return await cursor.fetchall()


async def set_source_active(source_id: int, active: bool):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE sources SET active = ? WHERE id = ?",
            (1 if active else 0, source_id)
        )
        await db.commit()

async def get_all_sources():
    """همه‌ی منابع (فعال و غیرفعال) — برای پنل مدیریت کانال‌ها در بات."""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM sources ORDER BY priority ASC, id ASC"
        )
        return await cursor.fetchall()


async def delete_source(source_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM sources WHERE id = ?", (source_id,))
        await db.commit()


# ────────────────────────────────────────────
# POSTS
# ────────────────────────────────────────────

async def is_source_url_seen(source_url: str) -> bool:
    """Check if a post with exact source_url already exists."""
    if not source_url:
        return False
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id FROM posts WHERE source_url = ? LIMIT 1", (source_url,)
        )
        return await cursor.fetchone() is not None


async def add_post(
    content_type: str,
    text: str,
    user_id: int = None,
    file_id: str = None,
    source_type: str = "user",
    source_name: str = None,
    source_url: str = None,
    channel_msg_id: int = None,
) -> int:
    norm = normalize_text(text or "")
    h    = make_hash(norm) if norm else ""
    similarity_flag = None
    similar_post_id = None
    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    async with aiosqlite.connect(DB_NAME) as db:

        # Duplicate check — only published posts count
        if h:
            cursor = await db.execute(
                "SELECT id FROM posts WHERE hash = ? AND status = 'published' LIMIT 1", (h,)
            )
            duplicate_row = await cursor.fetchone()

            if duplicate_row:
                similar_post_id = duplicate_row[0]
                similarity_flag = "DUPLICATE"
            else:
                cursor = await db.execute(
                    """SELECT id, normalized_text FROM posts
                       WHERE status = 'published'
                       ORDER BY id DESC LIMIT 50"""
                )
                recent_posts = await cursor.fetchall()

                for existing_id, existing_norm in recent_posts:
                    if not existing_norm:
                        continue
                    score = compute_similarity(norm, existing_norm)
                    if score >= 0.60:
                        similar_post_id = existing_id
                        similarity_flag = f"SIMILAR:{int(score * 100)}"
                        break

        cursor = await db.execute(
            """INSERT INTO posts
               (user_id, content_type, text, file_id, status,
                normalized_text, hash, similarity_flag, similar_post_id,
                source_type, source_name, source_url, channel_msg_id, created_at)
               VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, content_type, text, file_id,
             norm, h, similarity_flag, similar_post_id,
             source_type, source_name, source_url, channel_msg_id, created_at)
        )
        await db.commit()
        return cursor.lastrowid
    

async def check_duplicate(text: str):
        """
        Read-only duplicate check against already-published posts.
        Does NOT insert anything into the database — safe to call
        before deciding whether to publish something.

        Returns a tuple: (flag, similar_post_id, normalized_text, hash)
        flag is one of: None, "DUPLICATE", "SIMILAR:<percent>"
        """
        norm = normalize_text(text or "")
        h = make_hash(norm)

        # Empty text (e.g. a photo with no caption) can't be meaningfully
        # compared — skip the check entirely to avoid false "duplicate" hits.
        if not norm.strip():
            return None, None, norm, h

        similarity_flag = None
        similar_post_id = None

        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                "SELECT id FROM posts WHERE hash = ? AND status = 'published' LIMIT 1", (h,)
            )
            duplicate_row = await cursor.fetchone()

            if duplicate_row:
                similar_post_id = duplicate_row[0]
                similarity_flag = "DUPLICATE"
            else:
                cursor = await db.execute(
                    """SELECT id, normalized_text FROM posts
                    WHERE status = 'published'
                    ORDER BY id DESC LIMIT 50"""
                )
                recent_posts = await cursor.fetchall()

                for existing_id, existing_norm in recent_posts:
                    if not existing_norm:
                        continue
                    score = compute_similarity(norm, existing_norm)
                    if score >= 0.60:
                        similar_post_id = existing_id
                        similarity_flag = f"SIMILAR:{int(score * 100)}"
                        break

        return similarity_flag, similar_post_id, norm, h


async def add_published_post(
    content_type: str,
    text: str,
    file_id: str = None,
    source_type: str = "bale",
    source_name: str = None,
    source_url: str = None,
    channel_msg_id: int = None,
) -> int:
    """
    Insert a post that has ALREADY been published (used for content
    forwarded from Bale). Stored directly with status='published' so:
      1) it counts correctly in /status stats
      2) future duplicate checks (from users, RSS, or Bale) can match it
    """
    norm = normalize_text(text or "")
    h = make_hash(norm)

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """INSERT INTO posts
               (user_id, content_type, text, file_id, status,
                normalized_text, hash, similarity_flag, similar_post_id,
                source_type, source_name, source_url, channel_msg_id)
               VALUES (NULL, ?, ?, ?, 'published', ?, ?, NULL, NULL, ?, ?, ?, ?)""",
            (content_type, text, file_id, norm, h,
             source_type, source_name, source_url, channel_msg_id)
        )
        await db.commit()
        return cursor.lastrowid


async def get_post(post_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        return await cursor.fetchone()


async def hash_already_seen(h: str) -> bool:
    if not h:
        return False
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT id FROM posts WHERE hash = ? LIMIT 1", (h,)
        )
        return await cursor.fetchone() is not None


async def update_status(post_id: int, status: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE posts SET status = ? WHERE id = ?", (status, post_id)
        )
        await db.commit()


async def save_channel_msg_id(post_id: int, msg_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE posts SET channel_msg_id = ? WHERE id = ?", (msg_id, post_id)
        )
        await db.commit()


# ────────────────────────────────────────────
# STATS (for /status command)
# ────────────────────────────────────────────

async def get_stats() -> dict:
    today = date.today().strftime("%Y-%m-%d")

    async with aiosqlite.connect(DB_NAME) as db:

        cursor = await db.execute(
            "SELECT COUNT(*) FROM posts WHERE status = 'pending'"
        )
        pending = (await cursor.fetchone())[0]

        cursor = await db.execute(
            """SELECT COUNT(*) FROM logs
               WHERE action = 'published' AND timestamp LIKE ?""",
            (f"{today}%",)
        )
        published_today = (await cursor.fetchone())[0]

        cursor = await db.execute(
            """SELECT COUNT(*) FROM logs
               WHERE action = 'rejected' AND timestamp LIKE ?""",
            (f"{today}%",)
        )
        rejected_today = (await cursor.fetchone())[0]

        cursor = await db.execute(
            """SELECT COUNT(*) FROM logs l
               JOIN posts p ON l.post_id = p.id
               WHERE l.action = 'submitted'
               AND p.source_type = 'user'
               AND l.timestamp LIKE ?""",
            (f"{today}%",)
        )
        user_submitted_today = (await cursor.fetchone())[0]

        cursor = await db.execute(
            """SELECT COUNT(*) FROM logs
               WHERE action = 'rss_fetched' AND timestamp LIKE ?""",
            (f"{today}%",)
        )
        rss_today = (await cursor.fetchone())[0]

        cursor = await db.execute(
            """SELECT COUNT(*) FROM logs
               WHERE action = 'telegram_channel_fetched' AND timestamp LIKE ?""",
            (f"{today}%",)
        )
        telegram_today = (await cursor.fetchone())[0]

        cursor = await db.execute(
            "SELECT COUNT(*) FROM sources WHERE active = 1"
        )
        active_sources = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM blocked_users")
        blocked_count = (await cursor.fetchone())[0]

    return {
        "pending":              pending,
        "published_today":      published_today,
        "rejected_today":       rejected_today,
        "user_submitted_today": user_submitted_today,
        "rss_today":            rss_today,
        "telegram_today":       telegram_today,
        "active_sources":       active_sources,
        "blocked_users":        blocked_count,
    }


async def get_pending_posts(limit: int = 10) -> list:
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT id, user_id, source_type, source_name, content_type, text
               FROM posts
               WHERE status = 'pending'
               ORDER BY id ASC
               LIMIT ?""",
            (limit,)
        )
        return await cursor.fetchall()


# ────────────────────────────────────────────
# LOGS
# ────────────────────────────────────────────

async def log_action(post_id: int, action: str):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO logs (post_id, action, timestamp) VALUES (?, ?, ?)",
            (post_id, action, timestamp)
        )
        await db.commit()