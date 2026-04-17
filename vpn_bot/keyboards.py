from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_after_topup_keyboard():
    keyboard = [
        [InlineKeyboardButton("⚡ Подключить VPN", callback_data="keys_menu")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_main_cabinet_keyboard():
    keyboard = [
        [InlineKeyboardButton("⚡ Подключить VPN", callback_data="keys_menu")],
        [
            InlineKeyboardButton("👤 Пригласить", callback_data="invite"),
            InlineKeyboardButton("⭐ Баланс", callback_data="balance")
        ],
        [InlineKeyboardButton("👛 Пополнить баланс", callback_data="up_balance")],
        [InlineKeyboardButton("💬 Поддержка", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)


def money_inline_keyboard():
    keyboard = [
        [InlineKeyboardButton("100₽", callback_data="topup_100")],
        [InlineKeyboardButton("300₽", callback_data="topup_300")],
        [InlineKeyboardButton("500₽", callback_data="topup_500")],
        [InlineKeyboardButton("700₽", callback_data="topup_700")],
        [InlineKeyboardButton("1000₽", callback_data="topup_1000")],
        [InlineKeyboardButton("2000₽", callback_data="topup_2000")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_support_menu(support_username):
    keyboard = [
        [InlineKeyboardButton("✉️ Написать в поддержку", url=f"https://t.me/{support_username}")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_connect_key_menu():
    keyboard = [
        [InlineKeyboardButton("⬅️ Назад к ключам", callback_data="keys_menu")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_low_balance_notification_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("👛 Пополнить баланс", callback_data="up_balance"),
            InlineKeyboardButton("⚡ Открыть ключи", callback_data="keys_menu"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_zero_balance_notification_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("👛 Пополнить баланс", callback_data="up_balance"),
            InlineKeyboardButton("💬 Поддержка", callback_data="help"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_user_delete_confirm_keyboard(key_id):
    keyboard = [
        [
            InlineKeyboardButton("🔥 Да, удалить", callback_data=f"confirm_delete_key_{key_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"key_{key_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_keys_menu(user_keys, selected_key_id=None):
    keyboard = [
        [InlineKeyboardButton("🆕 Создать новый ключ", callback_data="create_key")]
    ]

    keys_count = len(user_keys)

    for index, (key_id, key_value, created_at, status) in enumerate(user_keys, start=1):
        title = f"🔑 Ключ №{index}" if status == "active" else f"🔴 Ключ №{index}"

        keyboard.append([
            InlineKeyboardButton(title, callback_data=f"key_{key_id}")
        ])

        if selected_key_id == key_id:
            if keys_count == 1:
                keyboard.append([
                    InlineKeyboardButton("🔑 Получить", callback_data=f"connect_key_{key_id}"),
                    InlineKeyboardButton("🌍 Изменить", callback_data=f"replace_key_{key_id}")
                ])
            else:
                keyboard.append([
                    InlineKeyboardButton("🔑 Получить", callback_data=f"connect_key_{key_id}"),
                    InlineKeyboardButton("🔥 Удалить", callback_data=f"ask_delete_key_{key_id}"),
                    InlineKeyboardButton("🌍 Изменить", callback_data=f"replace_key_{key_id}")
                ])

    keyboard.append([
        InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    ])

    return InlineKeyboardMarkup(keyboard)


def get_admin_keyboard():
    keyboard = [
        [InlineKeyboardButton("👥 Список пользователей", callback_data="admin_users")],
        [InlineKeyboardButton("💰 Начислить баланс", callback_data="admin_add_balance")],
        [InlineKeyboardButton("🔑 Ключи пользователя", callback_data="admin_user_keys")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📜 Логи админа", callback_data="admin_logs")],
        [InlineKeyboardButton("🗑 Удалить ключ пользователя", callback_data="admin_delete_key")],
        [InlineKeyboardButton("🏠 Выйти из админки", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_back_keyboard():
    keyboard = [
        [InlineKeyboardButton("↩️ Назад в админку", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_balance_amounts_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("100₽", callback_data="admin_balance_amount_100"),
            InlineKeyboardButton("200₽", callback_data="admin_balance_amount_200"),
            InlineKeyboardButton("300₽", callback_data="admin_balance_amount_300"),
        ],
        [
            InlineKeyboardButton("400₽", callback_data="admin_balance_amount_400"),
            InlineKeyboardButton("500₽", callback_data="admin_balance_amount_500"),
            InlineKeyboardButton("Другое", callback_data="admin_balance_amount_other"),
        ],
        [InlineKeyboardButton("↩️ Назад в админку", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_user_keys_keyboard(user_keys):
    keyboard = []

    for index, (key_id, key_value, created_at, status) in enumerate(user_keys, start=1):
        status_icon = "🟢" if status == "active" else "🔴"
        keyboard.append([
            InlineKeyboardButton(
                f"{status_icon} Ключ №{index}",
                callback_data=f"admin_key_select_{key_id}"
            )
        ])

    keyboard.append([InlineKeyboardButton("↩️ Назад в админку", callback_data="admin_main")])
    return InlineKeyboardMarkup(keyboard)


def get_admin_single_key_keyboard(key_id):
    keyboard = [
        [InlineKeyboardButton("🗑 Удалить ключ", callback_data=f"admin_key_ask_delete_{key_id}")],
        [InlineKeyboardButton("⬅️ Назад к ключам", callback_data="admin_user_keys_back")],
        [InlineKeyboardButton("↩️ Назад в админку", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_admin_delete_confirm_keyboard(key_id):
    keyboard = [
        [
            InlineKeyboardButton("🔥 Да, удалить", callback_data=f"admin_key_confirm_delete_{key_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"admin_key_select_{key_id}")
        ],
        [InlineKeyboardButton("⬅️ Назад к ключам", callback_data="admin_user_keys_back")],
        [InlineKeyboardButton("↩️ Назад в админку", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_broadcast_mode_keyboard():
    keyboard = [
        [InlineKeyboardButton("Только текст", callback_data="admin_broadcast_send_plain")],
        [InlineKeyboardButton("Текст + кнопки", callback_data="admin_broadcast_send_buttons")],
        [InlineKeyboardButton("↩️ Назад в админку", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_broadcast_user_keyboard(channel_url=None):
    keyboard = [
        [
            InlineKeyboardButton("👛 Пополнить баланс", callback_data="up_balance"),
            InlineKeyboardButton("⚡ Открыть ключи", callback_data="keys_menu"),
        ],
        [InlineKeyboardButton("💬 Поддержка", callback_data="help")]
    ]

    if channel_url:
        keyboard.append([InlineKeyboardButton("📣 Канал", url=channel_url)])

    return InlineKeyboardMarkup(keyboard)


def get_broadcast_preview_plain_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("✅ Отправить всем", callback_data="admin_broadcast_confirm_send"),
            InlineKeyboardButton("❌ Отмена", callback_data="admin_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_broadcast_preview_buttons_keyboard(channel_url=None):
    keyboard = [
        [
            InlineKeyboardButton("👛 Пополнить баланс", callback_data="up_balance"),
            InlineKeyboardButton("⚡ Открыть ключи", callback_data="keys_menu"),
        ],
        [InlineKeyboardButton("💬 Поддержка", callback_data="help")]
    ]

    if channel_url:
        keyboard.append([InlineKeyboardButton("📣 Канал", url=channel_url)])

    keyboard.append([
        InlineKeyboardButton("✅ Отправить всем", callback_data="admin_broadcast_confirm_send"),
        InlineKeyboardButton("❌ Отмена", callback_data="admin_main")
    ])

    return InlineKeyboardMarkup(keyboard)