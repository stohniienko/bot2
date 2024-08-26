import re
import random
import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext

# Переменные окружения
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
PORT = int(os.getenv('PORT', 5000))

app = Flask(__name__)

# Состояния разговора
ASK_NAME, ASK_PHONE, ASK_INSTAGRAM, ASK_FACEBOOK, ASK_CAPTCHA = range(5)

# Инициализация бота
application = Application.builder().token(TOKEN).build()

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

    # Отправка капчи
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    context.user_data['captcha'] = a + b
    await update.message.reply_text(f'Решите капчу: {a} + {b} = ?')
    return ASK_CAPTCHA

async def check_captcha(update: Update, context: CallbackContext) -> int:
    try:
        user_captcha = int(update.message.text)
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число для капчи.")
        return ASK_CAPTCHA

    if user_captcha == context.user_data['captcha']:
        # Отправка данных в указанный чат
        message = (f"Имя: {context.user_data['name']}\n"
                   f"Телефон: {context.user_data['phone']}\n"
                   f"Instagram: {context.user_data['instagram']}\n"
                   f"Facebook: {context.user_data['facebook']}")
        await application.bot.send_message(chat_id=CHAT_ID, text=message)
        await update.message.reply_text('Спасибо! Ваши данные отправлены.')
        return ConversationHandler.END
    else:
        await update.message.reply_text('Неверный ответ на капчу. Попробуйте снова.')
        return ASK_CAPTCHA

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text('Отмена.')
    return ConversationHandler.END

# Настройка маршрутизации
@app.route('/' + TOKEN, methods=['POST'])
async def webhook():
    json_update = request.get_json()
    update = Update.de_json(json_update, application.bot)
    await application.process_update(update)
    return 'ok'

# Установка вебхука
def set_webhook():
    webhook_url = f'https://{os.getenv("HEROKU_APP_NAME")}.herokuapp.com/{TOKEN}'
    application.bot.set_webhook(url=webhook_url)

if __name__ == '__main__':
    set_webhook()
    app.run(host='0.0.0.0', port=PORT)
