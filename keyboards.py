import requests

from telegram.ext import CallbackContext

from config import API_ADDRESS


def get_posts_keyboard(context: CallbackContext):
    return get_devices_keyboard(context, types=[4], statuses=[1])


def get_zonds_keyboard(context: CallbackContext):
    return get_devices_keyboard(context, types=[5, 6], statuses=[1])


def get_regions_keyboard():
    r = requests.get(f"{API_ADDRESS}/telegram/location_region?_start=0&_end=100")
    regions = r.json()

    temp = []
    buttons = []

    for region in regions:
        temp.append(region['name'])
        buttons.append(temp)
        temp = []

    return buttons


def get_agromodels_keyboard(context: CallbackContext):
    headers = {'Authorization': 'Bearer ' + str(context.user_data.get('token'))}
    r = requests.get(f"{API_ADDRESS}/lk/agro_models", headers=headers)
    data = r.json()

    temp = []
    models = []
    agromodels = {}

    for i in data:
        if i['is_enabled'] and i['use_for_posts']:
            temp.append(i['name'])
            agromodels[i['name']] = i['link']
            models.append(temp)
            temp = []

    context.user_data['agromodels'] = agromodels

    return models


def get_sections_keyboard(context: CallbackContext):
    r = requests.get(f'{API_ADDRESS}/telegram/wiki_section/1')
    section = r.json()

    temp = []
    buttons = []
    wiki_sections = {}

    for c in section['child_sections']:
        wiki_sections[c['name']] = c['id']
        temp.append(c['name'])
        buttons.append(temp)
        temp = []

    context.user_data['wiki_sections'] = wiki_sections
    return buttons


def get_pages_keyboard(context: CallbackContext):
    url = f'{API_ADDRESS}/telegram/wiki_section/'
    chosen_section = context.user_data.get('section')
    r = requests.get(url + str(context.user_data.get('wiki_sections')[str(chosen_section)]))
    data = r.json()

    temp = []
    buttons = []
    wiki_pages = {}

    for c in data['wiki_pages']:
        wiki_pages[c['title']] = c['id']
        temp.append(c['title'])
        buttons.append(temp)
        temp = []

    context.user_data['wiki_pages'] = wiki_pages
    return buttons


def get_companies_keyboard(context: CallbackContext):
    r = requests.get(f'{API_ADDRESS}/telegram/company?_start=0&_end=-1')
    companies = r.json()

    temp = []
    buttons = []

    for company in companies:
        if company['location_region_id'] > 0:
            if company['location_region']['name'] == context.user_data.get('region'):
                temp.append(company['name'])
                buttons.append(temp)
                temp = []

    context.user_data['companies'] = companies

    return buttons


def get_devices_keyboard(context: CallbackContext, types=(), statuses=()):
    headers = {'Authorization': 'Bearer ' + str(context.user_data.get('token'))}
    zonds = requests.get(f"{API_ADDRESS}/lk/zonds", headers=headers).json()

    temp = []
    buttons = []
    devices = {}

    for z in zonds:
        if z['zond_status_id'] in statuses and z['zond_type_id'] in types:
                try:
                    n = z['number_in_db']
                    lr = (z['location_region']['short_name']) if z['location_region'] else 'Неизвестно'
                    lc = (z['location_city']['name']) if z['location_city'] else 'Неизвестно'
                except Exception as e:
                    print(e)
                    continue
                name = f"{n} ({lc}, {lr})"
                devices[name] = n
                temp.append(name)
                buttons.append(temp)
                temp = []

    if types == [4]:
        context.user_data['posts'] = devices
    elif types == [5, 6]:
        context.user_data['zonds'] = devices

    return buttons