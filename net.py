from config import *
from util import *
from model import *
import torch.nn as nn
import torch
import numpy as np

class Net(object):
    def __init__(self, model_path = None, device = None):
        if device is None: device = 'cuda' if torch.cuda.is_available() else 'cpu'        
        
        self.device = torch.device(device)
        self.model = Model().to(device = self.device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr = 1e-4)

        if model_path is None:
            self.model_path = 'scratch'
        else:
            self.model_path = model_path
            self.load(model_path)

        self.model = nn.DataParallel(self.model)
        print('* loaded neural net from {} on {}'.format(self.model_path, device))

    def eval(self, states, has_true = True):
        self.model.eval()

        input_batches = self._split_batches_(states)
        batch_pi = []

        for batch in input_batches:
            if has_true:
                before, player, history, _ = self._parse_data_(batch, has_true)
            else:
                before, player, history = self._parse_data_(batch, has_true)

            pi = self.model(before, player, history)
            pi = torch.exp(pi)

            batch_pi.append(pi.data.cpu().numpy())

        return np.vstack(batch_pi)

    def train(self, data):
        self.model.train()        

        input_batches = self._split_batches_(data)
        sum_loss = 0
        
        for batch in input_batches:
            self.optimizer.zero_grad()
            
            before, player, history, true_pi = self._parse_data_(batch, True)
            pi = self.model(before, player, history)

            loss = -torch.mean(torch.sum(pi * true_pi, (2, 1)))
            sum_loss += loss.data.cpu().numpy()

            loss.backward()

            self.optimizer.step()

        avg_loss = sum_loss / len(input_batches)
        return avg_loss

    def save(self, model_path, only_model = False):
        save_dict = {
            'model': self.model.module.state_dict()
        }
        save_dict['optimizer'] = None if only_model else self.optimizer.state_dict()
        torch.save(save_dict, model_path)

    def load(self, model_path):
        ckpt = torch.load(model_path, map_location = self.device)
        self.model.load_state_dict(ckpt['model'])

        state_dict = ckpt['optimizer']
        if state_dict is not None: self.optimizer.load_state_dict(state_dict)

    def get_param_count(self):
        return sum(param.numel() for param in self.model.parameters())

    def get_model_path(self):
        return self.model_path

    def set_lr(self, lr):
        for param_group in self.optimizer.param_groups:
            param_group['lr'] = lr

    def _split_batches_(self, data):
        i, batches = 0, []

        if len(data) > batch_size:
            while i < len(data):
                batches.append(data[i:i + batch_size])
                i += batch_size
        else:
            batches.append(data)

        return batches

    def _parse_data_(self, data, has_true):
        if has_true:
            before, player, history, true_pi = [], [], [], []

            for b, p, h, pi in data:
                before.append(b)
                player.append(p)
                history.append(h)
                true_pi.append(pi)

            before = torch.from_numpy(np.stack(before)).float().to(self.device)
            player = torch.from_numpy(np.stack(player)).float().to(self.device)
            history = torch.from_numpy(np.stack(history)).float().to(self.device)
            true_pi = torch.from_numpy(np.stack(true_pi)).float().to(self.device)

            return before, player, history, true_pi
        else:
            before, player, history = [], [], []

            for b, p, h in data:
                before.append(b)
                player.append(p)
                history.append(h)

            before = torch.from_numpy(np.stack(before)).float().to(self.device)
            player = torch.from_numpy(np.stack(player)).float().to(self.device)
            history = torch.from_numpy(np.stack(history)).float().to(self.device)

            return before, player, history

if __name__ == '__main__':
    mkdir('./logs')

    net = Net()
    net.save('./logs/best.ckpt', True)

    params = net.get_param_count()
    print()
    
    print('params : {}'.format(params))
    print('size : {:.2f}mb'.format(params * 4 / 1024 / 1024))
