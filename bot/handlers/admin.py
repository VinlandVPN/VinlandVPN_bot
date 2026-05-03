from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.config import ADMIN_ID, CHANNEL_URL
from bot.db import (
    get_users_count,
    get_total_keys_count,
    get_users_list,
    get_user_brief,
    add_balance,
    activate_user_keys,
    get_user_balance,
    get_user_keys,
    format_date_ru,
    get_all_user_ids,
    admin_delete_key_by_id,
    get_key_by_id,
    add_admin_log,
    get_admin_logs,
)
from bot.keyboards import (
    get_admin_keyboard,
    get_admin_back_keyboard,
    get_admin_balance_amounts_keyboard,
    get_admin_user_keys_keyboard,
    get_admin_single_key_keyboard,
    get_admin_delete_confirm_keyboard,
    get_broadcast_mode_keyboard,
    get_broadcast_preview_plain_keyboard,
    get_broadcast_preview_buttons_keyboard,
    get_broadcast_user_keyboard,
)

admin_router = Router()


class AdminStates(StatesGroup):
    waiting_balance_user_id = State()
    waiting_balance_custom_amount = State()
    waiting_keys_user_id = State()
    waiting_delete_key_user_id = State()
    waiting_delete_key_id = State()
    waiting_broadcast_text = State()


def is_admin(telegram_id):
    return telegram_id == ADMIN_ID


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


@admin_router.message(Command("admin"))
async def admin_command(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    await state.clear()

    users_count = get_users_count()
    keys_count = get_total_keys_count()

    await message.answer(
        f"🛠 Админка\n\n"
        f"👥 Пользователей: {users_count}\n"
        f"🔑 Ключей: {keys_count}",
        reply_markup=get_admin_keyboard()
    )


@admin_router.callback_query(F.data == "admin_main")
async def show_admin_main(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await callback.answer()
    await state.clear()

    users_count = get_users_count()
    keys_count = get_total_keys_count()

    await safe_edit(
        callback,
        f"🛠 Админка\n\n"
        f"👥 Пользователей: {users_count}\n"
        f"🔑 Ключей: {keys_count}",
        reply_markup=get_admin_keyboard()
    )


@admin_router.callback_query(F.data == "admin_users")
async def show_admin_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    await callback.answer()

    users = get_users_list()

    if not users:
        await safe_edit(
            callback,
            "👥 Пользователей пока нет.",
            reply_markup=get_admin_keyboard()
        )
        return

    lines = ["👥 Последние пользователи:\n"]
    for tg_id, first_name, balance in users:
        lines.append(f"{first_name} | {tg_id} | {int(balance)}₽")

    await safe_edit(
        callback,
        "\n".join(lines),
        reply_markup=get_admin_keyboard()
    )


@admin_router.callback_query(F.data == "admin_logs")
async def show_admin_logs(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    await callback.answer()

    logs = get_admin_logs(25)

    if not logs:
        await safe_edit(
            callback,
            "📜 Логов пока нет.",
            reply_markup=get_admin_keyboard()
        )
        return

    lines = ["📜 Последние действия админа:\n"]
    for admin_id, action, details, created_at in logs:
        details_part = f" | {details}" if details else ""
        lines.append(f"{created_at} | {action}{details_part}")

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:3950] + "\n\n... лог обрезан"

    await safe_edit(
        callback,
        text,
        reply_markup=get_admin_keyboard()
    )


@admin_router.callback_query(F.data == "admin_add_balance")
async def start_admin_add_balance(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await callback.answer()
    await state.clear()
    await state.set_state(AdminStates.waiting_balance_user_id)

    await safe_edit(
        callback,
        "💰 Начисление баланса\n\n"
        "Отправь Telegram ID пользователя, которому хочешь начислить баланс.",
        reply_markup=get_admin_back_keyboard()
    )


@admin_router.message(AdminStates.waiting_balance_user_id)
async def admin_receive_balance_user_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    try:
        target_user_id = int(message.text.strip())
    except ValueError:
        await message.answer("ID должен быть числом. Попробуй еще раз.")
        return

    user_info = get_user_brief(target_user_id)
    if user_info is None:
        await message.answer("Пользователь с таким Telegram ID не найден. Попробуй еще раз.")
        return

    _, first_name, balance = user_info

    await state.update_data(admin_target_user_id=target_user_id)

    await message.answer(
        f"💰 Начисление баланса\n\n"
        f"Пользователь найден:\n"
        f"{first_name} | {target_user_id} | {int(balance)}₽\n\n"
        f"Теперь выбери сумму:",
        reply_markup=get_admin_balance_amounts_keyboard()
    )


@admin_router.callback_query(F.data.startswith("admin_balance_amount_"))
async def admin_add_balance_amount(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await callback.answer()

    suffix = callback.data.split("_")[-1]
    data = await state.get_data()
    target_user_id = data.get("admin_target_user_id")

    if not target_user_id:
        await safe_edit(
            callback,
            "Сессия начисления баланса сброшена. Нажми заново «Начислить баланс».",
            reply_markup=get_admin_keyboard()
        )
        await state.clear()
        return

    if suffix == "other":
        await state.set_state(AdminStates.waiting_balance_custom_amount)
        await safe_edit(
            callback,
            f"💰 Начисление баланса\n\n"
            f"Пользователь: {target_user_id}\n\n"
            f"Введи сумму вручную:",
            reply_markup=get_admin_back_keyboard()
        )
        return

    amount = int(suffix)

    add_balance(target_user_id, amount)
    activate_user_keys(target_user_id)
    new_balance = get_user_balance(target_user_id)

    add_admin_log(
        callback.from_user.id,
        "add_balance_button",
        f"user={target_user_id}, amount={amount}"
    )

    await safe_edit(
        callback,
        f"✅ Баланс начислен.\n\n"
        f"Пользователь: {target_user_id}\n"
        f"Сумма: {amount}₽\n"
        f"Новый баланс: {int(new_balance)}₽",
        reply_markup=get_admin_keyboard()
    )

    try:
        await callback.bot.send_message(
            chat_id=target_user_id,
            text=f"💰 Вам начислен баланс: {amount}₽\nТекущий баланс: {int(new_balance)}₽"
        )
    except Exception:
        pass

    await state.clear()


@admin_router.message(AdminStates.waiting_balance_custom_amount)
async def admin_receive_custom_balance(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    try:
        amount = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("Сумма должна быть числом. Попробуй еще раз.")
        return

    if amount <= 0:
        await message.answer("Сумма должна быть больше 0. Попробуй еще раз.")
        return

    data = await state.get_data()
    target_user_id = data.get("admin_target_user_id")

    if not target_user_id:
        await message.answer("Сессия сброшена. Нажми заново «Начислить баланс».")
        await state.clear()
        return

    add_balance(target_user_id, amount)
    activate_user_keys(target_user_id)
    new_balance = get_user_balance(target_user_id)

    add_admin_log(
        message.from_user.id,
        "add_balance_custom",
        f"user={target_user_id}, amount={amount}"
    )

    await message.answer(
        f"✅ Баланс начислен.\n\n"
        f"Пользователь: {target_user_id}\n"
        f"Сумма: {int(amount)}₽\n"
        f"Новый баланс: {int(new_balance)}₽"
    )

    try:
        await message.bot.send_message(
            chat_id=target_user_id,
            text=f"💰 Вам начислен баланс: {int(amount)}₽\nТекущий баланс: {int(new_balance)}₽"
        )
    except Exception:
        pass

    await state.clear()


@admin_router.callback_query(F.data == "admin_user_keys")
async def start_admin_user_keys(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await callback.answer()
    await state.clear()
    await state.set_state(AdminStates.waiting_keys_user_id)

    await safe_edit(
        callback,
        "🔑 Ключи пользователя\n\n"
        "Отправь Telegram ID пользователя, чьи ключи хочешь посмотреть.",
        reply_markup=get_admin_back_keyboard()
    )


@admin_router.message(AdminStates.waiting_keys_user_id)
async def admin_receive_keys_user_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    try:
        target_user_id = int(message.text.strip())
    except ValueError:
        await message.answer("ID должен быть числом. Попробуй еще раз.")
        return

    user_info = get_user_brief(target_user_id)
    if user_info is None:
        await message.answer("Пользователь с таким Telegram ID не найден. Попробуй еще раз.")
        return

    keys = get_user_keys(target_user_id)
    await state.update_data(admin_selected_key_owner_id=target_user_id)

    if not keys:
        await message.answer(
            f"У пользователя {target_user_id} нет ключей.",
            reply_markup=get_admin_back_keyboard()
        )
        await state.clear()
        return

    _, first_name, balance = user_info

    await message.answer(
        f"🔑 Ключи пользователя\n\n"
        f"{first_name} | {target_user_id} | {int(balance)}₽\n\n"
        f"Выбери нужный ключ:",
        reply_markup=get_admin_user_keys_keyboard(keys)
    )

    await state.clear()


async def show_admin_user_keys_screen(callback: CallbackQuery, owner_id: int, state: FSMContext):
    user_info = get_user_brief(owner_id)

    if user_info is None:
        await safe_edit(callback, "Пользователь не найден.", reply_markup=get_admin_back_keyboard())
        return

    _, first_name, balance = user_info
    keys = get_user_keys(owner_id)

    if not keys:
        await safe_edit(
            callback,
            f"🔑 Ключи пользователя\n\n"
            f"{first_name} | {owner_id} | {int(balance)}₽\n\n"
            f"У пользователя нет ключей.",
            reply_markup=get_admin_back_keyboard()
        )
        return

    await state.update_data(admin_selected_key_owner_id=owner_id)

    await safe_edit(
        callback,
        f"🔑 Ключи пользователя\n\n"
        f"{first_name} | {owner_id} | {int(balance)}₽\n\n"
        f"Выбери нужный ключ:",
        reply_markup=get_admin_user_keys_keyboard(keys)
    )


@admin_router.callback_query(F.data == "admin_user_keys_back")
async def admin_user_keys_back(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await callback.answer()

    data = await state.get_data()
    owner_id = data.get("admin_selected_key_owner_id")

    if owner_id:
        await show_admin_user_keys_screen(callback, owner_id, state)
    else:
        await safe_edit(callback, "Владелец ключей не выбран.", reply_markup=get_admin_keyboard())


@admin_router.callback_query(F.data.startswith("admin_key_select_"))
async def admin_key_select(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await callback.answer()

    key_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    owner_id = data.get("admin_selected_key_owner_id")

    if not owner_id:
        await safe_edit(
            callback,
            "Не выбран владелец ключей. Зайди заново в раздел «Ключи пользователя».",
            reply_markup=get_admin_keyboard()
        )
        return

    key_info = get_key_by_id(key_id, owner_id)

    if key_info is None:
        await safe_edit(callback, "Ключ не найден.", reply_markup=get_admin_back_keyboard())
        return

    key_value, created_at, status = key_info
    status_text = "активен" if status == "active" else "остановлен"
    created_at_ru = format_date_ru(created_at)

    await safe_edit(
        callback,
        f"🔑 Информация о ключе\n\n"
        f"ID ключа: {key_id}\n"
        f"Ключ: {key_value}\n"
        f"Статус: {status_text}\n"
        f"Создан: {created_at_ru}",
        reply_markup=get_admin_single_key_keyboard(key_id)
    )


@admin_router.callback_query(F.data.startswith("admin_key_ask_delete_"))
async def admin_key_ask_delete(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    await callback.answer()

    key_id = int(callback.data.split("_")[-1])

    await safe_edit(
        callback,
        "⚠️ Подтверждение удаления\n\nТы точно хочешь удалить этот ключ?",
        reply_markup=get_admin_delete_confirm_keyboard(key_id)
    )


@admin_router.callback_query(F.data.startswith("admin_key_confirm_delete_"))
async def admin_key_confirm_delete(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await callback.answer()

    key_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    owner_id = data.get("admin_selected_key_owner_id")

    if not owner_id:
        await safe_edit(
            callback,
            "Не выбран владелец ключей. Зайди заново в раздел «Ключи пользователя».",
            reply_markup=get_admin_keyboard()
        )
        return

    key_info = get_key_by_id(key_id, owner_id)
    if key_info is None:
        await safe_edit(callback, "Ключ уже не найден.", reply_markup=get_admin_keyboard())
        return

    deleted = admin_delete_key_by_id(key_id)
    if not deleted:
        await safe_edit(callback, "Не удалось удалить ключ.", reply_markup=get_admin_keyboard())
        return

    add_admin_log(
        callback.from_user.id,
        "delete_key_button",
        f"user={owner_id}, key_id={key_id}"
    )

    try:
        await callback.bot.send_message(
            chat_id=owner_id,
            text="🗑 Один из ваших ключей был удален администратором."
        )
    except Exception:
        pass

    keys = get_user_keys(owner_id)

    if not keys:
        await safe_edit(
            callback,
            f"✅ Ключ удален.\n\nУ пользователя {owner_id} больше нет ключей.",
            reply_markup=get_admin_keyboard()
        )
        return

    await safe_edit(
        callback,
        f"✅ Ключ удален.\n\nОставшиеся ключи пользователя {owner_id}:",
        reply_markup=get_admin_user_keys_keyboard(keys)
    )


@admin_router.callback_query(F.data == "admin_delete_key")
async def start_admin_delete_key(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await callback.answer()
    await state.clear()
    await state.set_state(AdminStates.waiting_delete_key_user_id)

    await safe_edit(
        callback,
        "🗑 Удаление ключа пользователя\n\n"
        "Отправь Telegram ID пользователя, чей ключ хочешь удалить.",
        reply_markup=get_admin_back_keyboard()
    )


@admin_router.message(AdminStates.waiting_delete_key_user_id)
async def admin_receive_delete_key_user_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    try:
        target_user_id = int(message.text.strip())
    except ValueError:
        await message.answer("ID должен быть числом. Попробуй еще раз.")
        return

    user_info = get_user_brief(target_user_id)
    if user_info is None:
        await message.answer("Пользователь с таким Telegram ID не найден. Попробуй еще раз.")
        return

    keys = get_user_keys(target_user_id)
    if not keys:
        await message.answer(f"У пользователя {target_user_id} нет ключей.")
        await state.clear()
        return

    await state.update_data(admin_target_user_id=target_user_id)
    await state.set_state(AdminStates.waiting_delete_key_id)

    lines = [f"🗑 Ключи пользователя {target_user_id}:\n"]
    for index, (key_id, key_value, created_at, status) in enumerate(keys, start=1):
        lines.append(f"{index}) id={key_id} | {key_value} | {status} | {format_date_ru(created_at)}")

    lines.append("\nТеперь отправь id ключа, который нужно удалить.")

    await message.answer("\n".join(lines))


@admin_router.message(AdminStates.waiting_delete_key_id)
async def admin_receive_delete_key_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    try:
        key_id = int(message.text.strip())
    except ValueError:
        await message.answer("ID ключа должен быть числом. Попробуй еще раз.")
        return

    data = await state.get_data()
    target_user_id = data.get("admin_target_user_id")

    if not target_user_id:
        await message.answer("Сессия админки сброшена. Запусти /admin заново.")
        await state.clear()
        return

    key_info = get_key_by_id(key_id, target_user_id)
    if key_info is None:
        await message.answer("Ключ с таким id у этого пользователя не найден. Попробуй еще раз.")
        return

    deleted = admin_delete_key_by_id(key_id)
    if not deleted:
        await message.answer("Не удалось удалить ключ. Попробуй еще раз.")
        return

    add_admin_log(
        message.from_user.id,
        "delete_key_manual_text",
        f"user={target_user_id}, key_id={key_id}"
    )

    await message.answer(f"✅ Ключ id={key_id} удален у пользователя {target_user_id}.")

    try:
        await message.bot.send_message(
            chat_id=target_user_id,
            text="🗑 Один из ваших ключей был удален администратором."
        )
    except Exception:
        pass

    await state.clear()


@admin_router.callback_query(F.data == "admin_broadcast")
async def start_admin_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await callback.answer()
    await state.clear()
    await state.set_state(AdminStates.waiting_broadcast_text)

    await safe_edit(
        callback,
        "📢 Рассылка\n\n"
        "Отправь текст, который нужно разослать всем пользователям.",
        reply_markup=get_admin_back_keyboard()
    )


@admin_router.message(AdminStates.waiting_broadcast_text)
async def admin_receive_broadcast_text(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip()

    await state.update_data(admin_broadcast_text=text)

    await message.answer(
        "📢 Текст рассылки сохранен.\n\n"
        "Теперь выбери режим рассылки:",
        reply_markup=get_broadcast_mode_keyboard()
    )


@admin_router.callback_query(F.data == "admin_broadcast_send_plain")
async def admin_broadcast_send_plain(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await callback.answer()

    data = await state.get_data()
    text = data.get("admin_broadcast_text")

    if not text:
        await safe_edit(callback, "Текст рассылки не найден. Начни заново.", reply_markup=get_admin_keyboard())
        await state.clear()
        return

    await state.update_data(admin_broadcast_mode="plain")

    await safe_edit(
        callback,
        f"📢 Предпросмотр рассылки\n\n{text}",
        reply_markup=get_broadcast_preview_plain_keyboard()
    )


@admin_router.callback_query(F.data == "admin_broadcast_send_buttons")
async def admin_broadcast_send_buttons(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await callback.answer()

    data = await state.get_data()
    text = data.get("admin_broadcast_text")

    if not text:
        await safe_edit(callback, "Текст рассылки не найден. Начни заново.", reply_markup=get_admin_keyboard())
        await state.clear()
        return

    await state.update_data(admin_broadcast_mode="buttons")

    await safe_edit(
        callback,
        f"📢 Предпросмотр рассылки\n\n{text}",
        reply_markup=get_broadcast_preview_buttons_keyboard(CHANNEL_URL)
    )


@admin_router.callback_query(F.data == "admin_broadcast_confirm_send")
async def admin_broadcast_confirm_send(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    await callback.answer()

    data = await state.get_data()
    text = data.get("admin_broadcast_text")
    mode = data.get("admin_broadcast_mode")

    if not text or not mode:
        await safe_edit(callback, "Данные рассылки потеряны. Начни заново.", reply_markup=get_admin_keyboard())
        await state.clear()
        return

    user_ids = get_all_user_ids()
    sent_count = 0
    failed_count = 0

    for user_id in user_ids:
        try:
            if mode == "plain":
                await callback.bot.send_message(chat_id=user_id, text=text)
            else:
                await callback.bot.send_message(
                    chat_id=user_id,
                    text=text,
                    reply_markup=get_broadcast_user_keyboard(CHANNEL_URL)
                )
            sent_count += 1
        except Exception:
            failed_count += 1

    action = "broadcast_plain" if mode == "plain" else "broadcast_with_buttons"
    add_admin_log(
        callback.from_user.id,
        action,
        f"sent={sent_count}, failed={failed_count}"
    )

    await safe_edit(
        callback,
        f"📢 Рассылка завершена.\n\n"
        f"✅ Отправлено: {sent_count}\n"
        f"❌ Не удалось: {failed_count}",
        reply_markup=get_admin_keyboard()
    )

    await state.clear()