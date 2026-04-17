from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN
from db import init_db
from user_handlers import start, help_command, handle_user_button
from admin_handlers import admin_command, handle_admin_text, handle_admin_button


async def combined_callback_handler(update, context):
    handled = await handle_admin_button(update, context)
    if handled:
        return

    handled = await handle_user_button(update, context)
    if handled:
        return


def main():
    init_db()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(combined_callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_text))

    print("Inline-бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()