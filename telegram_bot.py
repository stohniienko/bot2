import os
import re
import random
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
)

# Шаги для ConversationHandler
ASK_NAME, ASK_PHONE, ASK_INSTAGRAM, ASK_FACEBOOK, ASK_CAPTCHA = range(5)

# Получаем значения переменных окружения
TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = os.getenv("CHAT_ID")

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

    # Генерация капчи (случайная простая математическая задача)
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    context.user_data['captcha'] = num1 + num2
    await update.message.reply_text(f"Для подтверждения, решите задачу: {num1} + {num2} = ?")
    return ASK_CAPTCHA

async def ask_captcha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answer = int(update.message.text)
    correct_answer = context.user_data.get('captcha')

    if answer != correct_answer:
        await update.message.reply_text("Неправильный ответ. Попробуйте еще раз.")
        return ASK_CAPTCHA

    user_data = context.user_data

    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=(
            f"Новые данные от пользователя:\n"
            f"Имя и фамилия: {user_data['name']}\n"
            f"Телефон: {user_data['phone']}\n"
            f"Instagram: {user_data['instagram']}\n"
            f"Facebook: {user_data['facebook']}"
        )
    )

    await update.message.reply_text("Спасибо! Ваши данные были отправлены.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Отмена. Если захотите начать снова, введите /start.')
    return ConversationHandler.END

def main():
    # Создание приложения с использованием токена из переменных окружения
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_INSTAGRAM: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_instagram)],
            ASK_FACEBOOK: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_facebook)],
            ASK_CAPTCHA: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_captcha)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == '__main__':
    main()
