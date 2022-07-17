import logging
import time

from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

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
            result = func(update, context)
        except Exception as ex:
            result = ConversationHandler.END
            fails_counter.inc()
            logger.error(ex)
            message = r"Извините, у нас возникли технические сложности\. Вскоре мы все исправим\."
            update.message.reply_markdown_v2(message)

        return result

    return catch


def auth_check(func):

    def wrap(update: Update, context: CallbackContext):
        if is_logged_in(update, context):
            result = func(update, context)
        else:
            result = no_login(update, context)

        return result

    return wrap


def is_logged_in(_: Update, context: CallbackContext) -> bool:
    return context.user_data.get('token') is not (False and None)


def no_login(update: Update, _: CallbackContext):
    message = "Пожалуйста, авторизуйтесь: /login"
    update.message.reply_markdown_v2(text=message)
    return ConversationHandler.END


def winter_mode(func):
    def wrap(update: Update, context: CallbackContext):
        if IS_WINTER is True:
            return no_act(update, context)

        return func(update, context)

    def no_act(update: Update, _: CallbackContext):
        message = "В зимнее время недоступно."
        update.message.reply_text(message)

    return wrap
