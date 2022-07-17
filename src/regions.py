import requests
import time
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

from config import API_ADDRESS, MONITOR_API_ADDRESS
from keyboards import get_regions_keyboard
from commands import cancel_command
from labels import Labels
from methods import get_formatted_report
from decorators import auth_check, catcher, log
from metrics import commands_counter

REGION_STEP, _ = range(2)


@catcher
@log
@auth_check
def regions_command(update: Update, context: CallbackContext):
    commands_counter.labels(Labels.REGIONS.value).inc()
    if not context.user_data.get('is_admin'):
        update.message.reply_markdown_v2(
            text="У вас нет прав для выполнения данной команды")

        return ConversationHandler.END
    else:
        reply_markup = ReplyKeyboardMarkup(get_regions_keyboard())
        update.message.reply_markdown_v2(
            text="Выберите район: ", reply_markup=reply_markup)

        return REGION_STEP


def enter_region(update: Update, context: CallbackContext):
    headers = {'Authorization': 'Bearer ' + str(context.user_data.get('token'))}
    devices = requests.get(f"{API_ADDRESS}/lk/zonds", headers=headers).json()

    filtered = []

    for device in devices:
        try:
            lr = (device['location_region']['name']) if device['location_region'] else 'Неизвестно'
        except KeyError:
            continue
        if lr == update.message.text:
            filtered.append(device)

    data_arr = []
    posts_stats = {}

    def _avg(metric):
        temp = {}
        for zond_data in data_arr:
            for packet in zond_data:

                if not packet[metric]:
                    continue

                if not temp.get(packet['date']):
                    temp[packet['date']] = []

                if metric in ['soil1c', 'soil2c', 'soil3c']:
                    temp[packet['date']].append(packet[metric])
                    continue
                elif metric in ['soil1', 'soil2', 'soil3']:
                    temp[packet['date']].append(packet[metric] * 100 / 4096)
                    continue

                temp[packet['date']].append(packet[metric])

        return [sum(arr) / len(arr) for arr in temp.values()]

    def _dates():
        return [m['date'] for m in data_arr[0]]

    update.message.reply_markdown_v2(text=f"Недельная сводка для {update.message.text}",
                                     reply_markup=ReplyKeyboardRemove())
    for zond in filtered:
        if zond["zond_type"]["displayed_name"] == "Пост":
            post_number = zond["number_in_db"]
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

            if len(posts_stats) == 0:
                posts_stats = r.json()
            else:
                if r.json()['PeakTemperature']['MaxT'] > posts_stats['PeakTemperature']['MaxT']:
                    posts_stats['PeakTemperature']['MaxT'] = r.json()['PeakTemperature']['MaxT']
                    posts_stats['PeakTemperature']['MaxDate'] = r.json()['PeakTemperature']['MaxDate']

                if r.json()['PeakTemperature']['MinT'] < posts_stats['PeakTemperature']['MinT']:
                    posts_stats['PeakTemperature']['MinT'] = r.json()['PeakTemperature']['MinT']
                    posts_stats['PeakTemperature']['MinDate'] = r.json()['PeakTemperature']['MinDate']

                if r.json()['PeakHumidity']['MaxHm'] > posts_stats['PeakHumidity']['MaxHm']:
                    posts_stats['PeakHumidity']['MaxHm'] = r.json()['PeakHumidity']['MaxHm']
                    posts_stats['PeakHumidity']['MaxDate'] = r.json()['PeakHumidity']['MaxDate']

                if r.json()['PeakHumidity']['MinHm'] < posts_stats['PeakHumidity']['MinHm']:
                    posts_stats['PeakHumidity']['MinHm'] = r.json()['PeakHumidity']['MinHm']
                    posts_stats['PeakHumidity']['MinDate'] = r.json()['PeakHumidity']['MinDate']

                if r.json()['WindStats']['MaxWindGusts'] > posts_stats['WindStats']['MaxWindGusts']:
                    posts_stats['WindStats']['MaxWindGusts'] = r.json()['WindStats']['MaxWindGusts']

                posts_stats['FARStats']['IntegralSum'] += r.json()['FARStats']['IntegralSum']
                posts_stats['RainfallStats']['Sum'] += r.json()['RainfallStats']['Sum']

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

        if len(posts_stats) > 0:
            update.message.reply_markdown_v2(get_formatted_report(digital_helper_stats=posts_stats, metrics={},
                                                                  device_type="post", period=7))

    return ConversationHandler.END


regions_conv = ConversationHandler(
    entry_points=[CommandHandler(Labels.REGIONS.value, regions_command)],
    states={
        REGION_STEP: [MessageHandler(Filters.text & (
            ~ Filters.text(f"/{Labels.CANCEL.value}")), enter_region)]
    },
    fallbacks=[CommandHandler(Labels.CANCEL.value, cancel_command)],
    allow_reentry=True,
    persistent=False)
