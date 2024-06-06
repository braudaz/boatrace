from prompt import *
from config import *
from util import *
from etl import *
from net import *
from llm import *
import itertools
import joblib
import json
import os

fetch_types = [
	'before', 'program', 'raw'
]

class Engine():
	def __init__(self):
		self.refresh_data()
		self.net = Net('./logs/best.ckpt')

	def refresh_data(self):
		self.id_data, self.game_data, self.course_data = load_raw_data(raw_dat_path)

	def predict(self, fetch_type, fetch_param, game_id):
		pi, before_info, game_id, idx = self.__get_pi__(fetch_type, fetch_param, game_id)
		player_names = self.__get_player_names__(fetch_type, fetch_param)

		extra_data = fetch_param.get('extra', '')

		if pi is not None:
			combs = list(itertools.permutations(list(range(6)), 3))
			prob_combs = []

			for com in combs:
				prob = pi[0][com[0]] * pi[1][com[1]] * pi[2][com[2]]
				com_str = '-'.join([str(c + 1) for c in com])

				prob_combs.append((prob, com_str))

			prob_combs.sort(key = lambda x: x[0], reverse = True)
			
			ret = {'code': 0, 'predict': {}, 'best': '', 'best_ex': '', 'why': ''}
			
			ret['best'] = prob_combs[0][1]
			ret['best_ex'] = self.__adjust_prediction__(pi, prob_combs[0][1], player_names, extra_data)

			prediction = ret['predict']

			for prob, com in prob_combs[:10]:
				prediction[com] = '{:.4f}'.format(prob)

			print('best', ret['best'])
			print('best_ex', ret['best_ex'])
			
			justify = self.__justify__(before_info, game_id, idx, ret['best_ex'], player_names, extra_data)

			ret['why'] = justify
		else:
			ret = {'code': -1, 'predict': {}, 'best': '', 'best_ex': '', 'why': 'Before-game info not found.'}

		return ret

	def justify(self, fetch_type, fetch_param, game_id):
		state_ex = get_state(fetch_type, fetch_param, game_id, self.id_data, self.game_data, self.course_data)

		extra_data = fetch_param.get('extra', '')
		ticket = fetch_param.get('ticket', '')		

		try:
			segs = ticket.split('-')

			for i in range(3):
				t = int(segs[i])
		except Exception:
			return {'code': -1, 'why': 'Parameter "ticket" is invalid. Expected "x-y-z" format.'}

		if state_ex is not None:
			state, before_info, game_id, idx = state_ex

			player_names = self.__get_player_names__(fetch_type, fetch_param)
			justify = self.__justify__(before_info, game_id, idx, ticket, player_names, extra_data)

			return {'code': 0, 'why': justify}
		else:
			return {'code': -2, 'why': 'Before-game info not found.'}

	def __get_player_names__(self, fetch_type, fetch_param):
		if fetch_type == 'raw':
			try:
				id_names = []

				for r in fetch_param['waku']:
					id_names.append((r['teiban'], r['name']))

				for _ in range(6 - len(id_names)):
					id_names.append(('9', 'Unknown'))

				id_names.sort(key = lambda x: x[0])
				return [idn[1] for idn in id_names]
			except Exception:
				pass
		
		return [f'選手{i}' for i in range(6)]

	def __get_pi__(self, fetch_type, fetch_param, game_id):
		state_ex = get_state(fetch_type, fetch_param, game_id, self.id_data, self.game_data, self.course_data)

		if state_ex is not None:
			state, before_info, game_id, idx = state_ex
			
			pi = self.net.eval([state], False)[0]

			if fetch_type == 'raw':
				for i, r in enumerate(fetch_param['waku']):
					if r.get('kjo', '0') == '1': pi[:][i] = 0

			return pi, before_info, game_id, idx
		else:
			return None, None, None, None

	def __adjust_prediction__(self, pi, ticket, player_names, extra_data):
		if extra_data:
			messages = [
				{
					"role": "user",
					"content": predict_user_prompt.format(
						ticket = ticket,
						matrix = self.__tabilize_pi__(pi),
						content = extra_data
					)
				},
				{
					"role": "assistant",
					"content": f"{{\n\t\"ticket\": \""
				}
			]
			ret, llm_ok = None, False

			for retry in range(5):
				try:
					llm_res = call_openai_block(
						messages = messages,
						system_prompt = predict_sys_prompt.format(
							names = ', '.join([f'選手{i + 1} - {player_names[i]}' for i in range(6)])
						),
						model = gpt_4_model,
						temperature = 0,
						max_tokens = max_tokens,
						json_response = True
					)
					ret = json.loads(llm_res)['ticket']
					segs = ret.split('-')

					for i in range(3):
						t = int(segs[i])

					llm_ok = True
					break
				except Exception as exc:
					print('err', exc)
					continue

			if llm_ok:
				return ret
			else:
				return ticket
		else:
			return ticket

	def __justify__(self, before_info, game_id, idx, ticket, player_names, extra_data):
		stats = get_statistics(before_info, game_id, idx, self.id_data, self.game_data, self.course_data, player_names)
		if stats is None: return 'Before-game info not found'

		general_stat, jcd_stat = stats
		jcd = jcd_map[game_id.split('_')[0]]
		
		messages = [
			{
				"role": "user",
				"content": justify_user_prompt_1
			},
			{
				"role": "assistant",
				"content": f"{{\n\t\"ticket\": \"{ticket}\"\n}}"
			},
			{
				"role": "user",
				"content": justify_user_prompt_2.format(
					ticket = ticket,
					jcd = jcd,
					general_stat = self.__tabilize_stat__(general_stat),
					jcd_stat = self.__tabilize_stat__(jcd_stat),
					extra = justify_user_extra.format(
						content = extra_data
					) if extra_data else ''
				)
			},
			{
				"role": "assistant",
				"content": "{\n\t\"justify\": \""
			}
		]
		ret, llm_ok = None, False

		for retry in range(5):
			try:
				llm_res = call_openai_block(
					messages = messages,
					system_prompt = justify_sys_prompt.format(jcd = jcd),
					model = gpt_4_model,
					temperature = 0,
					max_tokens = max_tokens,
					json_response = True
				)
				ret = json.loads(llm_res)['justify']
				ret = ret.replace('スタートコース', 'コース')

				llm_ok = True
				break
			except Exception as exc:
				print(exc)
				continue

		if llm_ok:
			return ret
		else:
			return 'AI failed to justify the claim.'

	def __tabilize_stat__(self, stat):
		cols = list(stat[0].keys())		
		table = 'player_number'

		for c in cols:
			table += '|' + c

		for i in range(6):
			table += '\n' + str(i + 1)

			for c in cols:
				table += '|' + stat[i][c]

		return table

	def __tabilize_pi__(self, pi):
		table = 'rank/player'

		for i in range(6):
			table += f'|選手{i + 1}'

		for r in range(6):
			table += f'\nRank{r + 1}'

			for i in range(6):
				table += '|' + '{:.4f}'.format(pi[r][i])

		return table

if __name__ == '__main__':
	engine = Engine()
	ret = engine.predict('id', '', '18_20240201_12')

	with open('./tmp/predict.txt', 'w', encoding = 'utf-8', errors = 'place') as fp:
		fp.write(
			json.dumps(
				ret,
				ensure_ascii = False,
				indent = 4
			)
		)

	print(ret)
