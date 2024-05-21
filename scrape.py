from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
from tqdm import tqdm
from config import *
import requests
import pickle
import os
import re

scrape_dates = True
scrape_players = True

only_18 = False

start_date = datetime(2012, 4, 12)
end_date = datetime(2024, 5, 10)

def scrape(url, file):
    response = requests.get(url, auth = HTTPBasicAuth(scrape_username, scrape_password))

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

if scrape_dates:    
    for place in all_places:
        valid_dates = []

        for target_name, target_url in date_targets.items():
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

        print(f'- total {len(valid_dates)} valid dates found.')

if scrape_players:
    valid_players = set()

    if not os.path.exists('./download/__players__.dat'):
        for place in ['{:02}'.format(idx + 1) for idx in range(24)]:
            if not os.path.exists(f'./download/__valid_dates_{place}__.dat'): continue

            with open(f'./download/__valid_dates_{place}__.dat', 'rb') as fp:
                valid_dates = pickle.load(fp)

            for date in tqdm(valid_dates, desc = f'collect players from {place}'):
                file = './download/result_{}_{}.xml'.format(place, date.strftime('%Y%m%d'))
                count = 0

                with open(file, 'r', encoding = 'utf-8') as fp:
                    text = fp.read()

                for occur in re.finditer(r'\<toban group=\"\w*\"\>([0-9]+)\<\/toban\>', text):
                    p = occur.group(1)
                    valid_players.add(p)

                    count += 1

                print(f'- found {count} players from {file}: total {len(valid_players)}')

        with open('./download/__players__.dat', 'wb') as fp:
            pickle.dump(valid_players, fp)
    else:
        with open('./download/__players__.dat', 'rb') as fp:
            valid_players = pickle.load(fp)

    print(f'- total {len(valid_players)} valid players found.')

    for target_name, target_url in player_targets.items():
        for player in valid_players:
            url = target_url.format(player = player)
            file = './download/{}_{}.xml'.format(target_name, player)

            response = scrape(url, file)

            if response.status_code == 200:
                print(f'- got {url}')
            elif response.status_code != 404:
                print(response.status_code)
                print(response.content)
                input('$$$ check please')
            else:
                print(f'# skipped {url}')
