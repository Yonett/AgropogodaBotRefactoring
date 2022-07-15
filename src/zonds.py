from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from telegram.utils.helpers import escape_markdown

from labels import Labels
from methods import device_report_callback
from commands import cancel_command
from keyboards import get_zonds_keyboard
from decorators import auth_check, catcher, log
from metrics import commands_counter

ZOND_STEP = range(1)


@catcher
@log
@auth_check
def zonds_command(update: Update, context: CallbackContext) -> None:
    commands_counter.labels(Labels.ZONDS.value).inc()
    reply_markup = ReplyKeyboardMarkup(get_zonds_keyboard(context))
    update.message.reply_markdown_v2(
        text="Выберите зонд: ", reply_markup=reply_markup)

    return ZOND_STEP


def enter_zond(update: Update, context: CallbackContext) -> None:
    device = context.chat_data.get('zonds')[update.message.text]

    message = fr"Суточная сводка для зонда {update.message.text}" + "\n\n"
    update.message.reply_markdown_v2(
        text=escape_markdown(message, version=2),
        reply_markup=ReplyKeyboardRemove())

    update.message.reply_markdown_v2(
        text=device_report_callback(device, "zond", period=1),
        reply_markup=ReplyKeyboardRemove())

    message = fr"Недельная сводка для зонда {update.message.text}" + "\n\n"
    update.message.reply_markdown_v2(
        text=escape_markdown(message, version=2),
        reply_markup=ReplyKeyboardRemove())

    update.message.reply_markdown_v2(
        text=device_report_callback(device, "zond", period=7),
        reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


zonds_conv = ConversationHandler(
    entry_points=[CommandHandler('zonds', zonds_command)],
    states={
        ZOND_STEP: [MessageHandler(Filters.text & (
            ~ Filters.text("/cancel")), enter_zond)]
    },
    fallbacks=[CommandHandler('cancel', cancel_command)],
    allow_reentry=True,
    persistent=False)
