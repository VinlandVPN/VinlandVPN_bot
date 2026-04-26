import asyncio
from telegram import Bot

from config import BOT_TOKEN
from db import (
    init_db,
    get_all_user_ids,
    apply_daily_billing,
    get_user_balance,
    get_total_keys_info,
    get_notification_flags,
    set_low_balance_notified,
    set_zero_balance_notified,
)
from keyboards import (
    get_low_balance_notification_keyboard,
    get_zero_balance_notification_keyboard,
)

LOW_DAYS_THRESHOLD = 3


async def process_user(bot: Bot, telegram_id: int):
    apply_daily_billing(telegram_id)

    balance = get_user_balance(telegram_id)
    total_keys, active_keys, _, approx_days = get_total_keys_info(telegram_id)
    low_notified, zero_notified = get_notification_flags(telegram_id)

    if total_keys <= 0:
        return

    if balance <= 0:
        if zero_notified == 0:
            try:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=(
                        "❌ У вас закончился баланс\n\n"
                        "Чтобы продолжить пользоваться сервисом, пополните баланс"
                    ),
                    reply_markup=get_zero_balance_notification_keyboard()
                )
                set_zero_balance_notified(telegram_id, 1)
                set_low_balance_notified(telegram_id, 1)
            except Exception:
                pass
        return

    if active_keys > 0 and approx_days <= LOW_DAYS_THRESHOLD:
        if low_notified == 0:
            try:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=(
                        f"⚠️ У вас осталось примерно {approx_days} дн. работы VPN\n\n"
                        "Пополните баланс заранее, чтобы не потерять доступ"
                    ),
                    reply_markup=get_low_balance_notification_keyboard()
                )
                set_low_balance_notified(telegram_id, 1)
            except Exception:
                pass

    if balance > 0 and zero_notified == 1:
        set_zero_balance_notified(telegram_id, 0)


async def main():
    init_db()
    bot = Bot(token=BOT_TOKEN)

    user_ids = get_all_user_ids()
    for telegram_id in user_ids:
        await process_user(bot, telegram_id)


if __name__ == "__main__":
    asyncio.run(main())