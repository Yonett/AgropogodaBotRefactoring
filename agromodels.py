import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from telegram.utils.helpers import escape_markdown

from methods import get_agromodels_keyboard, get_posts_keyboard
from commands import cancel_command

AGROMODEL_STEP, POST_STEP = range(2)


def agromodels_command(update: Update, context: CallbackContext) -> None:
    reply_markup = ReplyKeyboardMarkup(get_agromodels_keyboard(context))
    update.message.reply_markdown_v2(
        text="Выберите агромодель: ", reply_markup=reply_markup)
    return AGROMODEL_STEP


def enter_agromodel(update: Update, context: CallbackContext) -> None:
    context.user_data['agromodel'] = update.message.text
    reply_markup = ReplyKeyboardMarkup(get_posts_keyboard(context))
    update.message.reply_markdown_v2(
        text="Выберте пост: ", reply_markup=reply_markup)
    return POST_STEP


def enter_post(update: Update, context: CallbackContext) -> None:
    device = context.user_data.get('posts')[update.message.text]
    link = context.user_data.get('agromodels')[context.user_data['agromodel']]
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
