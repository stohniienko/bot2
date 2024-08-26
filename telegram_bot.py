from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import os
import re

# Настройки
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Инициализация Flask
app = Flask(__name__)

# Инициализация Telegram Application
application = Application.builder().token(TELEGRAM_TOKEN).build()

# Обработчики команд и сообщений
async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Привет! Пожалуйста, введите ваше имя и фамилию:")
    return ASK_NAME

async def ask_name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text

    if len(context.user_data['name'].split()) < 2:
        await update.message.reply_text("Пожалуйста, введите ваше имя и фамилию, разделенные пробелом.")
        return ASK_NAME

    await update.message.reply_text("Спасибо! Теперь введите ваш номер телефона в международном формате (например, +380123456789):")
    return ASK_PHONE

async def ask_phone(update: Update, context: CallbackContext) -> int:
    phone = update.message.text

    if not re.match(r"^\+\d{10,15}$", phone):
        await update.message.reply_text("Пожалуйста, введите корректный номер телефона в международном формате.")
        return ASK_PHONE

    context.user_data['phone'] = phone
    await update.message.reply_text("Отлично! Теперь введите ваш ник в Instagram (например, @username):")
    return ASK_INSTAGRAM

async def ask_instagram(update: Update, context: CallbackContext) -> int:
    instagram_nick = update.message.text

    if not re.match(r"^@\w{5,}$", instagram_nick):
        await update.message.reply_text("Пожалуйста, введите корректный ник в Instagram (начинается с @ и содержит минимум 5 символов).")
        return ASK_INSTAGRAM

    context.user_data['instagram'] = instagram_nick
    await update.message.reply_text("Теперь введите ваш ник на Facebook (например, facebook.com/username):")
    return ASK_FACEBOOK

async def ask_facebook(update: Update, context: CallbackContext) -> int:
    facebook_nick = update.message.text

    if not re.match(r"^facebook\.com/\w+$", facebook_nick):
        await update.message.reply_text("Пожалуйста, введите корректный ник на Facebook (например, facebook.com/username).")
        return ASK_FACEBOOK

    context.user_data['facebook'] = facebook_nick
    await update.message.reply_text("Спасибо! Ваши данные успешно сохранены.")
    return ConversationHandler.END

# Функция обработки вебхука
@app.route('/webhook', methods=['POST'])
async def webhook():
    json_update = request.get_json()
    update = Update.de_json(json_update, application.bot)
    await application.process_update(update)
    return '', 200

# Установка вебхука
async def set_webhook():
    await application.bot.set_webhook(url=WEBHOOK_URL)

if __name__ == '__main__':
    import asyncio

    async def main():
        await set_webhook()
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 9686)))

    asyncio.run(main())
