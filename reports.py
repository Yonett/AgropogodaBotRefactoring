import time

from datetime import datetime

import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

from config import MONITOR_API_ADDRESS
from keyboards import get_regions_keyboard, get_companies_keyboard
from commands import cancel_command
from methods import device_report_callback, get_formatted_report

REGION_STEP, COMPANY_STEP = range(2)


def reports_command(update: Update, context: CallbackContext) -> None:
    reply_markup = ReplyKeyboardMarkup(get_regions_keyboard())
    update.message.reply_markdown_v2(
        text="Выберите район: ", reply_markup=reply_markup)

    return REGION_STEP


def enter_region(update: Update, context: CallbackContext) -> None:
    context.user_data['region'] = update.message.text
    reply_markup = ReplyKeyboardMarkup(get_companies_keyboard(context))
    update.message.reply_markdown_v2(
        text="Выберите компанию: ", reply_markup=reply_markup)

    return COMPANY_STEP


def enter_company(update: Update, context: CallbackContext) -> None:
    # update.message.reply_markdown_v2(
    #     text=f"Отчёт для {update.message.text} из района {context.user_data.get('region')}",
    #     reply_markup=ReplyKeyboardRemove())

    companies = context.user_data.get('companies');
    company = {}
    for _company in companies:
        if _company['name'] == update.message.text:
            company = _company

    post_number = ""

    data_arr = []

    def _avg(metric):
        temp = {}
        for zond_data in data_arr:
            for packet in zond_data:
                if not temp.get(packet['date']):
                    temp[packet['date']] = []

                if metric == 'soil1':
                    try:
                        temp[packet['date']].append(packet[metric] * 100 / 4096)
                        continue
                    except:
                        temp[packet['date']].append(packet['soil1c'])
                        continue
                if metric == 'soil2':
                    try:
                        temp[packet['date']].append(packet[metric] * 100 / 4096)
                        continue
                    except:
                        temp[packet['date']].append(packet['soil2c'])
                        continue
                if metric == 'soil3':
                    try:
                        temp[packet['date']].append(packet[metric] * 100 / 4096)
                        continue
                    except:
                        temp[packet['date']].append(packet['soil3c'])
                        continue

                if not packet[metric]:
                    continue

                temp[packet['date']].append(packet[metric])

        return [sum(arr) / len(arr) for arr in temp.values()]

    def _dates():
        return [m['date'] for m in data_arr[0]]

    update.message.reply_markdown_v2(text=f"Недельная сводка для {update.message.text}", reply_markup=ReplyKeyboardRemove())
    for zond in company["zonds"]:
        if zond["zond_type"]["displayed_name"] == "Пост":
            post_number = zond["number_in_db"]
        if zond["zond_type"]["displayed_name"] == "Зонд":
            params = {
                "number_in_db": zond["number_in_db"],
                "end_date": int(time.time()),
                "start_date": int(time.time()) - 86400 * 7,
            }
            r = requests.get(f'{MONITOR_API_ADDRESS}/get_metrics_with_function/raw/avg', params=params)
            if r.status_code != 200:
                continue

            data = r.json()

            print(data)

            if data is not None and len(data) == 8:
                data_arr.append(data)

    if len(data_arr) != 0:
        dates = _dates()

        t0_arr = _avg('t0')
        t1_arr = _avg('t1')
        t2_arr = _avg('t2')

        s1_arr = _avg('soil1')
        s2_arr = _avg('soil2')
        s3_arr = _avg('soil3')

        message = "Средняя температура грунта\n"
        message += " дата  | 0 см | 5 см | 10 см \n"
        for d, t0, t1, t2 in zip(dates, t0_arr, t1_arr, t2_arr):
            rd = datetime.utcfromtimestamp(d).strftime('%d.%m')
            t0 = str(round(t0)).rjust(2, "0")
            t1 = str(round(t1)).rjust(2, "0")
            t2 = str(round(t2)).rjust(2, "0")
            message += f"{rd} | {t0}℃ | {t1}℃ | {t2}℃ \n"

        message += "\nСредняя влажность грунта\n"
        message += " дата  | 10 см | 30 см | 60 см \n"
        for d, s1, s2, s3 in zip(dates, s1_arr, s2_arr, s3_arr):
            rd = datetime.utcfromtimestamp(d).strftime('%d.%m')
            s1 = str(round(s1)).rjust(2, "0")
            s2 = str(round(s2)).rjust(2, "0")
            s3 = str(round(s3)).rjust(2, "0")
            message += f"{rd} | {s1}% | {s2}% | {s3}% \n"

        update.message.reply_text(text=message)

    if post_number:
        params = {
            "number_in_db": post_number,
            "end_date": int(time.time()),
            "start_date": int(time.time()) - 86400 * 7,
        }
        r = requests.get(f"{MONITOR_API_ADDRESS}/digital_helper", params=params)
        if r.status_code != 200:
            message = "Ой, что-то пошло не так. Попробуйте позже, скоро всё исправим!"
            update.message.reply_text(message)
            return

        update.message.reply_markdown_v2(get_formatted_report(digital_helper_stats=r.json(), metrics={},
                                                              device_type="post", period=7))
    else:
        update.message.reply_text(r"Нет данных ¯\_(ツ)_/¯")

    return ConversationHandler.END


reports_conv = ConversationHandler(
    entry_points=[
        CommandHandler(
            'reports',
            reports_command)],
    states={
        REGION_STEP: [
            MessageHandler(
                Filters.text & (
                    ~ Filters.text("/cancel")),
                enter_region)],
        COMPANY_STEP: [
            MessageHandler(
                Filters.text & (
                    ~ Filters.text("/cancel")),
                enter_company)]},
    fallbacks=[
        CommandHandler(
            'cancel',
            cancel_command)],
    allow_reentry=True,
    persistent=False)
