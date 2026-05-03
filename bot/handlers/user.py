from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from bot.config import (
    BOT_USERNAME,
    SUPPORT_USERNAME,
    MIN_TOPUP_FOR_BONUS,
    REFERRAL_BONUS,
)
from bot.db import (
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
from bot.keyboards import (
    get_main_cabinet_keyboard,
    money_inline_keyboard,
    get_support_menu,
    get_keys_menu,
    get_after_topup_keyboard,
    get_connect_key_menu,
    get_user_delete_confirm_keyboard,
)

user_router = Router()


async def safe_edit(callback: CallbackQuery, text, reply_markup=None, parse_mode=None):
    try:
        await callback.message.edit_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except TelegramBadRequest:
        await callback.message.answer(
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
                f"Пригласивший вас пользователь тоже получил {REFERRAL_BONUS}₽."
            )
        )
    except Exception:
        pass

    try:
        await bot.send_message(
            chat_id=referrer_id,
            text=(
                f"🎁 Вам начислен реферальный бонус: {REFERRAL_BONUS}₽\n"
                f"Ваш приглашенный пользователь впервые пополнил баланс."
            )
        )
    except Exception:
        pass

    return True


@user_router.message(Command("start"))
async def start(message: Message, command: CommandObject):
    telegram_id = message.from_user.id
    name = message.from_user.first_name

    referrer_id = None
    if command.args and command.args.startswith("ref_"):
        try:
            referrer_id = int(command.args.split("_")[1])
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

    await message.answer(
        f"{greeting}\n\n"
        f"Ваш баланс {int(real_balance)}₽ (~{approx_days} дней), {status}\n"
        f"Тариф: 100₽ / 30 дней за 1 ключ\n"
        f"Срок уменьшается ежедневно\n\n"
        f"👥 Пригласите друзей — когда друг пополнит баланс от 100₽, вы оба получите по 30₽!\n\n"
        f"📣 Обязательно подпишитесь на наш канал (скоро появится)",
        reply_markup=get_main_cabinet_keyboard()
    )


@user_router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "Команды:\n/start — запустить бота\n/help — помощь"
    )


async def render_keys_menu(callback: CallbackQuery, telegram_id, selected_key_id=None):
    apply_daily_billing(telegram_id)
    user_keys = get_user_keys(telegram_id)

    await safe_edit(
        callback,
        "🔑 Ваши ключи:\n\n"
        "ℹ️ Каждый ключ = 100₽ / 30 дней\n\n"
        "⇩ Нажмите, чтобы получить или изменить!⇩",
        reply_markup=get_keys_menu(user_keys, selected_key_id)
    )


@user_router.callback_query(F.data == "balance")
async def show_balance(callback: CallbackQuery):
    await callback.answer()

    telegram_id = callback.from_user.id
    apply_daily_billing(telegram_id)

    real_balance = get_user_balance(telegram_id)
    total_keys, active_keys, _, approx_days = get_total_keys_info(telegram_id)

    await safe_edit(
        callback,
        f"⭐ Баланс\n\n"
        f"💰 Ваш баланс: {int(real_balance)}₽\n"
        f"🔑 Всего ключей: {total_keys}\n"
        f"✅ Активных ключей: {active_keys}\n"
        f"⏳ Остаток: ~{approx_days} дней\n\n"
        f"Тариф: 100₽ / 30 дней за 1 ключ",
        reply_markup=get_main_cabinet_keyboard()
    )


@user_router.callback_query(F.data == "invite")
async def show_invite(callback: CallbackQuery):
    await callback.answer()

    telegram_id = callback.from_user.id
    invite_link = f"https://t.me/{BOT_USERNAME}?start=ref_{telegram_id}"

    await safe_edit(
        callback,
        "👫 Приглашайте друзей!\n\n"
        "Отправьте другу ссылку ниже.\n"
        "Если новый пользователь придет по ней и впервые пополнит баланс от 100₽,\n"
        "вы оба получите по 30₽.\n\n"
        f"Ваша ссылка:\n{invite_link}",
        reply_markup=get_main_cabinet_keyboard()
    )


@user_router.callback_query(F.data == "up_balance")
async def show_topup(callback: CallbackQuery):
    await callback.answer()

    await safe_edit(
        callback,
        "💳 Пополнение баланса\n\nВыберите сумму пополнения:",
        reply_markup=money_inline_keyboard()
    )


@user_router.callback_query(F.data.startswith("topup_"))
async def topup(callback: CallbackQuery):
    await callback.answer()

    telegram_id = callback.from_user.id
    amount = int(callback.data.split("_")[1])

    add_balance(telegram_id, amount)
    activate_user_keys(telegram_id)

    bonus_given = False
    if amount >= MIN_TOPUP_FOR_BONUS:
        bonus_given = await process_referral_bonus(telegram_id, callback.bot)

    new_balance = get_user_balance(telegram_id)

    text = (
        f"✅ Баланс пополнен на {amount}₽\n"
        f"💰 Текущий баланс: {int(new_balance)}₽\n\n"
        f"Если у вас были остановленные ключи, они снова активированы."
    )

    if bonus_given:
        text += "\n\n🎁 Реферальный бонус 30₽ начислен вам и пригласившему вас пользователю."

    await safe_edit(callback, text, reply_markup=get_after_topup_keyboard())


@user_router.callback_query(F.data == "help")
async def show_support(callback: CallbackQuery):
    await callback.answer()

    await safe_edit(
        callback,
        "🛟 Поддержка\n\n"
        "Если есть проблемы с подключением, ключом или балансом — напишите нам.",
        reply_markup=get_support_menu(SUPPORT_USERNAME)
    )


@user_router.callback_query(F.data == "keys_menu")
async def show_keys_menu(callback: CallbackQuery):
    await callback.answer()
    await render_keys_menu(callback, callback.from_user.id)


@user_router.callback_query(F.data.startswith("key_"))
async def show_key_info(callback: CallbackQuery):
    await callback.answer()

    key_id = int(callback.data.split("_")[1])
    await render_keys_menu(callback, callback.from_user.id, selected_key_id=key_id)


@user_router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery):
    await callback.answer()

    await safe_edit(
        callback,
        "🏠 Главное меню",
        reply_markup=get_main_cabinet_keyboard()
    )


@user_router.callback_query(F.data == "create_key")
async def create_key(callback: CallbackQuery):
    await callback.answer()

    telegram_id = callback.from_user.id
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
            f"⚠️ Сейчас ключ остановлен, потому что баланс равен 0₽.\n"
            f"После пополнения баланса ключ автоматически активируется."
        )

    await safe_edit(callback, text, reply_markup=get_after_topup_keyboard())


@user_router.callback_query(F.data.startswith("connect_key_"))
async def connect_key(callback: CallbackQuery):
    await callback.answer()

    telegram_id = callback.from_user.id
    key_id = int(callback.data.split("_")[2])
    result = get_key_by_id(key_id, telegram_id)

    if result is None:
        await render_keys_menu(callback, telegram_id)
        return

    key_value, _, status = result

    if status != "active":
        await safe_edit(
            callback,
            "⚠️ Этот ключ сейчас остановлен из-за нулевого баланса.\n\n"
            "Пополните баланс, и ключ снова станет активным.",
            reply_markup=get_after_topup_keyboard()
        )
        return

    await safe_edit(
        callback,
        "📲 Подключение VPN\n\n"
        "Скопируйте ключ ниже и вставьте его в приложение VPN:\n\n"
        f"`{key_value}`",
        reply_markup=get_connect_key_menu(),
        parse_mode="Markdown"
    )


@user_router.callback_query(F.data.startswith("ask_delete_key_"))
async def ask_delete_key(callback: CallbackQuery):
    await callback.answer()

    key_id = int(callback.data.split("_")[3])

    await safe_edit(
        callback,
        "⚠️ Подтверждение удаления\n\n"
        "Ты точно хочешь удалить этот ключ?",
        reply_markup=get_user_delete_confirm_keyboard(key_id)
    )


@user_router.callback_query(F.data.startswith("confirm_delete_key_"))
async def confirm_delete_key(callback: CallbackQuery):
    await callback.answer()

    telegram_id = callback.from_user.id
    key_id = int(callback.data.split("_")[3])
    delete_key_by_id(key_id, telegram_id)

    await render_keys_menu(callback, telegram_id)


@user_router.callback_query(F.data.startswith("replace_key_"))
async def replace_key(callback: CallbackQuery):
    await callback.answer()

    telegram_id = callback.from_user.id
    key_id = int(callback.data.split("_")[2])

    if get_key_by_id(key_id, telegram_id) is None:
        await render_keys_menu(callback, telegram_id)
        return

    delete_key_by_id(key_id, telegram_id)
    new_key = create_vpn_key(telegram_id)

    await safe_edit(
        callback,
        "🌍 Ключ изменен\n\n"
        f"🔑 Новый ключ:\n{new_key}\n\n"
        "Скопируйте его и вставьте в приложение VPN.",
        reply_markup=get_connect_key_menu()
    )