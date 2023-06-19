import os
import argparse
import cv2
import numpy as np
import os.path as osp
import torch
import dataset
from torch.utils.data import DataLoader
from MENet import MENet
from evaluator import Eval_thread
from dataloader import EvalDataset

import glob
import time

# --------- 1. get pth files list ---------
pth_dir = 'out/'
out_MAE = pth_dir + 'MAE_CAMO.txt'
out_dir = 'out/map/'

n = 0
MAE_list = []
pth_done = []

MAE_best = 100
pth_best = ''

class Map_out(object):
    def __init__(self, Dataset, Network, Path, Snapshot):
        ## dataset
        self.cfg    = Dataset.Config(datapath=Path, snapshot=Snapshot, mode='test')
        self.pth = Snapshot.split('/')[-1]
        self.data   = Dataset.Data(self.cfg)
        self.loader = DataLoader(self.data, batch_size=1, shuffle=False, num_workers=0)
        ## network
        self.net    = Network(self.cfg)
        self.net.train(False)
        self.net.cuda()

    def save(self):
        with torch.no_grad():
            n = 0
            for image, (H, W), name in self.loader:
                n += 1
                print('\rimages:{0}'.format( n ), end='')
                image, shape  = image.cuda().float(), (H, W)
                outb1, out1, outb2, out2, outb3, out3, outb4, out4 = self.net(image, shape)
                out = out4
                pred = torch.sigmoid(out[0,0]).cpu().numpy()*255
                #head = '../eval/maps/LDF_coarse/'+ self.cfg.datapath.split('/')[-1]
                pth_name = self.pth.split('.pth')[0]
                head = out_dir + method + '-' + pth_name + '/' + self.cfg.datapath.split('/')[-1]
                if not os.path.exists(head):
                    os.makedirs(head)
                cv2.imwrite(head+'/'+name[0]+'.png', np.round(pred))
                #print(name[0]+'.png')



def Eval(cfg):
    output_dir = cfg.save_dir
    gt_dir = cfg.root_dir_gt
    pred_dir = cfg.root_dir_pred
    if cfg.methods is None:
        method_names = os.listdir(pred_dir)
    else:
        method_names = cfg.methods.split('+')
    if cfg.datasets is None:
        dataset_names = os.listdir(gt_dir)
    else:
        dataset_names = cfg.datasets.split('+')

    threads = []
    for dataset in dataset_names:
        for method in method_names:
            loader = EvalDataset(osp.join(pred_dir, method, dataset), osp.join(gt_dir, dataset))
            thread = Eval_thread(loader, method, dataset, output_dir, cfg.cuda)
            threads.append(thread)
    for thread in threads:
        print(thread.run())


method = 'MENet'

pth_names = glob.glob(pth_dir + 'model*')
pth_names.sort( reverse = True )
print('\rpth_files:{0}'.format(len(pth_names)))

for pth in pth_names:
    if pth in pth_done:
        continue
    n = n + 1
    print(n,pth)

    for path in ['DUTS-TE', 'ECSSD', 'PASCAL-S', 'HKU-IS', 'DUT-OMRON', 'SOD']:
        path = '../../data/' + path
        t = Map_out(dataset, MENet, path, pth)
        t.save()

    parser = argparse.ArgumentParser()
    parser.add_argument('--methods', type=str, default=None)
    parser.add_argument('--datasets', type=str, default=None)
    parser.add_argument('--root_dir_gt', type=str, default='../../data/gt')
    parser.add_argument('--root_dir_gred', type=str, default='./')
    parser.add_argument('--save_dir', type=str, default=None)
    parser.add_argument('--cuda', type=bool, default=True)
    config = parser.parse_args()

    #config.root_dir_gt = '../../result_sod/gt'
    model_name = pth.split('/')[-1]
    model_name = model_name.split('.pth')[0]
    config.root_dir_pred = 'out/map/'
    config.save_dir = 'out/'

    config.datasets = 'DUT-OMRON+DUTS-TE+ECSSD+HKU-IS+PASCAL-S+SOD'
    config.methods = method + '-' + model_name
    Eval(config)



    if n>10:
        break

os.popen('python plot_excel.py')
