from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_ID, CHANNEL_URL
from db import (
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
from keyboards import (
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


def is_admin(telegram_id):
    return telegram_id == ADMIN_ID


async def safe_edit(query, text, reply_markup=None, parse_mode=None):
    await query.message.edit_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode=parse_mode
    )


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    if not is_admin(telegram_id):
        return

    users_count = get_users_count()
    keys_count = get_total_keys_count()

    for key in [
        "admin_state",
        "admin_target_user_id",
        "admin_selected_key_owner_id",
        "admin_broadcast_text",
        "admin_broadcast_mode",
    ]:
        context.user_data.pop(key, None)

    await update.message.reply_text(
        f"🛠 Админка\n\n"
        f"👥 Пользователей: {users_count}\n"
        f"🔑 Ключей: {keys_count}",
        reply_markup=get_admin_keyboard()
    )


async def show_admin_main(update: Update):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return

    users_count = get_users_count()
    keys_count = get_total_keys_count()

    await safe_edit(
        query,
        f"🛠 Админка\n\n"
        f"👥 Пользователей: {users_count}\n"
        f"🔑 Ключей: {keys_count}",
        reply_markup=get_admin_keyboard()
    )


async def show_admin_users(update: Update):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return

    users = get_users_list()
    if not users:
        await safe_edit(
            query,
            "👥 Пользователей пока нет",
            reply_markup=get_admin_keyboard()
        )
        return

    lines = ["👥 Последние пользователи:\n"]
    for tg_id, first_name, balance in users:
        lines.append(f"{first_name} | {tg_id} | {int(balance)}₽")

    await safe_edit(
        query,
        "\n".join(lines),
        reply_markup=get_admin_keyboard()
    )


async def show_admin_logs(update: Update):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return

    logs = get_admin_logs(25)
    if not logs:
        await safe_edit(
            query,
            "📜 Логов пока нет",
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
        query,
        text,
        reply_markup=get_admin_keyboard()
    )


async def start_admin_add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return

    context.user_data["admin_state"] = "waiting_balance_user_id"
    context.user_data.pop("admin_target_user_id", None)

    await safe_edit(
        query,
        "💰 Начисление баланса\n\n"
        "Отправь Telegram ID пользователя, которому хочешь начислить баланс",
        reply_markup=get_admin_back_keyboard()
    )


async def start_admin_user_keys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return

    context.user_data["admin_state"] = "waiting_keys_user_id"
    context.user_data.pop("admin_target_user_id", None)
    context.user_data.pop("admin_selected_key_owner_id", None)

    await safe_edit(
        query,
        "🔑 Ключи пользователя\n\n"
        "Отправь Telegram ID пользователя, чьи ключи хочешь посмотреть",
        reply_markup=get_admin_back_keyboard()
    )


async def show_admin_user_keys_screen(update: Update, target_user_id: int):
    query = update.callback_query
    user_info = get_user_brief(target_user_id)

    if user_info is None:
        await safe_edit(
            query,
            "Пользователь не найден",
            reply_markup=get_admin_back_keyboard()
        )
        return

    _, first_name, balance = user_info
    keys = get_user_keys(target_user_id)

    if not keys:
        await safe_edit(
            query,
            f"🔑 Ключи пользователя\n\n"
            f"{first_name} | {target_user_id} | {int(balance)}₽\n\n"
            f"У пользователя нет ключей",
            reply_markup=get_admin_back_keyboard()
        )
        return

    await safe_edit(
        query,
        f"🔑 Ключи пользователя\n\n"
        f"{first_name} | {target_user_id} | {int(balance)}₽\n\n"
        f"Выбери нужный ключ:",
        reply_markup=get_admin_user_keys_keyboard(keys)
    )


async def show_admin_single_key(update: Update, key_id: int, owner_user_id: int):
    query = update.callback_query
    key_info = get_key_by_id(key_id, owner_user_id)

    if key_info is None:
        await safe_edit(
            query,
            "Ключ не найден",
            reply_markup=get_admin_back_keyboard()
        )
        return

    key_value, created_at, status = key_info
    status_text = "активен" if status == "active" else "остановлен"
    created_at_ru = format_date_ru(created_at)

    await safe_edit(
        query,
        f"🔑 Информация о ключе\n\n"
        f"ID ключа: {key_id}\n"
        f"Ключ: {key_value}\n"
        f"Статус: {status_text}\n"
        f"Создан: {created_at_ru}",
        reply_markup=get_admin_single_key_keyboard(key_id)
    )


async def start_admin_delete_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return

    context.user_data["admin_state"] = "waiting_delete_key_user_id"
    context.user_data.pop("admin_target_user_id", None)

    await safe_edit(
        query,
        "🗑 Удаление ключа пользователя\n\n"
        "Отправь Telegram ID пользователя, чей ключ хочешь удалить",
        reply_markup=get_admin_back_keyboard()
    )


async def start_admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return

    context.user_data["admin_state"] = "waiting_broadcast_text"
    context.user_data.pop("admin_broadcast_text", None)
    context.user_data.pop("admin_broadcast_mode", None)

    await safe_edit(
        query,
        "📢 Рассылка\n\n"
        "Отправь текст, который нужно разослать всем пользователям",
        reply_markup=get_admin_back_keyboard()
    )


async def handle_admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    if not is_admin(telegram_id):
        return

    state = context.user_data.get("admin_state")
    if not state:
        return

    text = (update.message.text or "").strip()

    if state == "waiting_balance_user_id":
        try:
            target_user_id = int(text)
        except ValueError:
            await update.message.reply_text("ID должен быть числом. Попробуй еще раз")
            return

        user_info = get_user_brief(target_user_id)
        if user_info is None:
            await update.message.reply_text("Пользователь с таким Telegram ID не найден. Попробуй еще раз")
            return

        _, first_name, balance = user_info
        context.user_data["admin_state"] = "waiting_balance_amount_button"
        context.user_data["admin_target_user_id"] = target_user_id

        await update.message.reply_text(
            f"💰 Начисление баланса\n\n"
            f"Пользователь найден:\n"
            f"{first_name} | {target_user_id} | {int(balance)}₽\n\n"
            f"Теперь выбери сумму:",
            reply_markup=get_admin_balance_amounts_keyboard()
        )
        return

    if state == "waiting_balance_custom_amount":
        try:
            amount = float(text.replace(",", "."))
        except ValueError:
            await update.message.reply_text("Сумма должна быть числом. Попробуй еще раз")
            return

        if amount <= 0:
            await update.message.reply_text("Сумма должна быть больше 0. Попробуй еще раз")
            return

        target_user_id = context.user_data.get("admin_target_user_id")
        if not target_user_id:
            context.user_data.pop("admin_state", None)
            await update.message.reply_text("Сессия сброшена. Нажми заново «Начислить баланс»")
            return

        add_balance(target_user_id, amount)
        activate_user_keys(target_user_id)
        new_balance = get_user_balance(target_user_id)

        add_admin_log(
            telegram_id,
            "add_balance_custom",
            f"user={target_user_id}, amount={amount}"
        )

        await update.message.reply_text(
            f"✅ Баланс начислен\n\n"
            f"Пользователь: {target_user_id}\n"
            f"Сумма: {int(amount)}₽\n"
            f"Новый баланс: {int(new_balance)}₽"
        )

        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"💰 Вам начислен баланс: {int(amount)}₽\nТекущий баланс: {int(new_balance)}₽"
            )
        except Exception:
            pass

        context.user_data.pop("admin_state", None)
        context.user_data.pop("admin_target_user_id", None)
        return

    if state == "waiting_keys_user_id":
        try:
            target_user_id = int(text)
        except ValueError:
            await update.message.reply_text("ID должен быть числом. Попробуй еще раз")
            return

        user_info = get_user_brief(target_user_id)
        if user_info is None:
            await update.message.reply_text("Пользователь с таким Telegram ID не найден. Попробуй еще раз")
            return

        keys = get_user_keys(target_user_id)
        context.user_data["admin_state"] = None
        context.user_data["admin_target_user_id"] = target_user_id
        context.user_data["admin_selected_key_owner_id"] = target_user_id

        if not keys:
            await update.message.reply_text(
                f"У пользователя {target_user_id} нет ключей",
                reply_markup=get_admin_back_keyboard()
            )
            return

        _, first_name, balance = user_info
        await update.message.reply_text(
            f"🔑 Ключи пользователя\n\n"
            f"{first_name} | {target_user_id} | {int(balance)}₽\n\n"
            f"Выбери нужный ключ:",
            reply_markup=get_admin_user_keys_keyboard(keys)
        )
        return

    if state == "waiting_delete_key_user_id":
        try:
            target_user_id = int(text)
        except ValueError:
            await update.message.reply_text("ID должен быть числом. Попробуй еще раз")
            return

        user_info = get_user_brief(target_user_id)
        if user_info is None:
            await update.message.reply_text("Пользователь с таким Telegram ID не найден. Попробуй еще раз")
            return

        keys = get_user_keys(target_user_id)
        if not keys:
            await update.message.reply_text(
                f"У пользователя {target_user_id} нет ключей"
            )
            context.user_data.pop("admin_state", None)
            return

        context.user_data["admin_state"] = "waiting_delete_key_id"
        context.user_data["admin_target_user_id"] = target_user_id

        lines = [f"🗑 Ключи пользователя {target_user_id}:\n"]
        for index, (key_id, key_value, created_at, status) in enumerate(keys, start=1):
            lines.append(
                f"{index}) id={key_id} | {key_value} | {status} | {format_date_ru(created_at)}"
            )

        lines.append("\nТеперь отправь id ключа, который нужно удалить")

        await update.message.reply_text("\n".join(lines))
        return

    if state == "waiting_delete_key_id":
        try:
            key_id = int(text)
        except ValueError:
            await update.message.reply_text("ID ключа должен быть числом. Попробуй еще раз")
            return

        target_user_id = context.user_data.get("admin_target_user_id")
        if not target_user_id:
            context.user_data.pop("admin_state", None)
            await update.message.reply_text("Сессия админки сброшена. Запусти /admin заново")
            return

        key_info = get_key_by_id(key_id, target_user_id)
        if key_info is None:
            await update.message.reply_text("Ключ с таким id у этого пользователя не найден. Попробуй еще раз")
            return

        deleted = admin_delete_key_by_id(key_id)
        if not deleted:
            await update.message.reply_text("Не удалось удалить ключ. Попробуй еще раз")
            return

        add_admin_log(
            telegram_id,
            "delete_key_manual_text",
            f"user={target_user_id}, key_id={key_id}"
        )

        await update.message.reply_text(
            f"✅ Ключ id={key_id} удален у пользователя {target_user_id}"
        )

        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text="🗑 Один из ваших ключей был удален администратором"
            )
        except Exception:
            pass

        context.user_data.pop("admin_state", None)
        context.user_data.pop("admin_target_user_id", None)
        return

    if state == "waiting_broadcast_text":
        context.user_data["admin_broadcast_text"] = text
        context.user_data["admin_state"] = "waiting_broadcast_mode"

        await update.message.reply_text(
            "📢 Текст рассылки сохранен\n\n"
            "Теперь выбери режим рассылки:",
            reply_markup=get_broadcast_mode_keyboard()
        )
        return


async def handle_admin_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    telegram_id = query.from_user.id

    if not is_admin(telegram_id):
        return False

    if data == "admin_main":
        await show_admin_main(update)
        return True

    elif data == "admin_users":
        await show_admin_users(update)
        return True

    elif data == "admin_logs":
        await show_admin_logs(update)
        return True

    elif data == "admin_add_balance":
        await start_admin_add_balance(update, context)
        return True

    elif data.startswith("admin_balance_amount_"):
        suffix = data.split("_")[-1]
        target_user_id = context.user_data.get("admin_target_user_id")

        if suffix == "other":
            if not target_user_id:
                await safe_edit(
                    query,
                    "Сессия начисления баланса сброшена. Нажми заново «Начислить баланс»",
                    reply_markup=get_admin_keyboard()
                )
                return True

            context.user_data["admin_state"] = "waiting_balance_custom_amount"
            await safe_edit(
                query,
                f"💰 Начисление баланса\n\n"
                f"Пользователь: {target_user_id}\n\n"
                f"Введи сумму вручную:",
                reply_markup=get_admin_back_keyboard()
            )
            return True

        amount = int(suffix)

        if not target_user_id:
            await safe_edit(
                query,
                "Сессия начисления баланса сброшена. Нажми заново «Начислить баланс»",
                reply_markup=get_admin_keyboard()
            )
            return True

        add_balance(target_user_id, amount)
        activate_user_keys(target_user_id)
        new_balance = get_user_balance(target_user_id)

        add_admin_log(
            telegram_id,
            "add_balance_button",
            f"user={target_user_id}, amount={amount}"
        )

        await safe_edit(
            query,
            f"✅ Баланс начислен\n\n"
            f"Пользователь: {target_user_id}\n"
            f"Сумма: {amount}₽\n"
            f"Новый баланс: {int(new_balance)}₽",
            reply_markup=get_admin_keyboard()
        )

        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"💰 Вам начислен баланс: {amount}₽\nТекущий баланс: {int(new_balance)}₽"
            )
        except Exception:
            pass

        context.user_data.pop("admin_state", None)
        context.user_data.pop("admin_target_user_id", None)
        return True

    elif data == "admin_user_keys":
        await start_admin_user_keys(update, context)
        return True

    elif data == "admin_user_keys_back":
        owner_id = context.user_data.get("admin_selected_key_owner_id")
        if owner_id:
            await show_admin_user_keys_screen(update, owner_id)
        else:
            await show_admin_main(update)
        return True

    elif data.startswith("admin_key_select_"):
        key_id = int(data.split("_")[-1])
        owner_id = context.user_data.get("admin_selected_key_owner_id")

        if not owner_id:
            await safe_edit(
                query,
                "Не выбран владелец ключей. Зайди заново в раздел «Ключи пользователя»",
                reply_markup=get_admin_keyboard()
            )
            return True

        await show_admin_single_key(update, key_id, owner_id)
        return True

    elif data.startswith("admin_key_ask_delete_"):
        key_id = int(data.split("_")[-1])
        await safe_edit(
            query,
            "⚠️ Подтверждение удаления\n\nТы точно хочешь удалить этот ключ?",
            reply_markup=get_admin_delete_confirm_keyboard(key_id)
        )
        return True

    elif data.startswith("admin_key_confirm_delete_"):
        key_id = int(data.split("_")[-1])
        owner_id = context.user_data.get("admin_selected_key_owner_id")

        if not owner_id:
            await safe_edit(
                query,
                "Не выбран владелец ключей. Зайди заново в раздел «Ключи пользователя»",
                reply_markup=get_admin_keyboard()
            )
            return True

        key_info = get_key_by_id(key_id, owner_id)
        if key_info is None:
            await safe_edit(
                query,
                "Ключ уже не найден",
                reply_markup=get_admin_keyboard()
            )
            return True

        deleted = admin_delete_key_by_id(key_id)
        if not deleted:
            await safe_edit(
                query,
                "Не удалось удалить ключ",
                reply_markup=get_admin_keyboard()
            )
            return True

        add_admin_log(
            telegram_id,
            "delete_key_button",
            f"user={owner_id}, key_id={key_id}"
        )

        try:
            await context.bot.send_message(
                chat_id=owner_id,
                text="🗑 Один из ваших ключей был удален администратором"
            )
        except Exception:
            pass

        keys = get_user_keys(owner_id)
        if not keys:
            await safe_edit(
                query,
                f"✅ Ключ удален.\n\nУ пользователя {owner_id} больше нет ключей",
                reply_markup=get_admin_keyboard()
            )
            return True

        await safe_edit(
            query,
            f"✅ Ключ удален.\n\nОставшиеся ключи пользователя {owner_id}:",
            reply_markup=get_admin_user_keys_keyboard(keys)
        )
        return True

    elif data == "admin_delete_key":
        await start_admin_delete_key(update, context)
        return True

    elif data == "admin_broadcast":
        await start_admin_broadcast(update, context)
        return True

    elif data == "admin_broadcast_send_plain":
        text = context.user_data.get("admin_broadcast_text")
        if not text:
            await safe_edit(
                query,
                "Текст рассылки не найден. Начни заново",
                reply_markup=get_admin_keyboard()
            )
            return True

        context.user_data["admin_broadcast_mode"] = "plain"
        await safe_edit(
            query,
            f"📢 Предпросмотр рассылки\n\n{text}",
            reply_markup=get_broadcast_preview_plain_keyboard()
        )
        return True

    elif data == "admin_broadcast_send_buttons":
        text = context.user_data.get("admin_broadcast_text")
        if not text:
            await safe_edit(
                query,
                "Текст рассылки не найден. Начни заново",
                reply_markup=get_admin_keyboard()
            )
            return True

        context.user_data["admin_broadcast_mode"] = "buttons"
        await safe_edit(
            query,
            f"📢 Предпросмотр рассылки\n\n{text}",
            reply_markup=get_broadcast_preview_buttons_keyboard(CHANNEL_URL)
        )
        return True

    elif data == "admin_broadcast_confirm_send":
        text = context.user_data.get("admin_broadcast_text")
        mode = context.user_data.get("admin_broadcast_mode")

        if not text or not mode:
            await safe_edit(
                query,
                "Данные рассылки потеряны. Начни заново",
                reply_markup=get_admin_keyboard()
            )
            return True

        user_ids = get_all_user_ids()
        sent_count = 0
        failed_count = 0

        for user_id in user_ids:
            try:
                if mode == "plain":
                    await context.bot.send_message(chat_id=user_id, text=text)
                else:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=text,
                        reply_markup=get_broadcast_user_keyboard(CHANNEL_URL)
                    )
                sent_count += 1
            except Exception:
                failed_count += 1

        action = "broadcast_plain" if mode == "plain" else "broadcast_with_buttons"
        add_admin_log(
            telegram_id,
            action,
            f"sent={sent_count}, failed={failed_count}"
        )

        await safe_edit(
            query,
            f"📢 Рассылка завершена.\n\n"
            f"✅ Отправлено: {sent_count}\n"
            f"❌ Не удалось: {failed_count}",
            reply_markup=get_admin_keyboard()
        )

        context.user_data.pop("admin_state", None)
        context.user_data.pop("admin_broadcast_text", None)
        context.user_data.pop("admin_broadcast_mode", None)
        return True

    return False