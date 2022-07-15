import time
import logging

from telegram import Update
from telegram.ext import CallbackContext

from config import IS_WINTER
from metrics import fails_counter

logger = logging.getLogger("bot")


def log(func):
    """Logging decorator."""

    def logs(update: Update, context: CallbackContext):
        start = time.time()
        result = func(update, context)
        end = time.time()

        logger.info(f"{func.__name__} [{update.effective_user.username}]: {update.message.text} ({end - start})")

        return result

    return logs


def catcher(func):
    """Catching errors."""

    def catch(update: Update, context: CallbackContext):
        try:
            func(update, context)
        except Exception as ex:
            fails_counter.inc()
            logger.error(ex)
            message = r"Извините, у нас возникли технические сложности\. Вскоре мы все исправим\."
            update.message.reply_markdown_v2(message)

    return catch


def auth_check(func):

    def wrap(update: Update, context: CallbackContext):
        if is_logged_in(update, context):
            func(update, context)
        else:
            no_login(update, context)

    return wrap


def is_logged_in(_: Update, context: CallbackContext) -> bool:
    return context.user_data.get('token') is not False


def no_login(update: Update, _: CallbackContext) -> None:
    message = "Пожалуйста, авторизуйтесь: /login"
    update.message.reply_markdown_v2(text=message)


def winter_mode(func):
    def wrap(update: Update, context: CallbackContext):
        if IS_WINTER is True:
            no_act(update, context)
        else:
            func(update, context)

    def no_act(update: Update, _: CallbackContext) -> None:
        message = "В зимнее время недоступно."
        update.message.reply_text(message)

    return wrap
