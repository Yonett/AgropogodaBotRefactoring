import requests
import re

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from telegram.utils.helpers import escape_markdown
from keyboards import get_sections_keyboard, get_pages_keyboard
from commands import cancel_command
from config import API_ADDRESS
from decorators import log
from labels import Labels
from metrics import commands_counter

SECTION_STEP, PAGE_STEP = range(2)


# @catcher
@log
# @auth_check
def wiki_command(update: Update, context: CallbackContext) -> None:
    commands_counter.labels(Labels.WIKI.value).inc()
    reply_markup = ReplyKeyboardMarkup(get_sections_keyboard(context))
    update.message.reply_markdown_v2(
        text="Выберите раздел: ", reply_markup=reply_markup)

    return SECTION_STEP


def enter_section(update: Update, context: CallbackContext) -> None:
    context.chat_data['section'] = update.message.text
    reply_markup = ReplyKeyboardMarkup(get_pages_keyboard(context))
    update.message.reply_markdown_v2(
        text="Выберите страницу: ", reply_markup=reply_markup)

    return PAGE_STEP


def enter_page(update: Update, context: CallbackContext) -> None:
    """Print page's data"""
    url = f'{API_ADDRESS}/telegram/wiki_page/'
    chosen_page = update.message.text
    r = requests.get(url + str(context.chat_data['wiki_pages'][str(chosen_page)]))
    data = r.json()

    update.message.reply_markdown_v2(
        text=escape_markdown(re.sub('<[^<]+?>', '', data['title']), version=2),
        reply_markup=ReplyKeyboardRemove())

    update.message.reply_markdown_v2(
        text=escape_markdown(re.sub('<[^<]+?>', '', data['text']), version=2),
        reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


wiki_conv = ConversationHandler(
    entry_points=[
        CommandHandler(
            'wiki',
            wiki_command)],
    states={
        SECTION_STEP: [
            MessageHandler(
                Filters.text & (~ Filters.text("/cancel")),
                enter_section)],
        PAGE_STEP: [
            MessageHandler(
                Filters.text & (~ Filters.text("/cancel")),
                enter_page)]},
    fallbacks=[
        CommandHandler(
            'cancel',
            cancel_command)],
    allow_reentry=True,
    persistent=False)
