from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackContext

TOKEN: Final = "6560466673:AAH5JnpF9JJos5bT5BDBCC_4UslF43EDjHY"
BOT_USERNAME: Final = '@uyt_test_bot'

# Admin IDS
ADMIN_IDS: list[int] = [938510955]

# Storage of chats and available admins
active_chats: dict[int:int or None] = {}
active_admin_chats: dict[int:int] = {}
available_admins: list[int] = []


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет, я тест бот')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Задайте свой вопрос:')


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('О нас')


async def lib_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Наша библиотека - midashall.notion.site')


def get_available_chats() -> list[int]:
    return [key for key, value in active_chats.items() if value is None]


async def connect_admin_to_chat(admin_id: int, update: Update):
    available_chats = get_available_chats()
    if len(available_chats) > 0:
        first_chat = available_chats[0]

        active_chats[first_chat] = admin_id
        active_admin_chats[admin_id] = first_chat

        await update.message.reply_text(
            f"Вы подключены к чату с пользователем {first_chat}. Напишите '/end' что бы завершить.")
    else:
        available_admins.append(admin_id)
        await update.message.reply_text("Ожидайте вопросов от пользователей. Напишите '/leave' если хотите выйти.")


async def chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in ADMIN_IDS:
        await connect_admin_to_chat(user_id, update)
    else:
        if len(available_admins) > 0:
            first_admin = available_admins[0]
            active_chats[user_id] = first_admin
            active_admin_chats[first_admin] = user_id
            available_admins.remove(first_admin)
            await context.bot.send_message(
                chat_id=first_admin,
                text=f"Вы подключены к чату с пользователем {user_id}. Напишите '/end' что бы завершить."
            )
            await update.message.reply_text("Вы начали чат с администратором. Пожалуйста, задайте ваш вопрос и ожидайте ответ.")
        else:
            active_chats[user_id] = None
            await update.message.reply_text("На данный момент нет администраторов онлайн. Попробуйте снова позже.")

    print(active_chats, active_admin_chats, available_admins)


async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(active_chats)
    user_id = update.message.from_user.id
    if user_id in active_chats:
        admin_chat_id = active_chats[user_id]
        if admin_chat_id is None:
            await update.message.reply_text("На данный момент нет администраторов онлайн. Попробуйте снова позже.")
        else:
            await context.bot.send_message(
                chat_id=admin_chat_id,
                text=f"Сообщение от пользователя {update.message.from_user.username}:\n{update.message.text}"
            )
    else:
        await update.message.reply_text("Пожалуйста, начните чат с администратором командой /chat.")


async def handle_admin_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(active_chats, active_admin_chats, available_admins)
    text_message = update.message.text
    admin_id = update.message.from_user.id
    user_id = active_admin_chats.get(admin_id, None)
    if text_message == '/end':
        if admin_id not in active_admin_chats and user_id not in active_chats:
            await update.message.reply_text('Вы не подключены к чату.')
        else:
            active_chats.pop(user_id)
            active_admin_chats.pop(admin_id)
            await update.message.reply_text(f'Чат с {user_id} завершен.')
            await context.bot.send_message(
                chat_id=user_id,
                text="Чат с администратором завершен."
            )

            await connect_admin_to_chat(admin_id, update)
            print(active_chats, active_admin_chats, available_admins)
    elif text_message == '/leave':
        available_admins.remove(admin_id)
        await update.message.reply_text('Вы вышли из режима чатов.')
    else:
        print(user_id)
        if user_id is None:
            await update.message.reply_text('Вы не подключены к чату.')
        else:
            await context.bot.send_message(chat_id=user_id, text=update.message.text)


def handle_response(text: str):
    processed = text.lower()
    if 'hello' in processed:
        return 'Hey there'
    if 'how are you' in processed:
        return 'Great!'
    return "I don't understand"


# async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     message_type: str = update.message.chat.type
#     text: str = update.message.text
#
#     print(f'User ({update.message.chat.id}) in {message_type}: {text}')
#
#     if message_type == 'group':
#         if BOT_USERNAME in text:
#             new_text: str = text.replace(BOT_USERNAME, '').strip()
#             response: str = handle_response(new_text)
#         else:
#             return
#     else:
#         response: str = handle_response(text)
#
#     print('Bot:', response)
#     await update.message.reply_text(response)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error: {context.error}')


if __name__ == '__main__':
    print('starting bot')
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('info', info_command))
    app.add_handler(CommandHandler('lib', lib_command))

    app.add_handler(CommandHandler("chat", chat_command))
    app.add_handler(MessageHandler(filters.User(ADMIN_IDS), handle_admin_messages))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    # Messages
    # app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    print('Polling...')
    app.run_polling(poll_interval=3)
