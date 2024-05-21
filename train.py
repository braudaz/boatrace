
from tqdm import tqdm
from config import *
from util import *
from net import *
import numpy as np
import argparse
import joblib
import random
import time
import glob
import os

def train_ai(net, count, is_new, is_eval_first):
	train_records, test_records = joblib.load(train_dat_path)
	true_pi = []

	for _, _, _, pi in test_records:
		true_pi.append(pi)

	true_pi = np.argmax(np.stack(true_pi), axis = -1)

	log_dir = './logs'
	log_file = log_dir + '/__log__.txt'
	
	def _log_(msg = ''):
		bilog(log_file, msg)

	last_model_file = './logs/best.ckpt'
	
	best_acc, epoch = 0, 0

	if not is_new:
		model_files = glob.glob(log_dir + '/*.ckpt')

		for f in sorted(model_files):
			if f.endswith('best.ckpt'): continue

			last_model_file = f.replace('\\', '/')
			segs = last_model_file.split('/')[-1][:-5].split('_')

			epoch = int(segs[0].split('=')[1])
			acc = float(segs[1].split('=')[1])

			if acc >= best_acc: best_acc = acc
	else:
		last_model_file = None
		rmdir(log_dir)

	if net is None: net = Net(last_model_file)
	batches = len(train_records) // batch_size

	_log_()
	_log_('* train {} on {}'.format(
		'started' if epoch == 0 else 'resumed',
		time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
	))
	_log_()

	def eval():
		pred_pi = np.argmax(net.eval(test_records), axis = -1)
		strict_matches, loose_matches = 0, 0

		for i in range(len(true_pi)):
			tpi, ppi = list(true_pi[i])[:3], list(pred_pi[i])[:3]

			if tuple(tpi) == tuple(ppi): strict_matches += 1
			if set(tpi) == set(ppi): loose_matches += 1

		return strict_matches / len(true_pi), loose_matches / len(true_pi)

	if is_eval_first:
		strict_acc, loose_acc = eval()

		_log_('* first evaluation: strict_acc={:.4f}, loose_acc={:.4f}'.format(strict_acc, loose_acc))
		_log_()

	for _ in range(count):
		epoch += 1
		sum_loss = 0

		for _ in tqdm(range(batches), desc = 'training', leave = False):
			train_samples = random.sample(train_records, batch_size)
			sum_loss += net.train(train_samples)

		loss = sum_loss / batches
		strict_acc, loose_acc = eval()

		net.save('{}/epoch={:04}_strict={:.4f}_loose={:.4f}_loss={:.4f}.ckpt'.format(
			log_dir, epoch, strict_acc, loose_acc, loss
		))
		_log_('epoch-{:04}: strict_acc={:.4f}, loose_acc={:.4f}, loss={:.4f}'.format(
			epoch, strict_acc, loose_acc, loss
		))

		if strict_acc >= best_acc:
			net.save('{}/best.ckpt'.format(log_dir))
			best_acc = strict_acc

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-c', '--count', type = int, default = 1000, help = 'number of epochs to train')
	parser.add_argument('-n', '--new', action = 'store_true', default = False, help = 'new start')
	parser.add_argument('-e', '--eval', action = 'store_true', default = False, help = 'evaluate first')
	args = parser.parse_args()

	train_ai(None, args.count, args.new, args.eval)
