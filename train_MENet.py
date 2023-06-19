#!/usr/bin/python3
#coding=utf-8

import sys
import datetime

sys.path.insert(0, '../')
sys.dont_write_bytecode = True

import dataset
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from apex import amp
from MENet  import MENet


import my_config.my_config as my_config
import numpy as np


def structure_loss(pred, mask):
    weit = 1 + 5*torch.abs(F.avg_pool2d(mask, kernel_size=31, stride=1, padding=15) - mask)
    wbce = F.binary_cross_entropy_with_logits(pred, mask, reduce='none')
    wbce = (weit*wbce).sum(dim=(2, 3)) / weit.sum(dim=(2, 3))

    pred = torch.sigmoid(pred)
    inter = ((pred * mask)*weit).sum(dim=(2, 3))
    union = ((pred + mask)*weit).sum(dim=(2, 3))
    wiou = 1 - (inter + 1)/(union - inter+1)
    return (wbce + wiou).mean()

def iou_loss(pred, mask):
    pred  = torch.sigmoid(pred)
    inter = (pred*mask).sum(dim=(2,3))
    union = (pred+mask).sum(dim=(2,3))
    iou  = 1-(inter+1)/(union-inter+1)
    return iou.mean()


def floss(prediction, target, beta=0.3, log_like=False):
    prediction = torch.sigmoid(prediction)
    EPS = 1e-10
    N = N = prediction.size(0)
    TP = (prediction * target).view(N, -1).sum(dim=1)
    H = beta * target.view(N, -1).sum(dim=1) + prediction.view(N, -1).sum(dim=1)
    fmeasure = (1 + beta) * TP / (H + EPS)
    if log_like:
        floss = -torch.log(fmeasure)
    else:
        floss  = (1 - fmeasure)
    floss = floss.mean()
    return floss

def eval_pr(y_pred, y, num):
    prec, recall = torch.zeros(num).cuda(), torch.zeros(num).cuda()
    # thlist = torch.linspace(0, 1 - 1e-10, num).cuda()
    thlist = torch.linspace(0, 1, num).cuda()

    for i in range(num-1):
        y_temp = torch.logical_and(y_pred>= thlist[i], y_pred < thlist[i+1]).float()
        #y_temp = (y_pred >= thlist[i] ).float()
        tp = (y_temp * y).sum()
        prec[i], recall[i] = tp / (y_temp.sum() + 1e-20), tp / (y.sum() + 1e-20)
    return prec, recall

def pr_loss(pred, gt):
    pred = torch.sigmoid(pred)
    prec, recall = eval_pr(pred, gt, 255)
    prec_loss = 1.0 - prec
    recall_loss = 1.0 - recall
    prec_loss = prec_loss.mean()
    recall_loss = recall_loss.mean()

    loss = prec_loss + recall_loss

    return  loss

def eval_pr_original(y_pred, y, num):
    prec, recall = torch.zeros(num).cuda(), torch.zeros(num).cuda()
    # thlist = torch.linspace(0, 1 - 1e-10, num).cuda()
    thlist = torch.linspace(0, 1, num).cuda()

    for i in range(num):
        y_temp = (y_pred >= thlist[i]).float()
        tp = (y_temp * y).sum()
        prec[i], recall[i] = tp / (y_temp.sum() + 1e-20), tp / (y.sum() + 1e-20)
    return prec, recall

def pr_loss1(pred, gt):
    beta2 = 0.3
    avg_f, avg_p, avg_r, img_num = 0.0, 0.0, 0.0, 0.0
    pred = torch.sigmoid(pred)
    for i in range(pred.shape[0]):
        prec, recall = eval_pr(pred[i,0,:], gt[i,0,:], 255)
        f_score = (1 + beta2) * prec * recall / (beta2 * prec + recall)
        f_score[f_score != f_score] = 0  # for Nan
        avg_f += f_score
        avg_p += prec
        avg_r += recall
        img_num += 1.0
    avg_p = avg_p / img_num
    avg_r = avg_r / img_num
    Fm = (1 + beta2) * avg_p * avg_r / (beta2 * avg_p + avg_r)

    p = 1 - avg_p
    r = 1 - avg_r
    Fm = 1 - Fm

    loss = p.mean() + r.mean() + Fm.mean()

    return  loss

def object(pred, gt) -> float:
    """
    Calculate the object score.
    """
    fg = pred * gt
    bg = (1 - pred) * (1 - gt)
    u = torch.mean(gt)
    object_score = u * s_object(fg, gt) + (1 - u) * s_object(bg, 1 - gt)
    return object_score

_EPS = np.spacing(1)
def s_object(pred, gt) -> float:
    x = torch.mean(pred[gt == 1])
    sigma_x = torch.std(pred[gt == 1], unbiased=True)
    score = 2 * x / (torch.pow(x, 2) + 1 + sigma_x + _EPS)
    return score

def region( pred, gt) -> float:
    """
    Calculate the region score.
    """
    x, y = centroid(gt)
    part_info = divide_with_xy(pred, gt, x, y)
    w1, w2, w3, w4 = part_info["weight"]
    # assert np.isclose(w1 + w2 + w3 + w4, 1), (w1 + w2 + w3 + w4, pred.mean(), gt.mean())

    pred1, pred2, pred3, pred4 = part_info["pred"]
    gt1, gt2, gt3, gt4 = part_info["gt"]
    score1 = ssim(pred1, gt1)
    score2 = ssim(pred2, gt2)
    score3 = ssim(pred3, gt3)
    score4 = ssim(pred4, gt4)

    return w1 * score1 + w2 * score2 + w3 * score3 + w4 * score4

def centroid(matrix) -> tuple:
    """
    To ensure consistency with the matlab code, one is added to the centroid coordinate,
    so there is no need to use the redundant addition operation when dividing the region later,
    because the sequence generated by ``1:X`` in matlab will contain ``X``.

    :param matrix: a data array
    :return: the centroid coordinate
    """
    h, w = matrix.shape
    if matrix.sum() == 0:
        x = torch.round(w / 2)
        y = torch.round(h / 2)
    else:
        area_object = torch.sum(matrix)
        row_ids = torch.arange(h).cuda()
        col_ids = torch.arange(w).cuda()
        x = torch.round(torch.sum(torch.sum(matrix, axis=0) * col_ids) / area_object)
        y = torch.round(torch.sum(torch.sum(matrix, axis=1) * row_ids) / area_object)
    return int(x) + 1, int(y) + 1

def divide_with_xy(pred, gt, x: int, y: int) -> dict:
    """
    Use (x,y) to divide the ``pred`` and the ``gt`` into four submatrices, respectively.
    """
    h, w = gt.shape
    area = h * w

    gt_LT = gt[0:y, 0:x]
    gt_RT = gt[0:y, x:w]
    gt_LB = gt[y:h, 0:x]
    gt_RB = gt[y:h, x:w]

    pred_LT = pred[0:y, 0:x]
    pred_RT = pred[0:y, x:w]
    pred_LB = pred[y:h, 0:x]
    pred_RB = pred[y:h, x:w]

    w1 = x * y / area
    w2 = y * (w - x) / area
    w3 = (h - y) * x / area
    w4 = 1 - w1 - w2 - w3

    return dict(
        gt=(gt_LT, gt_RT, gt_LB, gt_RB),
        pred=(pred_LT, pred_RT, pred_LB, pred_RB),
        weight=(w1, w2, w3, w4),
    )

def ssim(pred, gt) -> float:
    """
    Calculate the ssim score.
    """
    h, w = pred.shape
    N = h * w

    x = torch.mean(pred)
    y = torch.mean(gt)

    sigma_x = torch.sum((pred - x) ** 2) / (N - 1)
    sigma_y = torch.sum((gt - y) ** 2) / (N - 1)
    sigma_xy = torch.sum((pred - x) * (gt - y)) / (N - 1)

    alpha = 4 * x * y * sigma_xy
    beta = (x ** 2 + y ** 2) * (sigma_x + sigma_y)

    if alpha != 0:
        score = alpha / (beta + _EPS)
    elif alpha == 0 and beta == 0:
        score = 1
    else:
        score = 0
    return score


def Sm(pred, gt):
    """
    Calculate the S-measure.

    :return: s-measure
    """
    alpha = 0.5
    y = torch.mean(gt)
    if y == 0:
        sm = 1 - torch.mean(pred)
    elif y == 1:
        sm = torch.mean(pred)
    else:
        sm = alpha * object(pred, gt) + (1 - alpha) * region(pred, gt)
        sm = max(0, sm)
    return sm


def Sm_loss1(pred, mask):
    sm = 0.0
    pred = torch.sigmoid(pred)
    for i in range(pred.shape[0]):
        sm += Sm( pred=pred[i,0,:], gt=mask[i,0,:])
    sm = sm / pred.shape[0]
    sm_loss = 1.0 - sm
    return sm_loss


def _object(pred, gt):
    temp = pred[gt == 1]
    x = temp.mean()
    sigma_x = temp.std()
    score = 2.0 * x / (x * x + 1.0 + sigma_x + 1e-20)

    return score

def _S_object(pred, gt):
    fg = torch.where(gt == 0, torch.zeros_like(pred), pred)
    bg = torch.where(gt == 1, torch.zeros_like(pred), 1 - pred)
    o_fg = _object(fg, gt)
    o_bg = _object(bg, 1 - gt)
    u = gt.mean()
    Q = u * o_fg + (1 - u) * o_bg
    return Q

def _S_region(pred, gt):
    X, Y = _centroid(gt)
    gt1, gt2, gt3, gt4, w1, w2, w3, w4 = _divideGT(gt, X, Y)
    p1, p2, p3, p4 = _dividePrediction(pred, X, Y)
    Q1 = _ssim(p1, gt1)
    Q2 = _ssim(p2, gt2)
    Q3 = _ssim(p3, gt3)
    Q4 = _ssim(p4, gt4)
    Q = w1 * Q1 + w2 * Q2 + w3 * Q3 + w4 * Q4
    return Q

def _centroid(gt):
    rows, cols = gt.size()[-2:]
    gt = gt.view(rows, cols)
    if gt.sum() == 0:
        if True:
            X = torch.eye(1).cuda() * round(cols / 2)
            Y = torch.eye(1).cuda() * round(rows / 2)
        else:
            X = torch.eye(1) * round(cols / 2)
            Y = torch.eye(1) * round(rows / 2)
    else:
        total = gt.sum()
        if True:
            i = torch.from_numpy(np.arange(0, cols)).cuda().float()
            j = torch.from_numpy(np.arange(0, rows)).cuda().float()
        else:
            i = torch.from_numpy(np.arange(0, cols)).float()
            j = torch.from_numpy(np.arange(0, rows)).float()
        X = torch.round((gt.sum(dim=0) * i).sum() / total + 1e-20)
        Y = torch.round((gt.sum(dim=1) * j).sum() / total + 1e-20)
    return X.long(), Y.long()

def _divideGT(gt, X, Y):
    h, w = gt.size()[-2:]
    area = h * w
    gt = gt.view(h, w)
    LT = gt[:Y, :X]
    RT = gt[:Y, X:w]
    LB = gt[Y:h, :X]
    RB = gt[Y:h, X:w]
    X = X.float()
    Y = Y.float()
    w1 = X * Y / area
    w2 = (w - X) * Y / area
    w3 = X * (h - Y) / area
    w4 = 1 - w1 - w2 - w3
    return LT, RT, LB, RB, w1, w2, w3, w4

def _dividePrediction(pred, X, Y):
    h, w = pred.size()[-2:]
    pred = pred.view(h, w)
    LT = pred[:Y, :X]
    RT = pred[:Y, X:w]
    LB = pred[Y:h, :X]
    RB = pred[Y:h, X:w]
    return LT, RT, LB, RB

def _ssim(pred, gt):
    gt = gt.float()
    h, w = pred.size()[-2:]
    N = h * w
    x = pred.mean()
    y = gt.mean()
    sigma_x2 = ((pred - x) * (pred - x)).sum() / (N - 1 + 1e-20)
    sigma_y2 = ((gt - y) * (gt - y)).sum() / (N - 1 + 1e-20)
    sigma_xy = ((pred - x) * (gt - y)).sum() / (N - 1 + 1e-20)

    aplha = 4 * x * y * sigma_xy
    beta = (x * x + y * y) * (sigma_x2 + sigma_y2)

    if aplha != 0:
        Q = aplha / (beta + 1e-20)
    elif aplha == 0 and beta == 0:
        Q = 1.0
    else:
        Q = 0
    return Q


def Eval_Smeasure(pred, gt):
    alpha, avg_q, img_num = 0.5, 0.0, 0.0
    y = gt.mean()
    if y == 0:
        x = pred.mean()
        Q = 1.0 - x
    elif y == 1:
        x = pred.mean()
        Q = x
    else:
        gt[gt >= 0.5] = 1
        gt[gt < 0.5] = 0
        Q = alpha * _S_object(pred, gt) + (1 - alpha) * _S_region(pred, gt)
        if Q.item() < 0:
            Q = torch.FloatTensor([0.0])
    #q = Q.item()
    return 1.0 - Q

def Sm_loss(pred, mask):
    sm = 0.0
    pred = torch.sigmoid(pred)
    for i in range(pred.shape[0]):
        sm += Eval_Smeasure( pred=pred[i,0,:], gt=mask[i,0,:])
    sm = sm / pred.shape[0]
    sm_loss = 1.0 - sm
    return sm_loss


def train(Dataset, Network):
    ## dataset
    cfg    = Dataset.Config(datapath='../../data/DUTS', savepath='./out', mode='train', batch=my_config.batch, lr=0.05,
                            momen=0.9, decay=5e-4, epoch=99)
    data   = Dataset.Data(cfg)
    loader = DataLoader(data, collate_fn=data.collate, batch_size=cfg.batch,
                        shuffle=True, pin_memory=True, num_workers=0)
    ## network
    net    = Network(cfg)
    net.train(True)
    net.cuda()
    ## parameter
    base, head = [], []
    for name, param in net.named_parameters():
        if 'bkbone.conv1' in name or 'bkbone.bn1' in name:
            print(name)
        elif 'bkbone' in name:
            base.append(param)
        else:
            head.append(param)
    optimizer = torch.optim.SGD([{'params':base}, {'params':head}], lr=cfg.lr, momentum=cfg.momen,
                                weight_decay=cfg.decay, nesterov=True)
    net, optimizer = amp.initialize(net, optimizer, opt_level='O2')
    sw = SummaryWriter(cfg.savepath)
    global_step = 0

    for epoch in range(cfg.epoch):
        optimizer.param_groups[0]['lr'] = (1-abs((epoch+1)/(cfg.epoch+1)*2-1))*cfg.lr*0.1
        optimizer.param_groups[1]['lr'] = (1-abs((epoch+1)/(cfg.epoch+1)*2-1))*cfg.lr

        for step, (image, mask, gradient) in enumerate(loader):

            image, mask, gradient = image.cuda(), mask.cuda(), gradient.cuda()
            outg1, out1, outg2, out2, outg3, out3, outg4, out4 = net(image)

            lossg1 = F.binary_cross_entropy_with_logits(outg1, gradient) + pr_loss(outg1, gradient)
            lossg2 = F.binary_cross_entropy_with_logits(outg2, gradient) + pr_loss(outg2, gradient)
            lossg3 = F.binary_cross_entropy_with_logits(outg3, gradient) + pr_loss(outg3, gradient)
            lossg4 = F.binary_cross_entropy_with_logits(outg4, gradient) + pr_loss(outg4, gradient)

            loss1 = F.binary_cross_entropy_with_logits(out1, mask) + iou_loss(out1, mask) + structure_loss(out1, mask) + pr_loss(out1, mask) + Sm_loss1(out1,mask)
            loss2 = F.binary_cross_entropy_with_logits(out2, mask) + iou_loss(out2, mask) + structure_loss(out2, mask) + pr_loss(out2, mask) #+ Sm_loss1(out2,mask)
            loss3 = F.binary_cross_entropy_with_logits(out3, mask) + iou_loss(out3, mask) + structure_loss(out3, mask) + pr_loss(out3, mask) #+ Sm_loss1(out3,mask)
            loss4 = F.binary_cross_entropy_with_logits(out4, mask) + iou_loss(out4, mask) + structure_loss(out4, mask) + pr_loss(out4, mask)  # + Sm_loss1(out4,mask)

            loss = (lossg1 + lossg2 + lossg3 + lossg4 + loss1 + loss2 + loss3 + loss4) / 2

            optimizer.zero_grad()
            with amp.scale_loss(loss, optimizer) as scale_loss:
                scale_loss.backward()

            optimizer.step()

            ## log
            global_step += 1
            sw.add_scalar('lr'   , optimizer.param_groups[0]['lr'], global_step=global_step)
            sw.add_scalars('loss', { 'loss': loss.item(),
                                     'loss1': loss1.item()},
                           global_step=global_step)

            if step%10 == 0:
                print('%s | step:%d/%d/%d | lr=%.6f | loss=%.6f | loss1=%.6f '
                      % (datetime.datetime.now(), global_step, epoch + 1, cfg.epoch, optimizer.param_groups[0]['lr'],
                         loss.item(), loss1.item()))

        if epoch > 0:
            torch.save(net.state_dict(), cfg.savepath+'/model-'+str(epoch+1))


if __name__=='__main__':
    train(dataset, MENet)