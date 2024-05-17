from config import *
import torch.nn.functional as F
import numpy as np
import torch.nn as nn
import torch

class Model(nn.Module):
	def __init__(self):
		super(Model, self).__init__()

		self.hist_dense_1_1 = Dense(history_arr_len, 256, True)
		self.hist_dense_1_2 = Dense(256, 512, True)
		self.hist_dense_1_3 = Dense(512, 16, True)

		self.hist_dense_2_1 = Dense(feedback_len * 16, 1024, True)
		self.hist_dense_2_2 = Dense(1024, 512, True)
		self.hist_dense_2_3 = Dense(512, 256, True)
		self.hist_dense_2_4 = Dense(256, 64, True)

		self.dense_1 = Dense(before_arr_len + player_arr_len + 6 * 64, 1024, True)
		self.dense_2 = Dense(1024, 512, True)
		self.dense_3 = Dense(512, 256, True)
		self.dense_4 = Dense(256, 6 * 6, False)

	def forward(self, before, player, history):
		batch_len = before.shape[0]

		t_history = self.hist_dense_1_1(history)
		t_history = self.hist_dense_1_2(t_history)
		t_history = self.hist_dense_1_3(t_history)

		t_history = t_history.view(batch_len, 6, -1)

		t_history = self.hist_dense_2_1(t_history)
		t_history = self.hist_dense_2_2(t_history)
		t_history = self.hist_dense_2_3(t_history)
		t_history = self.hist_dense_2_4(t_history)

		t_history = t_history.view(batch_len, -1)
		t_joined = torch.cat((before, player, t_history), dim = 1)

		t_joined = self.dense_1(t_joined)
		t_joined = self.dense_2(t_joined)
		t_joined = self.dense_3(t_joined)
		t_joined = self.dense_4(t_joined)

		t_joined = t_joined.view(batch_len, 6, 6)
		pi = F.log_softmax(t_joined, dim = -1)

		return pi

class Dense(nn.Module):
	def __init__(self, in_features, out_features, apply_relu):
		super(Dense, self).__init__()

		self.layer = nn.Linear(in_features, out_features)
		self.apply_relu = apply_relu

	def forward(self, x):
		out = self.layer(x)
		if self.apply_relu: out = F.relu(out)
		return out
