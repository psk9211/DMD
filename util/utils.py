import os
import json

import torch
import math
import numpy as np
import torch.nn as nn
from models.MobileNetV2 import *
from models.MobileNetV3 import *
from models.InceptionV3 import *
from models.ShuffleNetV2 import *
from models.ResNet import *
import torch.optim as optim
from torchvision import transforms
from torch.optim.lr_scheduler import _LRScheduler
# import Augmentor
import torch.nn as nn

import pdb

np.random.seed(0)

mean_temp = (0.5,0.5,0.5)
std_temp = (0.25,0.25,0.25)
model_dict = {
    'MobileNetv2' : 1280,
    #'MobileNetv3_small' : 576,
    #'MobileNetv3_large' : 960,
    'Inception' : 2048,
    'ShuffleNet' : 1024,
    'ResNet34' : 512,
    'ResNet50' : 2048
}

def get_architecture(args):
    output_channel =0
    in_channel_1 = 1024
    in_channel_2 = 512

    if args.arch in ['MobileNetv2']:
        net = mobilenet_v2(pretrained = True).to(args.device)
        output_channel = 1280
        del net.classifier
        layer_count = 0
        for child in net.children():
            layer_count+=1
            if layer_count< int(len(list(net.children()))* args.freeze):
                for param in child.parameters():
                    param.requires_grad=False
        net.classifier = nn.Sequential(
                        nn.Linear(output_channel, in_channel_1),
                        nn.ReLU(),
                        nn.Dropout(p=0.5),
                        nn.Linear(in_channel_1, in_channel_2),
                        nn.ReLU(),
                        nn.Dropout(p=0.2),
                        nn.Linear(in_channel_2,args.num_classes),
                        )
    
    elif args.arch in ['MobileNetv3']:
        net = mobilenet_v3_large(pretrained = True).to(args.device)
        output_channel = 960

        del net.classifier
        layer_count = 0
        for child in net.children():
            layer_count+=1
            if layer_count< int(len(list(net.children()))* args.freeze):
                for param in child.parameters():
                    param.requires_grad=False
        net.classifier = nn.Sequential(
                        nn.Linear(output_channel, in_channel_1),
                        nn.ReLU(),
                        nn.Dropout(p=0.5),
                        nn.Linear(in_channel_1, in_channel_2),
                        nn.ReLU(),
                        nn.Dropout(p=0.2),
                        nn.Linear(in_channel_2,args.num_classes),
                        )
    
    elif args.arch in ['Inception']:
        net = inception_v3(pretrained = True).to(args.device)
        output_channel = 2048
        del net.fc
        layer_count = 0
        for child in net.children():
            layer_count+=1
            if layer_count< int(len(list(net.children()))* args.freeze):
                for param in child.parameters():
                    param.requires_grad=False
        net.fc = nn.Sequential(
                        nn.Linear(output_channel, in_channel_1),
                        nn.ReLU(),
                        nn.Dropout(p=0.5),
                        nn.Linear(in_channel_1, in_channel_2),
                        nn.ReLU(),
                        nn.Dropout(p=0.2),
                        nn.Linear(in_channel_2,args.num_classes),
                        )

    elif args.arch in ['ShuffleNet']:
        net = shufflenet_v2_x1_0(pretrained = True).to(args.device)
        output_channel = 1024

        del net.fc
        layer_count = 0
        for child in net.children():
            layer_count+=1
            if layer_count< int(len(list(net.children()))* args.freeze):
                for param in child.parameters():
                    param.requires_grad=False
        net.fc = nn.Sequential(
                        nn.Linear(output_channel, in_channel_1),
                        nn.ReLU(),
                        nn.Dropout(p=0.5),
                        nn.Linear(in_channel_1, in_channel_2),
                        nn.ReLU(),
                        nn.Dropout(p=0.2),
                        nn.Linear(in_channel_2,args.num_classes),
                        )
    
    elif args.arch in ['ResNet34']:
        net = resnet34(pretrained=True).to(args.device)
        output_channel = 512

        del net.fc
        layer_count = 0
        for child in net.children():
            layer_count+=1
            if layer_count< int(len(list(net.children()))* args.freeze):
                for param in child.parameters():
                    param.requires_grad=False
        net.fc = nn.Sequential(
                        nn.Linear(output_channel, in_channel_1),
                        nn.ReLU(),
                        nn.Dropout(p=0.5),
                        nn.Linear(in_channel_1, in_channel_2),
                        nn.ReLU(),
                        nn.Dropout(p=0.2),
                        nn.Linear(in_channel_2,args.num_classes),
                        )

    elif args.arch in ['ResNet50']:
        net = resnet50(pretrained=True).to(args.device)
        output_channel = 2048
        del net.fc
        layer_count = 0
        for child in net.children():
            layer_count+=1
            if layer_count< int(len(list(net.children()))* args.freeze):
                for param in child.parameters():
                    param.requires_grad=False
        net.fc = nn.Sequential(
                        nn.Linear(output_channel, in_channel_1),
                        nn.ReLU(),
                        nn.Dropout(p=0.5),
                        nn.Linear(in_channel_1, in_channel_2),
                        nn.ReLU(),
                        nn.Dropout(p=0.2),
                        nn.Linear(in_channel_2,args.num_classes),
                        )

    return net

def get_optim_scheduler(args,net):
    if args.optimizer == 'SGD':
        optimizer = optim.SGD(net.parameters(), lr=args.lr, momentum=0.9, weight_decay=args.wd)
    elif args.optimizer == 'Nesterov':
        optimizer = optim.SGD(net.parameters(), lr = args.lr, momentum=0.9, nesterov= True, weight_decay=args.wd)
    elif args.optimizer == 'Adam':
        optimizer = optim.Adam(net.parameters(), lr = args.lr)
    elif args.optimizer == 'AdamW':
        optimizer = optim.AdamW(net.parameters(), lr = args.lr)
    
    if args.scheduler == 'MultiStepLR':
        scheduler = optim.lr_scheduler.MultiStepLR(optimizer, [15,30],gamma=0.1)
    elif args.scheduler == 'CosineAnnealing':
        scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer,T_max=args.epoch)
    elif args.scheduler == 'CosineWarmup':
        torch_lr_scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer,T_max=args.epoch)
        scheduler = CosineAnnealingWarmupRestarts(optimizer, first_cycle_steps = args.epoch, cycle_mult=1.0, max_lr = args.lr, min_lr = 0.001, warmup_steps = args.warmup_duration, gamma = 1.0)
    return optimizer, scheduler

def get_transform(mode='train'):
    normalize = transforms.Normalize(mean = mean_temp, std = std_temp)
    if mode == 'train':
        TF = transforms.Compose([
            transforms.Resize((640,360)),
            CropRandomPosition(),
            transforms.Resize((224,224)),
            transforms.ToTensor(),
            normalize,
        ])
    elif mode == 'test':
        TF = transforms.Compose([
        transforms.Resize((224,224)),
        transforms.ToTensor(),
        normalize,
        ])
    
    return TF

class CropRandomPosition(object):
    position_idx = [1,0.875,0.75,0.65625]
    def __init__(self):
        pass

    def __call__(self,img):
        w, h = img.size
        new_h = int(self.position_idx[np.random.randint(0,4)] * h)
        new_w = int(self.position_idx[np.random.randint(0,4)] * w)
        random_starting_point = [(0,0),(w-new_w,0),(0,h-new_h),(w-new_w,h-new_h),(int((w-new_w)/2)-1,int((h-new_h)/2)-1)]
        starting_point_x, starting_point_y = random_starting_point[np.random.randint(0,5)]
        new_img = img.crop((starting_point_x,starting_point_y,starting_point_x+new_w,starting_point_y+new_h))
        return new_img

class Rotation(object):
    def __init__(self, max_range = 4):
        pass

    def __call__(self,img):
        image_dimension = img.size().__len__()
        aug_index = np.random.randint(1,4)
        img = torch.rot90(img,aug_index, (image_dimension-2,image_dimension-1))
        return img

class CutPerm(object):
    def __init__(self, max_range = 4):
        super(CutPerm, self).__init__()
        self.max_range = max_range

    def __call__(self, img):
        _, H, W = img.size()
        aug_index = np.random.randint(1,4)
        img = self._cutperm(img, aug_index)
        return img

    def _cutperm(self, inputs, aug_index):

        _, H, W = inputs.size()
        h_mid = int(H / 2)
        w_mid = int(W / 2)

        jigsaw_h = aug_index // 2
        jigsaw_v = aug_index % 2

        if jigsaw_h == 1:
            inputs = torch.cat((inputs[:, h_mid:, :], inputs[:, 0:h_mid, :]), dim=1)
        if jigsaw_v == 1:
            inputs = torch.cat((inputs[:, :, w_mid:], inputs[:, :, 0:w_mid]), dim=2)

        return inputs

class LabelSmoothingLoss(nn.Module):
    def __init__(self, classes, smoothing=0.0, dim=-1):
        super(LabelSmoothingLoss, self).__init__()
        self.confidence = 1.0 - smoothing
        self.smoothing = smoothing
        self.cls = classes
        self.dim = dim

    def forward(self, pred, target):
        pred = pred.log_softmax(dim=self.dim)
        with torch.no_grad():
            # true_dist = pred.data.clone()
            true_dist = torch.zeros_like(pred)
            true_dist.fill_(self.smoothing / (self.cls - 1))
            true_dist.scatter_(1, target.data.unsqueeze(1), self.confidence)
        return torch.mean(torch.sum(-true_dist * pred, dim=self.dim))

def mixup_data(args, x, y, alpha=1.0):
    '''Returns mixed inputs, pairs of targets, and lambda'''
    if alpha > 0:
        lam = np.random.beta(alpha, alpha)
    else:
        lam = 1

    batch_size = x.size()[0]

    index = torch.randperm(batch_size).to(args.device)

    mixed_x = lam * x + (1 - lam) * x[index, :]
    y_a, y_b = y, y[index]
    return mixed_x, y_a, y_b, lam


def mixup_criterion(criterion, pred, y_a, y_b, lam):
    return lam * criterion(pred, y_a) + (1 - lam) * criterion(pred, y_b)

class CosineAnnealingWarmupRestarts(_LRScheduler):
    """
        optimizer (Optimizer): Wrapped optimizer.
        first_cycle_steps (int): First cycle step size.
        cycle_mult(float): Cycle steps magnification. Default: -1.
        max_lr(float): First cycle's max learning rate. Default: 0.1.
        min_lr(float): Min learning rate. Default: 0.001.
        warmup_steps(int): Linear warmup step size. Default: 0.
        gamma(float): Decrease rate of max learning rate by cycle. Default: 1.
        last_epoch (int): The index of last epoch. Default: -1.
    """
    
    def __init__(self,
                 optimizer : torch.optim.Optimizer,
                 first_cycle_steps : int,
                 cycle_mult : float = 1.,
                 max_lr : float = 0.1,
                 min_lr : float = 0.001,
                 warmup_steps : int = 0,
                 gamma : float = 1.,
                 last_epoch : int = -1
        ):
        assert warmup_steps < first_cycle_steps
        
        self.first_cycle_steps = first_cycle_steps # first cycle step size
        self.cycle_mult = cycle_mult # cycle steps magnification
        self.base_max_lr = max_lr # first max learning rate
        self.max_lr = max_lr # max learning rate in the current cycle
        self.min_lr = min_lr # min learning rate
        self.warmup_steps = warmup_steps # warmup step size
        self.gamma = gamma # decrease rate of max learning rate by cycle
        
        self.cur_cycle_steps = first_cycle_steps # first cycle step size
        self.cycle = 0 # cycle count
        self.step_in_cycle = last_epoch # step size of the current cycle
        
        super(CosineAnnealingWarmupRestarts, self).__init__(optimizer, last_epoch)
        
        # set learning rate min_lr
        self.init_lr()
    
    def init_lr(self):
        self.base_lrs = []
        for param_group in self.optimizer.param_groups:
            param_group['lr'] = self.min_lr
            self.base_lrs.append(self.min_lr)
    
    def get_lr(self):
        if self.step_in_cycle == -1:
            return self.base_lrs
        elif self.step_in_cycle < self.warmup_steps:
            return [(self.max_lr - base_lr)*self.step_in_cycle / self.warmup_steps + base_lr for base_lr in self.base_lrs]
        else:
            return [base_lr + (self.max_lr - base_lr) \
                    * (1 + math.cos(math.pi * (self.step_in_cycle-self.warmup_steps) \
                                    / (self.cur_cycle_steps - self.warmup_steps))) / 2
                    for base_lr in self.base_lrs]

    def step(self, epoch=None):
        if epoch is None:
            epoch = self.last_epoch + 1
            self.step_in_cycle = self.step_in_cycle + 1
            if self.step_in_cycle >= self.cur_cycle_steps:
                self.cycle += 1
                self.step_in_cycle = self.step_in_cycle - self.cur_cycle_steps
                self.cur_cycle_steps = int((self.cur_cycle_steps - self.warmup_steps) * self.cycle_mult) + self.warmup_steps
        else:
            if epoch >= self.first_cycle_steps:
                if self.cycle_mult == 1.:
                    self.step_in_cycle = epoch % self.first_cycle_steps
                    self.cycle = epoch // self.first_cycle_steps
                else:
                    n = int(math.log((epoch / self.first_cycle_steps * (self.cycle_mult - 1) + 1), self.cycle_mult))
                    self.cycle = n
                    self.step_in_cycle = epoch - int(self.first_cycle_steps * (self.cycle_mult ** n - 1) / (self.cycle_mult - 1))
                    self.cur_cycle_steps = self.first_cycle_steps * self.cycle_mult ** (n)
            else:
                self.cur_cycle_steps = self.first_cycle_steps
                self.step_in_cycle = epoch
                
        self.max_lr = self.base_max_lr * (self.gamma**self.cycle)
        self.last_epoch = math.floor(epoch)
        for param_group, lr in zip(self.optimizer.param_groups, self.get_lr()):
            param_group['lr'] = lr


# TODO : Get exact DMD_mean and DMD_std
# Need to verify
def get_DMD_info(data_loader, force):
    # Use train data if possible

    if os.path.isfile("./train_data_mean_std.json") and not force:
        with open("./train_data_mean_std.json", 'r') as jf:
            mean, std = json.load(jf)

    else:
        mean = 0.0
        var = 0.0
        for images, _ in data_loader:
            batch_samples = images.size(0) 
            images = images.view(batch_samples, images.size(1), -1)
            mean += images.mean(2).sum(0)
        mean = mean / len(data_loader.dataset)

        for images, _ in data_loader:
            batch_samples = images.size(0) 
            images = images.view(batch_samples, images.size(1), -1)
            var += ((images - mean.unsqueeze(1))**2).sum([0,2])
        pdb.set_trace()
        std = torch.sqrt(var / (len(data_loader.dataset)*1280*720)) # resolution of DMD set is 1280*720

        print(f'Mean: {mean}, std: {std}')

        if isinstance(mean, torch.Tensor):
            mean = mean.tolist()
        if isinstance(std, torch.Tensor):
            std = std.tolist()

        with open("./train_data_mean_std.json", 'w') as jf:
            json.dump([mean, std], jf)

    return mean, std