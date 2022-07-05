from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from keyboards import get_regions_keyboard
from commands import cancel_command

REGION_STEP = range(1)


def regions_command(update: Update, context: CallbackContext) -> None:
    reply_markup = ReplyKeyboardMarkup(get_regions_keyboard())
    update.message.reply_markdown_v2(
        text="Выберите район: ", reply_markup=reply_markup)

    return REGION_STEP


def enter_region(update: Update, context: CallbackContext) -> None:
    update.message.reply_markdown_v2(
        text=f"Отчёт для {update.message.text}",
        reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


regions_conv = ConversationHandler(
    entry_points=[CommandHandler('regions', regions_command)],
    states={
        REGION_STEP: [MessageHandler(Filters.text & (
            ~ Filters.text("/cancel")), enter_region)]
    },
    fallbacks=[CommandHandler('cancel', cancel_command)],
    allow_reentry=True,
    persistent=False)
