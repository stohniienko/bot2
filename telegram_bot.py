import logging
import os
import re
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import asyncio

# Конфигурация логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Константы для состояний
ASK_NAME, ASK_PHONE, ASK_INSTAGRAM, ASK_FACEBOOK = range(4)

app = Flask(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Привет! Пожалуйста, введите ваше имя и фамилию:")
    return ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text

    if len(context.user_data['name'].split()) < 2:
        await update.message.reply_text("Пожалуйста, введите ваше имя и фамилию, разделенные пробелом.")
        return ASK_NAME

    await update.message.reply_text("Спасибо! Теперь введите ваш номер телефона в международном формате (например, +380123456789):")
    return ASK_PHONE

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone = update.message.text

    if not re.match(r"^\+\d{10,15}$", phone):
        await update.message.reply_text("Пожалуйста, введите корректный номер телефона в международном формате.")
        return ASK_PHONE

    context.user_data['phone'] = phone
    await update.message.reply_text("Отлично! Теперь введите ваш ник в Instagram (например, @username):")
    return ASK_INSTAGRAM

async def ask_instagram(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    instagram_nick = update.message.text

    if not re.match(r"^@\w{5,}$", instagram_nick):
        await update.message.reply_text("Пожалуйста, введите корректный ник в Instagram (начинается с @ и содержит минимум 5 символов).")
        return ASK_INSTAGRAM

    context.user_data['instagram'] = instagram_nick
    await update.message.reply_text("Теперь введите ваш ник на Facebook (например, facebook.com/username):")
    return ASK_FACEBOOK

async def ask_facebook(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    facebook_nick = update.message.text

    if not re.match(r"^facebook\.com/\w+$", facebook_nick):
        await update.message.reply_text("Пожалуйста, введите корректный ник на Facebook (например, facebook.com/username).")
        return ASK_FACEBOOK

    context.user_data['facebook'] = facebook_nick

    # Отправка собранной информации в другой чат
    bot = context.bot
    message = (f"Получены данные:\n"
               f"Имя и фамилия: {context.user_data['name']}\n"
               f"Телефон: {context.user_data['phone']}\n"
               f"Instagram: {context.user_data['instagram']}\n"
               f"Facebook: {context.user_data['facebook']}")
    
    # Отправка сообщения в указанный чат
    await bot.send_message(chat_id=CHAT_ID, text=message)
    
    await update.message.reply_text("Спасибо! Ваши данные успешно отправлены.")
    return ConversationHandler.END

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(), bot)
    application.process_update(update)
    return 'ok'

async def set_webhook():
    bot = Bot(token=TELEGRAM_TOKEN)
    webhook_url = WEBHOOK_URL
    await bot.set_webhook(url=webhook_url)

def main() -> None:
    # Создание приложения и добавление обработчиков
    global application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Добавление обработчиков команд и сообщений
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_instagram))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ask_facebook))

    # Настройка вебхука
    asyncio.run(set_webhook())

    # Запуск Flask сервера
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

if __name__ == '__main__':
    main()
