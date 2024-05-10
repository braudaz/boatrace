from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
import requests
import pickle
import os

scrape_dates = True
scrape_players = True

only_18 = True

start_date = datetime(2012, 4, 12)
end_date = datetime(2024, 5, 10)

username = 'sanspo02'
password = 'DZZA4828'

test_url = 'https://xml-sv.boatrace.jp/cms/race_main.xml'

date_targets = [
    ('result', 'https://xml-sv.boatrace.jp/race/{date}/{place}/result.xml'),
    ('before', 'https://xml-sv.boatrace.jp/race/{date}/{place}/before_info.xml'),
    ('award', 'https://xml-sv.boatrace.jp/race/{date}/race_har.xml')
]

player_targets = [
    ('course', 'https://xml-sv.boatrace.jp/profile/{player}/course.xml'),
    ('three', 'https://xml-sv.boatrace.jp/profile/{player}/3setu.xml')    
]

def scrape(url, file):
    response = requests.get(url, auth = HTTPBasicAuth(username, password))

    if response.status_code == 200 and file:
        with open(file, 'wb') as file:
            file.write(response.content)
    
    return response

response = scrape(test_url, None)

print(f'\n- code: {response.status_code}\n- content:\n{response.content}')
input('- press enter to continue')

if not os.path.exists('./download'): os.makedirs('./download')

if not only_18:
    all_places = ['{:02}'.format(idx + 1) for idx in range(24)]
else:
    all_places = ['18']

for place in all_places:
    valid_dates = []

    if scrape_dates:
        for target_name, target_url in date_targets:
            if target_name == 'result':
                date, all_dates = start_date, []

                while date < end_date:
                    all_dates.append(date)
                    date += timedelta(days = 1)
            else:
                all_dates = valid_dates

            for date in all_dates:
                url = target_url.format(place = place, date = date.strftime('%Y%m%d'))
                file = './download/{}_{}_{}.xml'.format(target_name, place, date.strftime('%Y%m%d'))

                response = scrape(url, file)

                if response.status_code == 200:
                    if target_name == 'result': valid_dates.append(date)
                    print(f'- got {url}')
                elif response.status_code != 404:
                    print(response.status_code)
                    print(response.content)
                    input('$$$ check please')
                else:
                    print(f'# skipped {url}')

        with open(f'./download/__valid_dates_{place}__.dat', 'wb') as fp:
            pickle.dump(valid_dates, fp)
    else:
        with open(f'./download/__valid_dates_{place}__.dat', 'rb') as fp:
            valid_dates = pickle.load(fp)

    print(f'- total {len(valid_dates)} valid dates found.')
