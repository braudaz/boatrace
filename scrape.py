from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
import requests
import pickle
import os

scrape_dates = True
scrape_players = True

start_date = datetime(2012, 4, 12)
end_date = datetime(2024, 5, 10)

username = 'sanspo02'
password = 'DZZA4828'

date_targets = [
    ('result', 'http://xml-sv.boatrace.jp/race/{date}/[jcd]/result.xml'),
    ('before', 'http://xml-sv.boatrace.jp/race/{date}/[jcd]/before_info.xml'),
    ('award', 'http://xml-sv.boatrace.jp/race/{date}/race_har.xml')
]

player_targets = [
    ('course', 'http://xml-sv.boatrace.jp/profile/{player}/course.xml'),
    ('three', 'http://xml-sv.boatrace.jp/profile/{player}/3setu.xml')    
]

def scrape(url, file):
    response = requests.get(url, auth = HTTPBasicAuth(username, password))

    if response.status_code == 200:
        with open(file, 'wb') as file:
            file.write(response.content)

        return True
    else:
        return False

if not os.path.exists('./download'): os.makedirs('./download')

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
            url = target_url.format(date = date.strftime('%Y%m%d'))
            file = f'./download/{target_name}_{date.strftime('%Y%m%d')}.xml'

            ok = scrape(url, file)

            if ok:
                if target_name == 'result': valid_dates.append(date)
                print(f'- got {url}')

    with open('./download/__valid_dates__.dat', 'wb') as fp:
        pickle.dump(valid_dates, fp)
else:
    with open('./download/__valid_dates__.dat', 'rb') as fp:
        valid_dates = pickle.load(fp)

print(f'- total {len(valid_dates)} valid dates found.')