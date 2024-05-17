
from tqdm import tqdm
from config import *
from util import *
from net import *
import numpy as np
import argparse
import time
import glob
import random
import os

def main(args):
	train_records, test_records = joblib.load(train_dat_path)

	log_dir = './logs'
	log_file = log_dir + '/__log__.txt'
	
	def _log_(msg = ''):
		bilog(log_file, msg)

	last_model_file = './logs/best.ckpt'
	
	best_loss, epoch = 1e10, 0

	if not args.new:
		model_files = glob.glob(log_dir + '/*.ckpt')

		for f in sorted(model_files):
			if f.endswith('best.ckpt'): continue

			last_model_file = f.replace('\\', '/')
			segs = last_model_file.split('/')[-1][:-5].split('_')

			epoch = int(segs[0].split('=')[1])
			loss = float(segs[1].split('=')[1])

			if loss < best_loss: best_loss = loss
	else:
		rmdir(log_dir)

	net = Net(last_model_file)
	batches = len(train_records) // batch_size

	_log_()
	_log_('* train {} on {}'.format(
		'started' if epoch == 0 else 'resumed',
		time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
	))
	_log_()

	for _ in range(args.count):
		epoch += 1
		sum_loss = 0

		for _ in tqdm(range(batches), desc = 'training', leave = False):
			train_samples = random.sample(train_records, batch_size)
			sum_loss += net.train(train_samples)

		loss = sum_loss / batches

		net.save('{}/epoch={:04}_loss={:.4f}.ckpt'.format(
			log_dir, epoch, loss
		))
		_log_('epoch-{:04}: loss={:.4f}'.format(
			epoch, loss
		))

		if loss < best_loss:
			net.save('{}/best.ckpt'.format(log_dir))
			best_loss = loss

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('-c', '--count', type = int, default = 1000, help = 'number of epochs to train')
	parser.add_argument('-n', '--new', action = 'store_true', default = False, help = 'new start')
	args = parser.parse_args()

	main(args)
