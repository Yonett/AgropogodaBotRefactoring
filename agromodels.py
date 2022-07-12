import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from telegram.utils.helpers import escape_markdown

from keyboards import get_agromodels_keyboard, get_posts_keyboard
from decorators import auth_check, catcher, log, winter_mode
from commands import cancel_command
from metrics import commands_counter
from labels import Labels

AGROMODEL_STEP, POST_STEP = range(2)


@catcher
@log
@auth_check
@winter_mode
def agromodels_command(update: Update, context: CallbackContext) -> None:
    commands_counter.labels(Labels.AGROMODELS.value).inc()
    reply_markup = ReplyKeyboardMarkup(get_agromodels_keyboard(context))
    update.message.reply_markdown_v2(
        text="Выберите агромодель: ", reply_markup=reply_markup)
    return AGROMODEL_STEP


def enter_agromodel(update: Update, context: CallbackContext) -> None:
    context.chat_data['agromodel'] = update.message.text
    reply_markup = ReplyKeyboardMarkup(get_posts_keyboard(context))
    update.message.reply_markdown_v2(
        text="Выберте пост: ", reply_markup=reply_markup)
    return POST_STEP


def enter_post(update: Update, context: CallbackContext) -> None:
    device = context.chat_data.get('posts')[update.message.text]
    link = context.chat_data.get('agromodels')[context.chat_data['agromodel']]
    url = f'{link}?zond={device}'

    r = requests.get(url)

    update.message.reply_markdown_v2(
        text=escape_markdown(r.json()["Text"], version=2),
        reply_markup=ReplyKeyboardRemove())

    update.message.reply_markdown_v2(
        text=escape_markdown(r.json()["Output"], version=2),
        reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


agromodels_conv = ConversationHandler(
    entry_points=[
        CommandHandler(
            'agromodels',
            agromodels_command)],
    states={
        AGROMODEL_STEP: [
            MessageHandler(
                Filters.text & (
                    ~ Filters.text("/cancel")),
                enter_agromodel)],
        POST_STEP: [
            MessageHandler(
                Filters.text & (
                    ~ Filters.text("/cancel")),
                enter_post)]},
    fallbacks=[
        CommandHandler(
            'cancel',
            cancel_command)],
    allow_reentry=True,
    persistent=False)
