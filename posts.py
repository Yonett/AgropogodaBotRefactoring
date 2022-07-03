from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from telegram.utils.helpers import escape_markdown

from methods import get_posts_keyboard, device_report_callback
from commands import cancel_command

POST_STEP = range(1)


def posts_command(update: Update, context: CallbackContext) -> None:
    reply_markup = ReplyKeyboardMarkup(get_posts_keyboard(context))
    update.message.reply_markdown_v2(
        text="Выберите пост: ", reply_markup=reply_markup)

    return POST_STEP


def enter_post(update: Update, context: CallbackContext) -> None:
    device = context.user_data.get('posts')[update.message.text]

    message = fr"Суточная сводка для поста {update.message.text}" + "\n\n"
    update.message.reply_markdown_v2(
        text=escape_markdown(message, version=2),
        reply_markup=ReplyKeyboardRemove())

    update.message.reply_markdown_v2(
        text=device_report_callback(device, "post", 1),
        reply_markup=ReplyKeyboardRemove())

    message = fr"Недельная сводка для поста {update.message.text}" + "\n\n"
    update.message.reply_markdown_v2(
        text=escape_markdown(message, version=2),
        reply_markup=ReplyKeyboardRemove())

    update.message.reply_markdown_v2(
        text=device_report_callback(device, "post", 7),
        reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


posts_conv = ConversationHandler(
    entry_points=[CommandHandler('posts', posts_command)],
    states={
        POST_STEP: [MessageHandler(Filters.text & (~ Filters.text("/cancel")), enter_post)]
    },
    fallbacks=[CommandHandler('cancel', cancel_command)],
    allow_reentry=True,
    persistent=False)
