import requests

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ConversationHandler, CallbackContext
from telegram.utils.helpers import escape_markdown

from config import API_ADDRESS
from labels import Labels
from methods import get_rainfall
from decorators import auth_check, catcher, log, winter_mode
from metrics import commands_counter


@catcher
@log
@auth_check
def start_command(update: Update, _: CallbackContext):
    commands_counter.labels(Labels.START.value).inc()
    user = update.effective_user

    message = fr'Рад знакомству, {user.mention_markdown_v2()}\!' + "\n\n"
    message += r"Я официальный бот проекта https://agropogoda\.com" + "\n\n"
    message += r"Умею показывать текущую метеорологическую ситуацию на полях и давать небольшие прогнозы\." + "\n\n"
    message += r"Список доступных команд: /help"

    update.message.reply_markdown_v2(text=message)


@catcher
@log
@auth_check
def help_command(update: Update, _: CallbackContext):
    commands_counter.labels(Labels.HELP.value).inc()
    message = r"К вашим услугам\! Вот что я умею:" + "\n"
    message += rf"/{Labels.REPORTS.value} \- печать отчёта для компании" + "\n"
    message += rf"/{Labels.REGIONS.value} \- печать отчёта для района" + "\n"
    message += rf"/{Labels.ZONDS.value} \- печать метеосводки для зондов" + "\n"
    message += rf"/{Labels.POSTS.value} \- печать метеосводки для постов" + "\n"
    message += rf"/{Labels.RAINFALL.value} \- данные по осадкам" + "\n"
    message += rf"/{Labels.AGROMODELS.value} \- доступные агромодели" + "\n"
    message += rf"/{Labels.WIKI.value} \- справочник платформы" + "\n"
    message += rf"/{Labels.LEGEND.value} \- сокращения районов" + "\n"

    update.message.reply_markdown_v2(text=message)


@catcher
@log
@auth_check
@winter_mode
def rainfall_command(update: Update, _: CallbackContext):
    commands_counter.labels(Labels.RAINFALL.value).inc()
    message = "Суточные осадки:" + "\n"
    period = 86400
    update.message.reply_markdown_v2(text=escape_markdown(get_rainfall(message, period), version=2))

    message = "Недельные осадки:" + "\n"
    period = 86400 * 7
    update.message.reply_markdown_v2(text=escape_markdown(get_rainfall(message, period), version=2))


@catcher
@log
@auth_check
def legend_command(update: Update, _: CallbackContext):
    commands_counter.labels(Labels.LEGEND.value).inc()
    message = "Используемые сокращения:" + "\n"
    for d in requests.get(f"{API_ADDRESS}/telegram/location_region?_start=0&_end=100").json():
        message += f"{d['short_name']}: {d['name']}" + "\n"

    update.message.reply_markdown_v2(text=escape_markdown(message, version=2))


@catcher
@log
@auth_check
def cancel_command(update: Update, _: CallbackContext):
    update.message.reply_markdown_v2(
        text="Диалог прерван", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END
