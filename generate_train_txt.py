#!/usr/bin/python3
#coding=utf-8

import os
import sys
sys.path.insert(0, '../')
sys.dont_write_bytecode = True

import cv2
import numpy as np
import matplotlib.pyplot as plt
plt.ion()

import torch
import dataset
from torch.utils.data import DataLoader
#from net import LDF

# input_path = '/home/wtz/data/COD/COD10K_train'
# output_path = '/home/wtz/data/COD/COD10K_train'

# input_path = '/home/wtz/data/COD/CAMO_TestingDataset/'
# output_path = '/home/wtz/data/COD/CAMO_TestingDataset/'

input_path = '/home/wtz/data/COD/CHAMELEON_TestingDataset/'
output_path = '/home/wtz/data/COD/CHAMELEON_TestingDataset/'

# input_path = '/home/wtz/data/COD/COD10K_TestingDataset/'
# output_path = '/home/wtz/data/COD/COD10K_TestingDataset/'

def generate_train_txt(path):
    print(path)
    names = []
    for name in os.listdir(path + '/Image'):
        name = os.path.splitext(name)[0]
        names.append(name)

    file = open(output_path + '/train.txt', 'w+')
    for i in names:
        file.write(i + '\n')
    file.close()

if __name__=='__main__':
    t = generate_train_txt( input_path)
