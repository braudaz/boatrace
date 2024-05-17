from config import *
import numpy as np
import pickle
import shutil
import glob
import os

def mkdir(path):
	os.makedirs(path, exist_ok = True)

def rmdir(path, remove_self = False):
	gl = sorted(glob.glob(path + '/**', recursive = True))

	for g in gl:
		if not os.path.isdir(g): os.remove(g)

	gl = gl[::-1] if remove_self else gl[:1:-1]

	for g in gl:
		if os.path.isdir(g): os.rmdir(g)

def backup_src(path):
	mkdir(path)

	for pyfile in os.listdir('./'):
		if not pyfile.endswith('.py'): continue
		if os.path.exists(path + '/' + pyfile): continue

		shutil.copy(pyfile, path + '/' + pyfile)

def softmax(x):
	probs = np.exp(x - np.max(x))
	probs /= np.sum(probs)
	return probs
	
def pickle_dump(data, path):
	with open(path, 'wb') as f:
		pickle.dump(data, f)

def pickle_load(path):
	with open(path, 'rb') as f:
		return pickle.load(f)


def bilog(path, msg = ''):
	with open(path, 'a') as f:
		f.write(msg + '\n')

	print(msg)

def get_model_path(fname):
	if os.path.exists(fname): return fname
	paths = glob.glob('./logs/**', recursive = True)

	for f in paths:
		if fname in f: return f

	return fname
