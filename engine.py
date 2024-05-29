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

		if pi is not None:
			combs = list(itertools.permutations(list(range(6)), 3))
			prob_combs = []

			for com in combs:
				prob = pi[0][com[0]] * pi[1][com[1]] * pi[2][com[2]]
				com_str = '-'.join([str(c + 1) for c in com])

				prob_combs.append((prob, com_str))

			prob_combs.sort(key = lambda x: x[0], reverse = True)
			
			ret = {'code': 0, 'predict': {}, 'best': '', 'why': ''}
			ret['best'] = prob_combs[0][1]

			prediction = ret['predict']

			for prob, com in prob_combs[:10]:
				prediction[com] = '{:.4f}'.format(prob)

			print(prob_combs[0][1])

			justify = self.__justify__(before_info, game_id, idx, prob_combs[0][1])
			ret['why'] = justify
		else:
			ret = {'code': -1, 'predict': {}, 'best': '', 'why': 'Before-game info not found.'}

		return ret

	def __get_pi__(self, fetch_type, fetch_param, game_id):
		state_ex = get_state(fetch_type, fetch_param, game_id, self.id_data, self.game_data, self.course_data)

		if state_ex is not None:
			state, before_info, game_id, idx = state_ex			
			pi = self.net.eval([state], False)[0]

			return pi, before_info, game_id, idx
		else:
			return None, None, None, None

	def __justify__(self, before_info, game_id, idx, best_comb):
		stats = get_statistics(before_info, game_id, idx, self.id_data, self.game_data, self.course_data)
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
				"content": f"{{\n\t\"ticket\": \"{best_comb}\"\n}}"
			},
			{
				"role": "user",
				"content": justify_user_prompt_2.format(
					comb = best_comb,
					jcd = jcd,
					general_stat = self.__tablize__(general_stat),
					jcd_stat = self.__tablize__(jcd_stat)
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
			except Exception:
				continue

		if llm_ok:
			return ret
		else:
			return 'AI failed to justify the claim.'

	def __tablize__(self, stat):
		cols = list(stat[0].keys())		
		table = 'player_number'

		for c in cols:
			table += '|' + c

		for i in range(6):
			table += '\n' + str(i + 1)

			for c in cols:
				table += '|' + stat[i][c]

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
