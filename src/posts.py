from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from telegram.utils.helpers import escape_markdown

from labels import Labels
from methods import device_report_callback
from commands import cancel_command
from keyboards import get_posts_keyboard
from decorators import auth_check, catcher, log
from metrics import commands_counter

POST_STEP = range(1)


@catcher
@log
@auth_check
def posts_command(update: Update, context: CallbackContext) -> None:
    commands_counter.labels(Labels.POSTS.value).inc()
    reply_markup = ReplyKeyboardMarkup(get_posts_keyboard(context))
    update.message.reply_markdown_v2(
        text="Выберите пост: ", reply_markup=reply_markup)

    return POST_STEP


def enter_post(update: Update, context: CallbackContext) -> None:
    device = context.chat_data.get('posts')[update.message.text]

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
    entry_points=[CommandHandler(Labels.POSTS.value, posts_command)],
    states={
        POST_STEP: [MessageHandler(Filters.text & (~ Filters.text(f"/{Labels.CANCEL.value}")), enter_post)]
    },
    fallbacks=[CommandHandler(Labels.CANCEL.value, cancel_command)],
    allow_reentry=True,
    persistent=False)
