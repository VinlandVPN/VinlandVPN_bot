import sqlite3
import random
from datetime import datetime

from bot.config import DAILY_PRICE_PER_KEY


def get_today_str():
    return datetime.now().strftime("%Y-%m-%d")


def get_now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_column_exists(cursor, table_name, column_name, column_definition):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]

    if column_name not in columns:
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        )


def init_db():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        first_name TEXT,
        balance REAL DEFAULT 0,
        referrer_id INTEGER,
        referral_bonus_given INTEGER DEFAULT 0,
        last_billing_date TEXT,
        low_balance_notified INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vpn_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        key TEXT,
        created_at TEXT,
        is_deleted INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        action TEXT,
        details TEXT,
        created_at TEXT
    )
    """)

    ensure_column_exists(cursor, "users", "zero_balance_notified", "INTEGER DEFAULT 0")
    ensure_column_exists(cursor, "users", "low_balance_notified", "INTEGER DEFAULT 0")

    conn.commit()
    conn.close()


def add_admin_log(admin_id, action, details=""):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO admin_logs (admin_id, action, details, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (admin_id, action, details, get_now_str()),
    )

    conn.commit()
    conn.close()


def get_admin_logs(limit=30):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT admin_id, action, details, created_at
        FROM admin_logs
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()

    conn.close()
    return rows


def save_user(telegram_id, first_name, referrer_id=None):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT telegram_id FROM users WHERE telegram_id = ?", (telegram_id,)
    )
    exists = cursor.fetchone()
    is_new = exists is None

    if is_new:
        cursor.execute(
            """
            INSERT INTO users (
                telegram_id, first_name, balance, referrer_id,
                referral_bonus_given, last_billing_date,
                low_balance_notified, zero_balance_notified
            )
            VALUES (?, ?, 0, ?, 0, ?, 0, 0)
            """,
            (telegram_id, first_name, referrer_id, get_today_str()),
        )

    conn.commit()
    conn.close()
    return is_new


def get_all_user_ids():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute("SELECT telegram_id FROM users")
    rows = cursor.fetchall()

    conn.close()
    return [row[0] for row in rows]


def get_user_referrer(telegram_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT referrer_id FROM users WHERE telegram_id = ?", (telegram_id,)
    )
    result = cursor.fetchone()

    conn.close()
    return result[0] if result else None


def was_referral_bonus_given(telegram_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT referral_bonus_given FROM users WHERE telegram_id = ?", (telegram_id,)
    )
    result = cursor.fetchone()

    conn.close()
    return bool(result and result[0] == 1)


def mark_referral_bonus_given(telegram_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET referral_bonus_given = 1 WHERE telegram_id = ?",
        (telegram_id,),
    )

    conn.commit()
    conn.close()


def get_user_balance(telegram_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute("SELECT balance FROM users WHERE telegram_id = ?", (telegram_id,))
    result = cursor.fetchone()

    conn.close()
    return float(result[0]) if result else 0.0


def add_balance(telegram_id, amount):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET balance = balance + ?,
            low_balance_notified = 0,
            zero_balance_notified = 0
        WHERE telegram_id = ?
        """,
        (amount, telegram_id),
    )

    conn.commit()
    conn.close()


def get_users_count():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]

    conn.close()
    return count


def get_total_keys_count():
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM vpn_keys WHERE is_deleted = 0")
    count = cursor.fetchone()[0]

    conn.close()
    return count


def get_users_list(limit=20):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT telegram_id, first_name, balance
        FROM users
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    users = cursor.fetchall()

    conn.close()
    return users


def get_user_brief(telegram_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT telegram_id, first_name, balance
        FROM users
        WHERE telegram_id = ?
        """,
        (telegram_id,),
    )
    result = cursor.fetchone()

    conn.close()
    return result


def get_last_billing_date(telegram_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT last_billing_date FROM users WHERE telegram_id = ?", (telegram_id,)
    )
    result = cursor.fetchone()

    conn.close()
    return result[0] if result and result[0] else get_today_str()


def set_last_billing_date(telegram_id, date_str):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET last_billing_date = ? WHERE telegram_id = ?",
        (date_str, telegram_id),
    )

    conn.commit()
    conn.close()


def get_notification_flags(telegram_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT low_balance_notified, zero_balance_notified
        FROM users
        WHERE telegram_id = ?
        """,
        (telegram_id,),
    )
    result = cursor.fetchone()

    conn.close()

    if not result:
        return 0, 0

    return int(result[0] or 0), int(result[1] or 0)


def set_low_balance_notified(telegram_id, value: int):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET low_balance_notified = ? WHERE telegram_id = ?",
        (value, telegram_id),
    )

    conn.commit()
    conn.close()


def set_zero_balance_notified(telegram_id, value: int):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET zero_balance_notified = ? WHERE telegram_id = ?",
        (value, telegram_id),
    )

    conn.commit()
    conn.close()


def create_vpn_key(telegram_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    key = f"vpn_{random.randint(100000, 999999)}"
    balance = get_user_balance(telegram_id)
    status = "active" if balance > 0 else "paused"

    cursor.execute(
        """
        INSERT INTO vpn_keys (user_id, key, created_at, is_deleted, status)
        VALUES (?, ?, ?, 0, ?)
        """,
        (telegram_id, key, get_today_str(), status),
    )

    conn.commit()
    conn.close()
    return key


def get_user_keys(telegram_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, key, created_at, status
        FROM vpn_keys
        WHERE user_id = ? AND is_deleted = 0
        ORDER BY id ASC
        """,
        (telegram_id,),
    )
    keys = cursor.fetchall()

    conn.close()
    return keys


def get_key_by_id(key_id, telegram_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT key, created_at, status
        FROM vpn_keys
        WHERE id = ? AND user_id = ? AND is_deleted = 0
        """,
        (key_id, telegram_id),
    )
    result = cursor.fetchone()

    conn.close()
    return result


def delete_key_by_id(key_id, telegram_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE vpn_keys
        SET is_deleted = 1
        WHERE id = ? AND user_id = ? AND is_deleted = 0
        """,
        (key_id, telegram_id),
    )

    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    return deleted > 0


def admin_delete_key_by_id(key_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE vpn_keys
        SET is_deleted = 1
        WHERE id = ? AND is_deleted = 0
        """,
        (key_id,),
    )

    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    return deleted > 0


def get_active_keys_count(telegram_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM vpn_keys
        WHERE user_id = ? AND is_deleted = 0 AND status = 'active'
        """,
        (telegram_id,),
    )
    count = cursor.fetchone()[0]

    conn.close()
    return count


def pause_user_keys(telegram_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE vpn_keys
        SET status = 'paused'
        WHERE user_id = ? AND is_deleted = 0
        """,
        (telegram_id,),
    )

    conn.commit()
    conn.close()


def activate_user_keys(telegram_id):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE vpn_keys
        SET status = 'active'
        WHERE user_id = ? AND is_deleted = 0
        """,
        (telegram_id,),
    )

    conn.commit()
    conn.close()


def apply_daily_billing(telegram_id):
    today = datetime.now().date()
    last_date_str = get_last_billing_date(telegram_id)
    last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()

    days_passed = (today - last_date).days
    if days_passed <= 0:
        return

    active_keys = get_active_keys_count(telegram_id)
    if active_keys <= 0:
        set_last_billing_date(telegram_id, today.strftime("%Y-%m-%d"))
        return

    total_charge = days_passed * active_keys * DAILY_PRICE_PER_KEY

    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()

    cursor.execute("SELECT balance FROM users WHERE telegram_id = ?", (telegram_id,))
    result = cursor.fetchone()
    current_balance = float(result[0]) if result else 0.0

    new_balance = current_balance - total_charge
    if new_balance < 0:
        new_balance = 0.0

    cursor.execute(
        "UPDATE users SET balance = ?, last_billing_date = ? WHERE telegram_id = ?",
        (new_balance, today.strftime("%Y-%m-%d"), telegram_id),
    )

    conn.commit()
    conn.close()

    if new_balance <= 0:
        pause_user_keys(telegram_id)
    else:
        activate_user_keys(telegram_id)


def get_total_keys_info(telegram_id):
    user_keys = get_user_keys(telegram_id)

    total_keys = len(user_keys)
    active_keys = sum(1 for _, _, _, status in user_keys if status == "active")

    balance = get_user_balance(telegram_id)
    daily_total = active_keys * DAILY_PRICE_PER_KEY

    if active_keys > 0 and daily_total > 0:
        approx_days = int(balance / daily_total)
    else:
        approx_days = 0

    visual_balance = int(balance)

    return total_keys, active_keys, visual_balance, approx_days


def format_date_ru(date_str):
    if not date_str:
        return "не указано"

    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%d-%m-%Y")
