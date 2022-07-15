import requests

from telegram import Update
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters, CallbackContext
from commands import cancel_command

from config import API_ADDRESS
from labels import Labels
from metrics import commands_counter

LOGIN_STEP, PASSWORD_STEP = range(2)


def authorization(update: Update, _: CallbackContext) -> None:
    commands_counter.labels(Labels.LOGIN.value).inc()
    message = "Введите логин (например, demo)"
    update.message.reply_text(text=message)
    return LOGIN_STEP


def enter_login(update: Update, context: CallbackContext) -> None:
    context.user_data['username'] = update.message.text
    context.user_data['token'] = False
    context.user_data['is_admin'] = False
    update.message.reply_text(r'Введите пароль')
    return PASSWORD_STEP


def enter_password(update: Update, context: CallbackContext) -> None:
    # hidden_password = "".join(["*" for _ in update.message.text])
    # context.user_data['password'] = update.message.text
    context.bot.deleteMessage(update.message.chat_id,
                              update.message.message_id)

    authorization_check(update, context)

    return ConversationHandler.END


auth_conv = ConversationHandler(
    entry_points=[
        CommandHandler(
            'login',
            authorization)],
    states={
        LOGIN_STEP: [
            MessageHandler(
                Filters.text & (
                    ~ Filters.text("/cancel")),
                enter_login)],
        PASSWORD_STEP: [
            MessageHandler(
                Filters.text & (
                    ~ Filters.text("/cancel")),
                enter_password)]},
    fallbacks=[
        CommandHandler(
            'cancel',
            cancel_command)],
    allow_reentry=True,
    name="auth_conv",
    persistent=False)


def authorization_check(update: Update, context: CallbackContext) -> None:
    url = f'{API_ADDRESS}/telegram/login'

    credentials = {
        "username": context.user_data.get('username', 'Not found'),
        "password": update.message.text
    }

    r = requests.post(url, json=credentials)
    if r.status_code == 200:
        data = r.json()
        update.message.reply_text("Авторизация прошла успешно")
        update.message.reply_text("Список доступных команд: /help")
        context.user_data['token'] = data['token']
        context.user_data['is_admin'] = data['is_admin']
    else:
        update.message.reply_text("Неверные логин или пароль")
        update.message.reply_text("Повторная попытка: /login")
