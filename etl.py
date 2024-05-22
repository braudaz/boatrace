from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
from tqdm import tqdm
from config import *
from util import *
import xml.etree.ElementTree as ET
import numpy as np
import traceback
import requests
import joblib
import random
import os

out_dirs = ['./data', './tmp']

for di in out_dirs:
	mkdir(di)

def read_file(file):
	with open(file, 'r', encoding = 'utf-8', errors = 'place') as fp:
		text = fp.read()

	return text

def scrape_url(url, file):
	response = requests.get(url, auth = HTTPBasicAuth(scrape_username, scrape_password))

	if response.status_code == 200:
		with open(file, 'wb') as fp:
			fp.write(response.content)

		return True
	elif response.status_code == 404:
		return False
	else:
		print(f'$$$ error scraping url: {url}')
		print(f'$$$ code = {response.status_code}')
		input('$$$ continue?')

		return False

def read_xml_course(file):
	xml = read_file(file)
	root = ET.fromstring(xml)

	table = root.find('table')
	infos = {}

	for record in table.findall('record'):
		player_id = record.find('toban').text
		infos[player_id] = [safe_float(record.find(k).text, 0.0) for k in course_keys]

	return infos

def read_xml_program(file):
	xml = read_file(file)
	root = ET.fromstring(xml)

	table = root.find('table')
	programs = {}

	for record in table.findall('record'):
		for race in record.findall('race'):
			hdate = race.find('hdate').text
			jcd = race.find('jcd').text
			rno = race.find('rno').text

			game_id = f'{jcd}_{hdate}_{rno}'

			stime = stime_secs(race.find('stime').text, True)
			info = []

			for syussou in race.findall('syussou'):
				line_id = int(syussou.find('teiban').text)
				player_id = syussou.find('toban').text
				gender = int(syussou.find('seibetsu').text)
				weight = safe_float(syussou.find('taiju').text, 51.0)

				info.append((line_id, player_id, gender, weight, 0.0, 6.9, 0))

			info.sort(key = lambda x: x[0])
			programs[game_id] = (stime, info)

	return programs

def read_xml_before(file):
	xml = read_file(file)
	root = ET.fromstring(xml)

	table = root.find('table')
	race_id = table.get('race_id')
	befores = {}
	
	for record in table.findall('record'):
		rno = record.find('rno').text
		game_id = f'{race_id}_{rno}'

		stime = stime_secs(record.find('stime').text, True)
		info = []

		for waku in record.findall('waku'):
			line_id = int(waku.find('teiban').text)
			player_id = waku.find('toban').text
			gender = int(waku.find('seibetsu').text)
			weight = safe_float(waku.find('taiju').text, 51.0)
			adj_weight = safe_float(waku.find('ctaiju').text, 0.0)
			warm_time = safe_float(waku.find('ttime').text, 6.9)
			tilt = float(waku.find('tiltc').text)

			info.append((line_id, player_id, gender, weight, adj_weight, warm_time, tilt))

		info.sort(key = lambda x: x[0])
		befores[game_id] = (stime, info)

	return befores

def read_xml_result(file):
	xml = read_file(file)
	root = ET.fromstring(xml)

	table = root.find('table')
	race_id = table.get('race_id')
	results = {}

	for record in table.findall('record'):
		rno = record.find('rno').text
		game_id = f'{race_id}_{rno}'

		stime = stime_secs(record.find('stime').text, False)
		info = []

		for chaku in record.findall('chaku'):
			line_id = int(chaku.find('teiban').text)
			player_id = chaku.find('toban').text
			gender = int(chaku.find('seibetsu').text)
			rank = int(chaku.get('chk'))
			rtime = rtime_secs(chaku.find('rtime').text)
			course = safe_int(chaku.find('cs').text, line_id)
			timing = safe_float(chaku.find('st').text, 0.0)

			info.append((rank, line_id, player_id, gender, rtime, course, timing))

		info.sort(key = lambda x: x[0])
		results[game_id] = (stime, info)

	return results

def safe_int(text, null_val):
	try:
		return int(text)
	except Exception:
		return null_val

def safe_float(text, null_val):
	try:
		return float(text)
	except Exception:
		return null_val

def safe_div(num1, num2, null_val):
	if num2 != 0:
		return num1 / num2
	else:
		return null_val

def safe_percent(num1, num2, null_val):
	if num2 != 0:
		return 100 * num1 / num2
	else:
		return null_val

def safe_avg(list, null_val):
	if len(list) > 0:
		return np.average(list)
	else:
		return null_val

def safe_num_str(num, format_str, null_str):
	if type(num) == int or type(num) == float:
		return format_str.format(num)
	else:
		return null_str

def stime_secs(stime, is_column):
	if is_column:
		segs = stime.split(':')		
	else:
		segs = [stime[:2], stime[2:]]

	return int(segs[0]) * 60 + int(segs[1])

def rtime_secs(rtime):
	try:
		secs = safe_int(rtime.split('"')[1], 0)
	except Exception:
		return 0

	try:
		secs += safe_int(rtime.split("'")[1].split('"')[0], 0) * 60
	except Exception:
		return secs

	try:
		secs += safe_int(rtime.split("'")[0], 0) * 3600
	except Exception:
		return secs

	return secs

def safe_rtime(rtime, null_str):
	try:
		rtime = int(rtime)
		ret = ''

		h = rtime // 3600
		if h > 0: ret += f'{h}\''

		m = (rtime - 3600 * h) // 60
		ret += f'{m}"'

		s = rtime % 60
		ret += f'{s}'

		return ret
	except Exception:
		return null_str

def new_game_data(stime, before_info, result_info):
	return {
		'stime': stime,
		'before': before_info,
		'result': result_info
	}

def update_with_xml(game_data, course_data, xml_type, src_type, src_path):
	if src_type == 'url':
		file = './tmp/scrape.txt'
		if not scrape_url(src_path, file): return False
	else:
		file = src_path

	if xml_type == 'before':
		befores = read_xml_before(file)

		for game_id, v in befores.items():
			stime, info = v

			if game_id not in game_data:
				game_data[game_id] = new_game_data(stime, info, None)
			else:
				game_data[game_id]['before'] = info
				game_data[game_id]['stime'] = stime
	elif xml_type == 'result':
		results = read_xml_result(file)

		for game_id, v in results.items():
			stime, info = v

			if game_id not in game_data:
				game_data[game_id] = new_game_data(stime, None, info)
			else:
				game_data[game_id]['result'] = info
	elif xml_type == 'course':
		infos = read_xml_course(file)
		course_data.update(infos)

	return True

def dump_local_data(xml_root):
	xml_files = []

	for file in os.listdir(xml_root):
		if not file.endswith('.xml'): continue
		keyword = file.split('_')[0]

		if keyword in ['before', 'result', 'course']:
			xml_files.append((keyword, os.path.join(xml_root, file)))

	print(f'- total {len(xml_files)} xml files found')
	game_data, course_data = {}, {}

	for keyword, file in tqdm(xml_files, desc = 'loading'):
		try:
			update_with_xml(game_data, course_data, keyword, 'file', file)
		except Exception:
			print(f'# error in loading {keyword} --> {file}')
			print(traceback.format_exc())
			exit(-1)

	joblib.dump((game_data, course_data), raw_dat_path)

def game_id_order_tuple(game_id):
	segs = game_id.split('_')
	return segs[1], segs[2]

def load_raw_data(raw_path):
	if os.path.exists(raw_path):
		game_data, course_data = joblib.load(raw_path)
		id_data = get_id_data(game_data)

		return id_data, game_data, course_data
	else:
		print(f'- {raw_path} does not exist. loaded empty placeholders.')
		return [], {}, {}

def get_id_data(game_data):
	id_data = sorted(list(game_data.keys()), key = lambda x: game_id_order_tuple(x))
	return id_data

def check_player_in_game(game_info, player_id):
	if game_info['before']:
		for i, before in enumerate(game_info['before']):
			line_id, pid, gender, weight, adj_weight, warm_time, tilt = before

			if player_id == pid: return i

	return -1

def make_train_record(before_info, stime, history_info, result_info, course_data):
	before_arr, player_arr, history_arr = make_state_record(before_info, stime, history_info, course_data)
	out_arr = make_pi_record(before_info, result_info)	

	return before_arr, player_arr, history_arr, out_arr

def make_state_record(before_info, stime, history_info, course_data):
	before_arr = np.zeros(before_arr_len, dtype = np.float32)
	before_arr[-1] = stime

	player_arr = np.zeros(player_arr_len, dtype = np.float32)
	
	for i, before in enumerate(before_info):
		line_id, player_id, gender, weight, adj_weight, warm_time, tilt = before

		before_arr[i * 5:(i + 1) * 5] = [gender, weight, adj_weight, warm_time, tilt]
		if player_id in course_data: player_arr[i * 42:(i + 1) * 42] = course_data[player_id][:]

	history_arr = np.zeros((6, feedback_len, history_arr_len), dtype = np.float32)

	for pid, history in enumerate(history_info):
		for fid, old_info in enumerate(history):
			old_game_info, old_lid, old_player_id = old_info

			old_before_info = old_game_info['before']
			old_result_info = old_game_info['result']
			old_stime = old_game_info['stime']

			for i, before in enumerate(old_before_info):
				line_id, player_id, gender, weight, adj_weight, warm_time, tilt = before
				history_arr[pid][fid][i * 5:(i + 1) * 5] = [gender, weight, adj_weight, warm_time, tilt]

			history_arr[pid][fid][30] = old_stime
			history_arr[pid][fid][31 + old_lid] = 1

			for rank, result in enumerate(old_result_info):
				_, line_id, player_id, gender, rtime, course, timing = result

				if old_player_id == player_id:
					history_arr[pid][fid][37 + rank] = 1
					history_arr[pid][fid][43] = rtime
					history_arr[pid][fid][44] = course
					break

	return before_arr, player_arr, history_arr

def make_pi_record(before_info, result_info):
	player_id_map = {}

	for i, before in enumerate(before_info):
		line_id, player_id, gender, weight, adj_weight, warm_time, tilt = before
		player_id_map[player_id] = i

	out_arr = np.zeros((6, 6), dtype = np.float32)
	failed_pids = list(range(6))

	for rank, result in enumerate(result_info):
		_, line_id, player_id, gender, rtime, course, timing = result

		if player_id in player_id_map:
			pid = player_id_map[player_id]

			out_arr[rank][pid] = 1
			failed_pids.remove(pid)

	for i, pid in enumerate(failed_pids):
		out_arr[5 - i][pid] = 1

	return out_arr

def get_state(fetch_type, fetch_param, game_id, id_data, game_data, course_data):
	if fetch_type == 'id':
		for i, gid in enumerate(id_data):
			if gid == game_id:
				return get_data_record(game_id, i, id_data, game_data, course_data, False, for_state = True)

		return None

	if fetch_type == 'before' or fetch_type == 'program':
		if fetch_param.startswith('http'):
			file = './tmp/scrape.txt'
			if not scrape_url(fetch_param, file): return None
		else:
			file = fetch_param

		infos = read_xml_before(file) if fetch_type == 'before' else read_xml_program(file)

		if game_id in infos:
			stime, before_info = infos[game_id]
		else:
			return None
	elif fetch_type == 'raw':
		jcd = fetch_param['jcd']
		hdate = fetch_param['hdate']
		rno = fetch_param['rno']

		game_id = f'{jcd}_{hdate}_{rno}'
		stime = stime_secs('15:15', True)

		before_info = []

		for r in fetch_param['waku']:
			before_info.append((r['teiban'], r['toban'], 1, 51.0, 0.0, 6.9, 0.0))

		before_info.sort(key = lambda x: x[0])
	else:
		return None

	idx = len(id_data)

	for i, gid in enumerate(id_data):
		if game_id_order_tuple(gid) >= game_id_order_tuple(game_id):
			idx = i
			break

	history_info = []

	for line_id, player_id, gender, weight, adj_weight, warm_time, tilt in before_info:			
		player_history = []

		for old_game_id in id_data[:idx]:
			old_game_info = game_data[old_game_id]
			old_lid = check_player_in_game(old_game_info, player_id)

			if old_lid >= 0:
				player_history.append((old_game_info, old_lid, player_id))
				if len(player_history) == feedback_len: break

		history_info.append(player_history)

	return make_state_record(before_info, stime, history_info, course_data), before_info, game_id, idx

def get_data_record(game_id, idx, id_data, game_data, course_data, for_train, for_state = False):
	game_info = game_data[game_id]
	before_info = game_info['before']
	
	if before_info is None: return None

	result_info = game_info['result']
	stime = game_info['stime']

	history_info = []

	for line_id, player_id, gender, weight, adj_weight, warm_time, tilt in before_info:			
		player_history = []

		for old_game_id in id_data[:idx]:
			old_game_info = game_data[old_game_id]
			old_lid = check_player_in_game(old_game_info, player_id)

			if old_lid >= 0:
				player_history.append((old_game_info, old_lid, player_id))
				if len(player_history) == feedback_len: break

		history_info.append(player_history)

	if for_train:
		return make_train_record(before_info, stime, history_info, result_info, course_data)
	else:
		if for_state:
			return make_state_record(before_info, stime, history_info, course_data), before_info, game_id, idx
		else:
			return make_state_record(before_info, stime, history_info, course_data)

def get_statistics(before_info, game_id, idx, id_data, game_data, course_data):	
	jcd = game_id.split('_')[0]

	records = [
		{
			'ranks': [],
			'first': 0,
			'second': 0,
			'third': 0,
			'within': 0,
			'rtimes': []
		}
		for _ in range(6)
	]
	general_stats = [
		{
			'rate_of_1st_rank': 'NaN',
			'rate_of_2nd_rank': 'NaN',
			'rate_of_3rd_rank': 'NaN',
			'rate_of_within_3rd_rank': 'NaN',
			'average_start_timing': 'NaN'
		}
		for _ in range(6)
	]
	jcd_stats = [
		{
			'average_rank': 'NaN',
			'rate_of_1st_rank': 'NaN',
			'rate_of_2nd_rank': 'NaN',
			'rate_of_3rd_rank': 'NaN',
			'rate_of_within_3rd_rank': 'NaN',
			'average_arrival_time': 'NaN'
		}
		for _ in range(6)
	]

	lid = 0

	for line_id, player_id, gender, weight, adj_weight, warm_time, tilt in before_info:
		course_info = course_data[player_id]

		if course_info is not None:
			cid = lid + 1

			def nonzero_str(key, is_percent = True):
				v = course_info[course_keys.index(key.format(cid))]

				if v != 0:
					if is_percent:
						return '{:.1f}%'.format(v)
					else:
						return '{:.1f}'.format(v)
				else:
					return 'NaN'

			general_stats[lid]['rate_of_1st_rank'] = nonzero_str('p_3ren{}1')
			general_stats[lid]['rate_of_2nd_rank'] = nonzero_str('p_3ren{}2')
			general_stats[lid]['rate_of_3rd_rank'] = nonzero_str('p_3ren{}3')
			general_stats[lid]['rate_of_within_3rd_rank'] = nonzero_str('p_3ren{}')
			general_stats[lid]['average_start_timing'] = nonzero_str('p_sttiming{}', False)

		for old_game_id in id_data[:idx]:
			old_jcd = old_game_id.split('_')[0]
			if jcd != old_jcd: continue

			old_game_info = game_data[old_game_id]
			old_lid = check_player_in_game(old_game_info, player_id)

			if old_lid < 0: continue

			old_result_info = old_game_info['result']

			for rank, result in enumerate(old_result_info):
				_, line_id, pid, gender, rtime, course, timing = result

				if player_id == pid:
					records[lid]['ranks'].append(rank)
					records[lid]['rtimes'].append(rtime)

					if rank == 0:
						records[lid]['first'] += 1
					elif rank == 1:
						records[lid]['second'] += 1
					elif rank == 2:
						records[lid]['third'] += 1

					if rank <= 2:
						records[lid]['within'] += 1

		lid += 1

	for i in range(6):
		jcd_stats[i]['average_rank'] = safe_num_str(safe_avg(records[i]['ranks'], None), '{:.1f}', 'NaN')
		jcd_stats[i]['rate_of_1st_rank'] = safe_num_str(safe_percent(records[i]['first'], len(records[i]['ranks']), None), '{:.1f}%', 'NaN')
		jcd_stats[i]['rate_of_2nd_rank'] = safe_num_str(safe_percent(records[i]['second'], len(records[i]['ranks']), None), '{:.1f}%', 'NaN')
		jcd_stats[i]['rate_of_3rd_rank'] = safe_num_str(safe_percent(records[i]['third'], len(records[i]['ranks']), None), '{:.1f}%', 'NaN')
		jcd_stats[i]['rate_of_within_3rd_rank'] = safe_num_str(safe_percent(records[i]['within'], len(records[i]['ranks']), None), '{:.1f}%', 'NaN')
		jcd_stats[i]['average_arrival_time'] = safe_rtime(safe_avg(records[i]['rtimes'], None), 'NaN')

	return general_stats, jcd_stats

def prepare_train_data():
	id_data, game_data, course_data = load_raw_data(raw_dat_path)
	all_records = []
	i = 300

	for game_id in tqdm(id_data, desc = 'loading'):
		record = get_data_record(game_id, i, id_data, game_data, course_data, True)
		
		if record: all_records.append(record)
		i += 1

	print(f'- total {len(all_records)} records prepared')
	random.shuffle(all_records)

	train_records = all_records[:int(len(all_records) * 0.9)]
	test_records = all_records[len(train_records):]

	joblib.dump((train_records, test_records), train_dat_path)

def blind_update(id_data, game_data, course_data):
	now = datetime.now()

	for jcd in jcd_map:
		last_date_str = None

		for game_id in id_data[::-1]:
			if game_id.startswith(jcd):
				last_date_str = game_id.split('_')[1]
				break

		if last_date_str is None: continue
		date = datetime.strptime(last_date_str, '%Y%m%d')

		print(f'* last date = {last_date_str} for jcd = {jcd}')

		while date < now:
			xmls = [
				('before', date_targets['before'].format(date = date.strftime('%Y%m%d'), place = jcd)),
				('result', date_targets['result'].format(date = date.strftime('%Y%m%d'), place = jcd)),
			]
			for xml_type, src_path in xmls:
				if update_with_xml(game_data, course_data, xml_type, 'url', src_path): print(f'- fetched {src_path}')

			date += timedelta(days = 1)

	players = set()

	for game_id in game_data:
		before_info = game_data[game_id]['before']

		for line_id, player_id, gender, weight, adj_weight, warm_time, tilt in before_info:
			players.add(player_id)

	for player_id in players:
		src_path = player_targets['course'].format(player = player_id)

		if update_with_xml(game_data, course_data, 'course', 'url', src_path): print(f'- fetched {src_path}')

	joblib.dump((game_data, course_data), raw_dat_path)

if __name__ == '__main__':
	#read_xml_before('./snippet/before_info.xml')
	#read_xml_course('./snippet/course.xml')
	#read_xml_result('./snippet/result.xml')
	#read_xml_program('./snippet/program.xml')

	#dump_local_data(local_xml_path)
	prepare_train_data()
