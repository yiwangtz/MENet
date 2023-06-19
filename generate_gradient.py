#coding=utf-8
import os
import cv2
import numpy as np
import matplotlib.pyplot as plt

def generate_gradient(path):
    print(path)
    for name in os.listdir(path + '/GT'):
        mask = cv2.imread(path + '/GT/' + name, 0)

        h, w = mask.shape[:2]
        x = cv2.Sobel(mask, cv2.CV_16S, 1, 0, ksize=1)
        y = cv2.Sobel(mask, cv2.CV_16S, 0, 1, ksize=1)

        absX = cv2.convertScaleAbs(x)  # 在经过处理后，需要用convertScaleAbs()函数将其转回原来的uint8形式，否则将无法显示图像，而只是一副灰色的窗口。
        absY = cv2.convertScaleAbs(y)

        dst = cv2.addWeighted(absX, 0.5, absY, 0.5, 0)  # 由于Sobel算子是在两个方向计算的，最后还需要用cv2.addWeighted(...)函数将其组合起来
        print(np.max(dst))


        # tmp = body[np.where(body > 0)]
        # if len(tmp) != 0:
        #     body[np.where(body > 0)] = np.floor(tmp / np.max(tmp) * 255)

        if not os.path.exists(path+'/gradient/'):
            os.makedirs(path+'/gradient/')
        cv2.imwrite(path + '/gradient/' + name, dst)

        print(name)

def split_map(datapath):
    print(datapath)
    for name in os.listdir(datapath+'/mask'):
        mask = cv2.imread(datapath+'/mask/'+name,0)
        body = cv2.blur(mask, ksize=(5,5))
        body = cv2.distanceTransform(body, distanceType=cv2.DIST_L2, maskSize=5)
        body = body**0.5

        tmp  = body[np.where(body>0)]
        if len(tmp)!=0:
            body[np.where(body>0)] = np.floor(tmp/np.max(tmp)*255)

        # if not os.path.exists(datapath+'/body-origin/'):
        #     os.makedirs(datapath+'/body-origin/')
        cv2.imwrite(datapath+'/body-origin/'+name, body)

        # if not os.path.exists(datapath+'/detail-origin/'):
        #     os.makedirs(datapath+'/detail-origin/')
        detail = mask-body
        cv2.imwrite(datapath+'/detail-origin/'+name, mask-body)

        print(name)


if __name__=='__main__':
    generate_gradient('/home/wtz/data/COD/COD10K_train')

