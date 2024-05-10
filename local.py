import xml.etree.ElementTree as ET

def read_file(file):
	with open(file, 'r', encoding = 'utf-8', errors = 'place') as fp:
		text = fp.read()

	return text

def read_xml_course(file):
	keys = [
		'p_sinnyu1', 'p_3ren1', 'p_sttiming1', 'p_stjun1', 'p_3ren11', 'p_3ren12', 'p_3ren13',
		'p_sinnyu2', 'p_3ren2',	'p_sttiming2', 'p_stjun2', 'p_3ren21', 'p_3ren22', 'p_3ren23',
		'p_sinnyu3', 'p_3ren3', 'p_sttiming3', 'p_stjun3', 'p_3ren31', 'p_3ren32', 'p_3ren33',
		'p_sinnyu4', 'p_3ren4', 'p_sttiming4', 'p_stjun4', 'p_3ren41', 'p_3ren42', 'p_3ren43',
		'p_sinnyu5', 'p_3ren5', 'p_sttiming5', 'p_stjun5', 'p_3ren51', 'p_3ren52', 'p_3ren53',
		'p_sinnyu6', 'p_3ren6', 'p_sttiming6', 'p_stjun6', 'p_3ren61', 'p_3ren62', 'p_3ren63'
	]

	xml = read_file(file)
	root = ET.fromstring(xml)

	table = root.find('table')
	infos = {}

	for record in table.findall('record'):
		player_id = record.find('toban').text
		f = {}

		for k in keys:
			f[k] = float(record.find(k).text)

		infos[player_id] = f
		print(f.values())

	return infos

def read_xml_before_info(file):
	xml = read_file(file)
	root = ET.fromstring(xml)

	table = root.find('table')
	race_id = table.get('race_id')
	games = {}
	
	for record in table.findall('record'):
		rno = record.find('rno').text
		game_id = f'{race_id}_{rno}'

		stime = record.find('stime').text
		lineup = {}

		for waku in record.findall('waku'):
			line_id = int(waku.find('teiban').text)

			info = {
				'player_id': waku.find('toban').text,
				'gender': int(waku.find('seibetsu').text),
				'weight': float(waku.find('taiju').text),
				'adj_weight': float(waku.find('ctaiju').text),
				'warm_time': float(waku.find('ttime').text),
				'tilt': float(waku.find('tiltc').text)
			}
			lineup[line_id] = info
			print(info.values())

		games[game_id] = lineup

	return games

if __name__ == '__main__':
	read_xml_before_info('./snippet/before_info.xml')
	read_xml_course('./snippet/course.xml')
