from telegram import Update
from telegram.ext import ContextTypes

from config import (
    BOT_USERNAME,
    SUPPORT_USERNAME,
    MIN_TOPUP_FOR_BONUS,
    REFERRAL_BONUS,
)
from db import (
    save_user,
    get_user_balance,
    get_total_keys_info,
    apply_daily_billing,
    get_user_keys,
    get_key_by_id,
    create_vpn_key,
    activate_user_keys,
    add_balance,
    get_user_referrer,
    was_referral_bonus_given,
    mark_referral_bonus_given,
    delete_key_by_id,
)
from keyboards import (
    get_main_cabinet_keyboard,
    money_inline_keyboard,
    get_support_menu,
    get_keys_menu,
    get_after_topup_keyboard,
    get_connect_key_menu,
    get_user_delete_confirm_keyboard,
)


async def safe_edit(query, text, reply_markup=None, parse_mode=None):
    await query.message.edit_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode
    )


async def process_referral_bonus(telegram_id, bot):
    referrer_id = get_user_referrer(telegram_id)

    if referrer_id is None:
        return False

    if referrer_id == telegram_id:
        return False

    if was_referral_bonus_given(telegram_id):
        return False

    add_balance(telegram_id, REFERRAL_BONUS)
    add_balance(referrer_id, REFERRAL_BONUS)
    activate_user_keys(telegram_id)
    activate_user_keys(referrer_id)
    mark_referral_bonus_given(telegram_id)

    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=(
                f"🎁 Вам начислен реферальный бонус: {REFERRAL_BONUS}₽\n"
                f"Пригласивший вас пользователь тоже получил {REFERRAL_BONUS}₽"
            )
        )
    except Exception:
        pass

    try:
        await bot.send_message(
            chat_id=referrer_id,
            text=(
                f"🎁 Вам начислен реферальный бонус: {REFERRAL_BONUS}₽\n"
                f"Ваш приглашенный пользователь впервые пополнил баланс"
            )
        )
    except Exception:
        pass

    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    name = update.effective_user.first_name

    referrer_id = None
    if context.args:
        arg = context.args[0]
        if arg.startswith("ref_"):
            try:
                referrer_id = int(arg.split("_")[1])
            except ValueError:
                referrer_id = None

            if referrer_id == telegram_id:
                referrer_id = None

    is_new = save_user(telegram_id, name, referrer_id)
    apply_daily_billing(telegram_id)

    real_balance = get_user_balance(telegram_id)
    _, active_keys, _, approx_days = get_total_keys_info(telegram_id)
    status = "аккаунт работает" if active_keys > 0 and real_balance > 0 else "аккаунт не активен"

    greeting = f"Рады видеть вас, {name}!" if is_new else f"Рады видеть вас снова, {name}!"

    await update.message.reply_text(
        f"{greeting}\n\n"
        f"Ваш баланс {int(real_balance)}₽ (~{approx_days} дней), {status}\n"
        f"Тариф: 100₽ / 30 дней за 1 ключ\n"
        f"Срок уменьшается ежедневно\n\n"
        f"👥 Пригласите друзей — когда друг пополнит баланс от 100₽, вы оба получите по 30₽!\n\n"
        f"📣 Обязательно подпишитесь на наш канал (скоро появится)",
        reply_markup=get_main_cabinet_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Команды:\n/start — запустить бота\n/help — помощь"
    )


async def show_balance(update: Update):
    query = update.callback_query
    telegram_id = query.from_user.id
    apply_daily_billing(telegram_id)

    real_balance = get_user_balance(telegram_id)
    total_keys, active_keys, _, approx_days = get_total_keys_info(telegram_id)

    await safe_edit(
        query,
        f"⭐ Баланс\n\n"
        f"💰 Ваш баланс: {int(real_balance)}₽\n"
        f"🔑 Всего ключей: {total_keys}\n"
        f"✅ Активных ключей: {active_keys}\n"
        f"⏳ Остаток: ~{approx_days} дней\n\n"
        f"Тариф: 100₽ / 30 дней за 1 ключ",
        reply_markup=get_main_cabinet_keyboard()
    )


async def show_invite(update: Update):
    query = update.callback_query
    telegram_id = query.from_user.id
    invite_link = f"https://t.me/{BOT_USERNAME}?start=ref_{telegram_id}"

    await safe_edit(
        query,
        "👫 Приглашайте друзей!\n\n"
        "Отправьте другу ссылку ниж.\n"
        "Если новый пользователь придет по ней и впервые пополнит баланс от 100₽,\n"
        "вы оба получите по 30₽\n\n"
        f"Ваша ссылка:\n{invite_link}",
        reply_markup=get_main_cabinet_keyboard()
    )


async def render_keys_menu(query, telegram_id, selected_key_id=None):
    apply_daily_billing(telegram_id)
    user_keys = get_user_keys(telegram_id)

    await safe_edit(
        query,
        "🔑 Ваши ключи:\n\n"
        "ℹ️ Каждый ключ = 100₽ / 30 дней\n\n"
        "⇩ Нажмите, чтобы получить или изменить!⇩",
        reply_markup=get_keys_menu(user_keys, selected_key_id)
    )


async def show_keys_menu(update: Update):
    query = update.callback_query
    telegram_id = query.from_user.id
    await render_keys_menu(query, telegram_id)


async def show_key_info(update: Update, key_id: int):
    query = update.callback_query
    telegram_id = query.from_user.id

    user_keys = get_user_keys(telegram_id)
    if not user_keys:
        await render_keys_menu(query, telegram_id)
        return

    await render_keys_menu(query, telegram_id, selected_key_id=key_id)


async def handle_user_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    telegram_id = query.from_user.id

    if data == "create_key":
        balance = get_user_balance(telegram_id)
        key = create_vpn_key(telegram_id)

        if balance > 0:
            text = (
                f"✅ Новый ключ создан!\n\n"
                f"🔑 Ваш ключ:\n{key}\n\n"
                f"Тариф: 100₽ / 30 дней за 1 ключ"
            )
        else:
            text = (
                f"✅ Новый ключ создан!\n\n"
                f"🔑 Ваш ключ:\n{key}\n\n"
                f"⚠️ Сейчас ключ остановлен, потому что баланс равен 0₽\n"
                f"После пополнения баланса ключ автоматически активируется"
            )

        await safe_edit(
            query,
            text,
            reply_markup=get_after_topup_keyboard()
        )
        return True

    elif data == "balance":
        await show_balance(update)
        return True

    elif data == "up_balance":
        await safe_edit(
            query,
            "💳 Пополнение баланса\n\nВыберите сумму пополнения:",
            reply_markup=money_inline_keyboard()
        )
        return True

    elif data.startswith("topup_"):
        amount = int(data.split("_")[1])

        add_balance(telegram_id, amount)
        activate_user_keys(telegram_id)

        bonus_given = False
        if amount >= MIN_TOPUP_FOR_BONUS:
            bonus_given = await process_referral_bonus(telegram_id, context.bot)

        new_balance = get_user_balance(telegram_id)

        text = (
            f"✅ Баланс пополнен на {amount}₽\n"
            f"💰 Текущий баланс: {int(new_balance)}₽\n\n"
            f"Если у вас были остановленные ключи, они снова активированы"
        )

        if bonus_given:
            text += "\n\n🎁 Реферальный бонус 30₽ начислен вам и пригласившему вас пользователю"

        await safe_edit(
            query,
            text,
            reply_markup=get_after_topup_keyboard()
        )
        return True

    elif data == "invite":
        await show_invite(update)
        return True

    elif data == "help":
        await safe_edit(
            query,
            "🛟 Поддержка\n\n"
            "Если есть проблемы с подключением, ключом или балансом — напишите нам",
            reply_markup=get_support_menu(SUPPORT_USERNAME)
        )
        return True

    elif data == "keys_menu":
        await show_keys_menu(update)
        return True

    elif data.startswith("key_"):
        key_id = int(data.split("_")[1])
        await show_key_info(update, key_id)
        return True

    elif data == "main_menu":
        await safe_edit(
            query,
            "🏠 Главное меню",
            reply_markup=get_main_cabinet_keyboard()
        )
        return True

    elif data.startswith("connect_key_"):
        key_id = int(data.split("_")[2])
        result = get_key_by_id(key_id, telegram_id)

        if result is None:
            await render_keys_menu(query, telegram_id)
            return True

        key_value, _, status = result

        if status != "active":
            await safe_edit(
                query,
                "⚠️ Этот ключ сейчас остановлен из-за нулевого баланса\n\n"
                "Пополните баланс, и ключ снова станет активным",
                reply_markup=get_after_topup_keyboard()
            )
            return True

        await safe_edit(
            query,
            "📲 Подключение VPN\n\n"
            "Скопируйте ключ ниже и вставьте его в приложение VPN:\n\n"
            f"`{key_value}`",
            reply_markup=get_connect_key_menu(),
            parse_mode="Markdown"
        )
        return True

    elif data.startswith("ask_delete_key_"):
        key_id = int(data.split("_")[3])
        await safe_edit(
            query,
            "⚠️ Подтверждение удаления\n\n"
            "Ты точно хочешь удалить этот ключ?",
            reply_markup=get_user_delete_confirm_keyboard(key_id)
        )
        return True

    elif data.startswith("confirm_delete_key_"):
        key_id = int(data.split("_")[3])
        deleted = delete_key_by_id(key_id, telegram_id)

        if not deleted:
            await render_keys_menu(query, telegram_id)
            return True

        await render_keys_menu(query, telegram_id)
        return True

    elif data.startswith("replace_key_"):
        key_id = int(data.split("_")[2])

        old_key = get_key_by_id(key_id, telegram_id)
        if old_key is None:
            await render_keys_menu(query, telegram_id)
            return True

        delete_key_by_id(key_id, telegram_id)
        new_key = create_vpn_key(telegram_id)

        await safe_edit(
            query,
            "🌍 Ключ изменен\n\n"
            f"🔑 Новый ключ:\n{new_key}\n\n"
            "Скопируйте его и вставьте в приложение VPN",
            reply_markup=get_connect_key_menu()
        )
        return True

    return False