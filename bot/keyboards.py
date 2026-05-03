from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_after_topup_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚡ Подключить VPN", callback_data="keys_menu")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
        ]
    )


def get_main_cabinet_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚡ Подключить VPN", callback_data="keys_menu")],
            [
                InlineKeyboardButton(text="👤 Пригласить", callback_data="invite"),
                InlineKeyboardButton(text="⭐ Баланс", callback_data="balance"),
            ],
            [
                InlineKeyboardButton(
                    text="👛 Пополнить баланс", callback_data="up_balance"
                )
            ],
            [InlineKeyboardButton(text="💬 Поддержка", callback_data="help")],
        ]
    )


def money_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="100₽", callback_data="topup_100")],
            [InlineKeyboardButton(text="300₽", callback_data="topup_300")],
            [InlineKeyboardButton(text="500₽", callback_data="topup_500")],
            [InlineKeyboardButton(text="700₽", callback_data="topup_700")],
            [InlineKeyboardButton(text="1000₽", callback_data="topup_1000")],
            [InlineKeyboardButton(text="2000₽", callback_data="topup_2000")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
        ]
    )


def get_support_menu(support_username):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✉️ Написать в поддержку",
                    url=f"https://t.me/{support_username}",
                )
            ],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
        ]
    )


def get_connect_key_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад к ключам", callback_data="keys_menu")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")],
        ]
    )


def get_low_balance_notification_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👛 Пополнить баланс", callback_data="up_balance"
                ),
                InlineKeyboardButton(
                    text="⚡ Открыть ключи", callback_data="keys_menu"
                ),
            ]
        ]
    )


def get_zero_balance_notification_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👛 Пополнить баланс", callback_data="up_balance"
                ),
                InlineKeyboardButton(text="💬 Поддержка", callback_data="help"),
            ]
        ]
    )


def get_user_delete_confirm_keyboard(key_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔥 Да, удалить", callback_data=f"confirm_delete_key_{key_id}"
                ),
                InlineKeyboardButton(text="❌ Отмена", callback_data=f"key_{key_id}"),
            ]
        ]
    )


def get_keys_menu(user_keys, selected_key_id=None):
    keyboard = [
        [InlineKeyboardButton(text="🆕 Создать новый ключ", callback_data="create_key")]
    ]

    keys_count = len(user_keys)

    for index, (key_id, key_value, created_at, status) in enumerate(user_keys, start=1):
        title = f"🔑 Ключ №{index}" if status == "active" else f"🔴 Ключ №{index}"

        keyboard.append(
            [InlineKeyboardButton(text=title, callback_data=f"key_{key_id}")]
        )

        if selected_key_id == key_id:
            if keys_count == 1:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            text="🔑 Получить", callback_data=f"connect_key_{key_id}"
                        ),
                        InlineKeyboardButton(
                            text="🌍 Изменить", callback_data=f"replace_key_{key_id}"
                        ),
                    ]
                )
            else:
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            text="🔑 Получить", callback_data=f"connect_key_{key_id}"
                        ),
                        InlineKeyboardButton(
                            text="🔥 Удалить", callback_data=f"ask_delete_key_{key_id}"
                        ),
                        InlineKeyboardButton(
                            text="🌍 Изменить", callback_data=f"replace_key_{key_id}"
                        ),
                    ]
                )

    keyboard.append(
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👥 Список пользователей", callback_data="admin_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💰 Начислить баланс", callback_data="admin_add_balance"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔑 Ключи пользователя", callback_data="admin_user_keys"
                )
            ],
            [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="📜 Логи админа", callback_data="admin_logs")],
            [
                InlineKeyboardButton(
                    text="🗑 Удалить ключ пользователя", callback_data="admin_delete_key"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Выйти из админки", callback_data="main_menu"
                )
            ],
        ]
    )


def get_admin_back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Назад в админку", callback_data="admin_main")]
        ]
    )


def get_admin_balance_amounts_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="100₽", callback_data="admin_balance_amount_100"
                ),
                InlineKeyboardButton(
                    text="200₽", callback_data="admin_balance_amount_200"
                ),
                InlineKeyboardButton(
                    text="300₽", callback_data="admin_balance_amount_300"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="400₽", callback_data="admin_balance_amount_400"
                ),
                InlineKeyboardButton(
                    text="500₽", callback_data="admin_balance_amount_500"
                ),
                InlineKeyboardButton(
                    text="Другое", callback_data="admin_balance_amount_other"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Назад в админку", callback_data="admin_main"
                )
            ],
        ]
    )


def get_admin_user_keys_keyboard(user_keys):
    keyboard = []

    for index, (key_id, key_value, created_at, status) in enumerate(user_keys, start=1):
        icon = "🟢" if status == "active" else "🔴"
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{icon} Ключ №{index}",
                    callback_data=f"admin_key_select_{key_id}",
                )
            ]
        )

    keyboard.append(
        [InlineKeyboardButton(text="↩️ Назад в админку", callback_data="admin_main")]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_single_key_keyboard(key_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗑 Удалить ключ",
                    callback_data=f"admin_key_ask_delete_{key_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад к ключам", callback_data="admin_user_keys_back"
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Назад в админку", callback_data="admin_main"
                )
            ],
        ]
    )


def get_admin_delete_confirm_keyboard(key_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔥 Да, удалить",
                    callback_data=f"admin_key_confirm_delete_{key_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Отмена", callback_data=f"admin_key_select_{key_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад к ключам", callback_data="admin_user_keys_back"
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Назад в админку", callback_data="admin_main"
                )
            ],
        ]
    )


def get_broadcast_mode_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Только текст", callback_data="admin_broadcast_send_plain"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Текст + кнопки", callback_data="admin_broadcast_send_buttons"
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Назад в админку", callback_data="admin_main"
                )
            ],
        ]
    )


def get_broadcast_user_keyboard(channel_url=None):
    keyboard = [
        [
            InlineKeyboardButton(
                text="👛 Пополнить баланс", callback_data="up_balance"
            ),
            InlineKeyboardButton(text="⚡ Открыть ключи", callback_data="keys_menu"),
        ],
        [InlineKeyboardButton(text="💬 Поддержка", callback_data="help")],
    ]

    if channel_url:
        keyboard.append([InlineKeyboardButton(text="📣 Канал", url=channel_url)])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_broadcast_preview_plain_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Отправить всем",
                    callback_data="admin_broadcast_confirm_send",
                ),
                InlineKeyboardButton(text="❌ Отмена", callback_data="admin_main"),
            ]
        ]
    )


def get_broadcast_preview_buttons_keyboard(channel_url=None):
    keyboard = [
        [
            InlineKeyboardButton(
                text="👛 Пополнить баланс", callback_data="up_balance"
            ),
            InlineKeyboardButton(text="⚡ Открыть ключи", callback_data="keys_menu"),
        ],
        [InlineKeyboardButton(text="💬 Поддержка", callback_data="help")],
    ]

    if channel_url:
        keyboard.append([InlineKeyboardButton(text="📣 Канал", url=channel_url)])

    keyboard.append(
        [
            InlineKeyboardButton(
                text="✅ Отправить всем", callback_data="admin_broadcast_confirm_send"
            ),
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_main"),
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
