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

xml_types = [
	'before', # BR02102: 直前情報
	'course', # BR031: 選手コース別成績
	'result', # BR020: レース結果
	'refund', # BR00301: 払戻金
	'program', # BR014: 出走表
	'other' # Otherwise
]

src_types = ['file', 'url']

class Engine():
	def __init__(self):
		if not os.path.exists(raw_dat_path): dump_local_data(local_xml_path)

		self.id_data, self.game_data, self.course_data = load_raw_data(raw_dat_path)
		self.net = Net('./logs/best.ckpt')

	def on_add_xml(self, xml_type, src_type, src_path):
		update_with_xml(self.game_data, self.course_data, xml_type, src_type, src_path)

		self.id_data = sorted(list(self.game_data.keys()), key = lambda x: game_id_order_tuple(x))

		joblib.dump((self.game_data, self.course_data), raw_dat_path)

	def predict(self, game_id):
		pi = self.__get_pi__(game_id)

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

			justify = self.__justify__(game_id, prob_combs[0][1])
			ret['why'] = justify
		else:
			ret = {'code': -1, 'predict': {}, 'best': '', 'why': 'Before-game info not found.'}

		return ret

	def __get_pi__(self, game_id):
		for i, gid in enumerate(self.id_data):
			if gid == game_id:
				state = get_data_record(game_id, i, self.id_data, self.game_data, self.course_data, False)
				pi = self.net.eval([state])[0]

				return pi

		return None

	def __justify__(self, game_id, best_comb):
		for i, gid in enumerate(self.id_data):
			if gid == game_id:
				stats = get_statistics(game_id, i, self.id_data, self.game_data, self.course_data)
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

						llm_ok = True
						break
					except Exception:
						continue

				if llm_ok:
					return ret
				else:
					return 'AI failed to justify the claim.'

		return 'Before-game info not found'

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
	# Before running,
	# please make sure you have input correct OpenAI API key into `config.py` file.

	# Instantiate engine
	engine = Engine()

	###########################################################################################################################

	# Signal to engine that a new XML is appeared
	# The before-game info is mandatory to predict
	#
	# engine.on_add_xml('before', 'file', '/home/kusanagi/dev-sunacchiiis/DocumentRoot/_get_xmldata/before_18_20240201.xml')
	# or
	# engine.on_add_xml('before', 'url', 'https://xml-sv.boatrace.jp/race/20240201/18/before_info.xml')
	#
	# Also, signal to engine that a new player's course info is added OR existing info is updated.
	#
	# engine.on_add_xml('course', 'file', '/home/kusanagi/dev-sunacchiiis/DocumentRoot/_get_xmldata/course_2876.xml')
	# or
	# engine.on_add_xml('course', 'url', 'https://xml-sv.boatrace.jp/profile/2876/course.xml')

	###########################################################################################################################

	# Engine can predict if the corresponding game's before-game info and course infos for known players are correctly loaded
	# In the following example, the last segment `_12` of `18_20240201_12` is for the race number - <rno>.

	ret = engine.predict('18_20240201_12')

	with open('./tmp/predict.txt', 'w', encoding = 'utf-8', errors = 'place') as fp:
		fp.write(
			json.dumps(
				ret,
				ensure_ascii = False,
				indent = 4
			)
		)

	print(ret)

	# The return of prediction is JSON
	# For e.g.,

	# {
	#	'code': 0, // 0 for success, <0 for failure
	#	'predict': { // top 10 combinations with their probabilities
	#		'3-2-6': 0.100587964,
	#		'3-6-2': 0.06823452,
	#		'3-1-2': 0.03797795,
	#		'3-2-1': 0.032113638,
	#		'3-2-5': 0.02813777,
	#		'3-1-6': 0.026001127,
	#		'3-4-2': 0.020500053,
	#		'3-2-4': 0.01845734,
	#		'3-6-1': 0.014914487,
	#		'3-4-6': 0.014035106
	#	},
	#	'best': '3-2-6', // best combination AI predicted
	#	'why': '''
	#		3-2-6のチケットが最も有望である理由は、以下の統計データに基づいています。まず、選手3は徳山での過去3シーズンの成績において、
	#		平均到着時間が1'12\"45と最も速く、3位以内に入る確率が42.9%と高いです。さらに、現在のスタートコースでの成績でも、
	#		3位以内に入る確率が61.1%と高く、特に2位に入る確率が33.3%と高いです。次に、選手2は徳山での成績で1位になる確率が23.1%、
	#		3位以内に入る確率が53.8%と安定しており、現在のスタートコースでも3位以内に入る確率が72.2%と非常に高いです。
	#		最後に、選手6は徳山での成績で3位以内に入る確率が38.2%と比較的高く、現在のスタートコースでも3位に入る確率が18.8%と一定の実績があります。
	#		これらのデータを総合的に考慮すると、3-2-6の順番が最も有望であると判断できます。
	#	''' // justify for success, error msg for failure
	# }
