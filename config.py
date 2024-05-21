openai_key = 'your_openai_api_key'

local_xml_path = '/home/kusanagi/dev-sunacchiiis/DocumentRoot/_get_xmldata'

scrape_username = 'sanspo02'
scrape_password = 'DZZA4828'

test_url = 'https://xml-sv.boatrace.jp/cms/race_main.xml'

date_targets = {
    'result': 'https://xml-sv.boatrace.jp/race/{date}/{place}/result.xml',
    'before': 'https://xml-sv.boatrace.jp/race/{date}/{place}/before_info.xml',
    'award': 'https://xml-sv.boatrace.jp/race/{date}/race_har.xml'
}

player_targets = {
    'course': 'https://xml-sv.boatrace.jp/profile/{player}/course.xml',
    'three': 'https://xml-sv.boatrace.jp/profile/{player}/3setu.xml'
}

raw_dat_path = './data/raw.dat'
train_dat_path = './data/train.dat'

feedback_len = 64

before_arr_len = 31
player_arr_len = 42 * 6
history_arr_len = 45

batch_size = 256

jcd_map = {
	'01': '桐生', '02': '戸田', '03': '江戸川', '	04': '平和島', '05': '多摩川', '06': '浜名湖',
	'07': '蒲郡', '08': '常滑', '09': '津', '10': '三国', '11': 'びわこ', '12': '住之江',
	'13': '尼崎', '14': '鳴門', '15': '丸亀', '16': '児島', '17': '宮島', '18': '徳山',
	'19': '下関', '20': '若松', '21': '芦屋', '22': '福岡', '23': '唐津', '24': '大村'
}

course_keys = [
	'p_sinnyu1', 'p_3ren1', 'p_sttiming1', 'p_stjun1', 'p_3ren11', 'p_3ren12', 'p_3ren13',
	'p_sinnyu2', 'p_3ren2',	'p_sttiming2', 'p_stjun2', 'p_3ren21', 'p_3ren22', 'p_3ren23',
	'p_sinnyu3', 'p_3ren3', 'p_sttiming3', 'p_stjun3', 'p_3ren31', 'p_3ren32', 'p_3ren33',
	'p_sinnyu4', 'p_3ren4', 'p_sttiming4', 'p_stjun4', 'p_3ren41', 'p_3ren42', 'p_3ren43',
	'p_sinnyu5', 'p_3ren5', 'p_sttiming5', 'p_stjun5', 'p_3ren51', 'p_3ren52', 'p_3ren53',
	'p_sinnyu6', 'p_3ren6', 'p_sttiming6', 'p_stjun6', 'p_3ren61', 'p_3ren62', 'p_3ren63'
]