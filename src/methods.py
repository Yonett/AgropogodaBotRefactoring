import time
import requests

from datetime import datetime

from config import API_ADDRESS, MONITOR_API_ADDRESS


def get_rainfall(message: str, period: int):
    r = requests.get(f"{API_ADDRESS}/telegram/all_zonds")
    devices = r.json()

    for device in devices:
        if device['zond_type_id'] == 4 and device['zond_status_id'] == 1:
            if '(демо)' not in device['number']:
                params = {
                    "number_in_db": device['number_in_db'],
                    "end_date": int(time.time()),
                    "start_date": int(time.time()) - period,
                }
                dh = requests.get(f"{MONITOR_API_ADDRESS}/digital_helper", params=params)
                rn = dh.json()['RainfallStats']['Sum']

                district = city = "не установлено"
                if device.get('location_region') and device.get('location_city'):
                    district = device['location_region']['short_name']
                    city = device['location_city']['name']

                message += fr"{device['zond_type']['type']} №{device['number']} ({city}, {district}): {rn:.2f} мм" + "\n"

    return message


def device_report_callback(device: str, device_type: str, period: int):
    params = {
        "number_in_db": device,
        "end_date": int(time.time()),
        "start_date": int(time.time()) - 86400 * period,
    }

    m = requests.get(f'{MONITOR_API_ADDRESS}/get_metrics_with_function/raw/avg', params=params)
    r = requests.get(f"{MONITOR_API_ADDRESS}/digital_helper", params=params)

    if r.status_code != 200 or m.status_code != 200:
        message = "Ой, что-то пошло не так. Попробуйте позже, скоро всё исправим!"
        return message

    message = get_formatted_report(digital_helper_stats=r.json(), metrics=m.json(),
                                   device_type=device_type, period=period)
    return message


def get_formatted_report(digital_helper_stats: {}, metrics: {}, device_type: str, period: int) -> str:
    t = digital_helper_stats

    if not t['TemperatureStats']['Count']:
        return "Недостаточно измерений для построения отчёта"

    for key1 in t.keys():
        if t[key1]:
            for key2 in t[key1].keys():
                if type(t[key1][key2]) == float:
                    t[key1][key2] = round(float(t[key1][key2]), 1)
                    t[key1][key2] = str(t[key1][key2]).replace(".", r'\.')

                t[key1][key2] = str(t[key1][key2]).replace("-", r'\-')

    temperature_avg = {'t0': 0, 't1': 0, 't2': 0, 't3': 0, 't4': 0, 't5': 0, 't6': 0}
    if device_type == "zond":
        for m in metrics:
            for level in temperature_avg.keys():
                temperature_avg[level] += m[level]

        for level in temperature_avg.keys():
            temperature_avg[level] /= len(metrics)
            temperature_avg[level] = str(round(temperature_avg[level])).rjust(2, "0")

    message = ""
    date_format = r'%d\.%m, %H:%M'

    max_t_date = datetime.utcfromtimestamp(int(t['PeakTemperature']['MaxDate'])).strftime(date_format)
    min_t_date = datetime.utcfromtimestamp(int(t['PeakTemperature']['MinDate'])).strftime(date_format)

    max_pr_date = datetime.utcfromtimestamp(int(t['PeakPressure']['MaxDate'])).strftime(date_format)
    min_pr_date = datetime.utcfromtimestamp(int(t['PeakPressure']['MinDate'])).strftime(date_format)

    max_hm_date = datetime.utcfromtimestamp(int(t['PeakHumidity']['MaxDate'])).strftime(date_format)
    min_hm_date = datetime.utcfromtimestamp(int(t['PeakHumidity']['MinDate'])).strftime(date_format)

    message += fr"Макс\. темп\. воздуха: *{t['PeakTemperature']['MaxT']}°C* \({max_t_date}\)" + "\n"
    message += fr"Мин\. темп\. воздуха: *{t['PeakTemperature']['MinT']}°C* \({min_t_date}\)" + "\n"
    message += "\n"
    message += fr"Макс\. влажн\. воздуха: *{t['PeakHumidity']['MaxHm']}%* \({max_hm_date}\)" + "\n"
    message += fr"Мин\. влажн\. воздуха: *{t['PeakHumidity']['MinHm']}%* \({min_hm_date}\)" + "\n"
    message += "\n"

    if period == 1:
        message += fr"Макс\. атм\. давление: *{t['PeakPressure']['MaxPr']} Па* \({max_pr_date}\)" + "\n"
        message += fr"Мин\. атм\. давление: *{t['PeakPressure']['MinPr']} Па* \({min_pr_date}\)" + "\n"
        message += "\n"

    if device_type == "post":
        far = int(float(t['FARStats']['IntegralSum'].replace(r'\.', '.')) / 1000)
        message += f"Сумма ФАР: *{far} кВт/м²*" + "\n"
        message += f"Сумма осадков: *{t['RainfallStats']['Sum']} мм*" + "\n"
        message += "\n"
        message += f"Ветер: преимущественно *{t['WindStats']['WindDirection']}*" + "\n"
        message += f"Порывы до *{t['WindStats']['MaxWindGusts']} м/с*" + "\n"
        message += "\n"
    else:
        if not period != 1:
            message += f"Сумма полезных температур" + "\n"
            message += fr"\- выше 0°C: *{t['GrowingSeasonHeatSupply']['T0']}*" + "\n"
            message += fr"\- выше 5°C: *{t['GrowingSeasonHeatSupply']['T5']}*" + "\n"
            message += fr"\- выше 10°C: *{t['GrowingSeasonHeatSupply']['T10']}*" + "\n"
            message += "\n"

    if device_type == "zond":
        message += "Средняя температура грунта на глубине:" + "\n"

        message += f"0 см: \t*{temperature_avg['t0']}*°C" + "\n"
        message += f"5 см: \t*{temperature_avg['t1']}*°C" + "\n"
        message += f"10 см: \t*{temperature_avg['t2']}*°C" + "\n"
        message += f"20 см: \t*{temperature_avg['t3']}*°C" + "\n"
        message += f"30 см: \t*{temperature_avg['t4']}*°C" + "\n"
        message += f"40 см: \t*{temperature_avg['t5']}*°C" + "\n"
        message += f"50 см: \t*{temperature_avg['t6']}*°C" + "\n"

    return message
