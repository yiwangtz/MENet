import xlwt
import os
import torch
import json
import numpy as np
import glob
import argparse

def set_style(name,height,bold=False,color=0):
	style = xlwt.XFStyle()
	font = xlwt.Font()
	font.name = name
	font.bold = bold
	font.colour_index = color
	font.height = height
	style.font = font
	return style


parser = argparse.ArgumentParser()
parser.add_argument('--out', type=str, default='out')
config = parser.parse_args()

out = config.out


res_dir = out + '/detail/'
out_dir = out + '/out'
os.makedirs(out_dir, exist_ok=True)

datasets = 'DUT-OMRON+DUTS-TE+ECSSD+HKU-IS+PASCAL-S+SOD'


method_path = out + '/map'
method_names = glob.glob(method_path+'/*')
method_names.sort( reverse = True )

metas = []
for method in method_names:
    method = method.split(method_path+'/')[-1]
    meta = {'name': method, 'network': ''}
    metas.append(meta)

# metas = []
# meta = {'name':'U2Net','network':'RSU'}                         #1
# metas.append(meta)
# meta = {'name':'BASNet','network':'ResNet-34'}                  #2
# metas.append(meta)
# meta = {'name':'GGNet_1','network':'ResNet-50'}                  #19
# metas.append(meta)
# meta = {'name':'MENet','network':'ResNet-50'}                  #19
# metas.append(meta)

dataset_names = datasets.split('+')
method_names = []
meta1s = []
for meta in metas:
    method_names.append(meta['name'])
    meta1s.append(meta['network'])

# datasets = 'DUT-OMRON+DUTS-TE+ECSSD+HKU-IS+PASCAL-S'
# methods = 'AFNet+GateNet_ResNet50+GateNet_VGG16+MINet_VGG16'
# method_names = methods.split('+')
# dataset_names = datasets.split('+')

def get_order(items,MAE='MAE'):
    temps = []
    for item in items:
        temps.append(item[MAE])

    if MAE == 'MAE':
        sorted_id = sorted(range(len(temps)), key=lambda k: temps[k], reverse=False)
        #sorted_id = sorted(temps, key=lambda x: float(x))
    else:
        sorted_id = sorted(range(len(temps)), key=lambda k: temps[k], reverse=True)

    i = 0
    for id in sorted_id:
        items[id][MAE+'_order'] = i
        if i == 0:
            items[id][MAE + '_color'] = 2
        elif i == 1:
            items[id][MAE + '_color'] = 3
        elif i == 2:
            items[id][MAE + '_color'] = 4
        else:
            items[id][MAE + '_color'] = 0

        i += 1



bs = []
for dataset in dataset_names:
    items = []
    for method,meta1 in zip(method_names,meta1s):
        file = os.path.join(res_dir, method + '_' + dataset + '.pth')
        if os.path.exists(file):
            iRes = torch.load(file)
            iRes.pop('Prec')
            iRes.pop('Recall')
            iRes.pop('Fm')
            #iRes.pop('TPR')
            #iRes.pop('FPR')
            #iRes.pop('Em')
            # temp = json.dumps(iRes)
        else:
            iRes = {}
            iRes['MAE'] = 100
            iRes['MaxFm'] = 0
            iRes['MeanFm'] = 0
            iRes['AP'] = 0
            #iRes['AUC'] = 0
            iRes['MaxEm'] = 0
            iRes['MeanEm'] = 0
            iRes['Sm'] = 0
            h = 0

        items.append(iRes)
        del iRes

    get_order(items, MAE='MAE')
    get_order(items, MAE='MaxFm')
    get_order(items, MAE='MeanFm')
    get_order(items, MAE='AP')
    get_order(items, MAE='MaxEm')
    get_order(items, MAE='MeanEm')
    get_order(items, MAE='Sm')

    bs.append(items)








f = xlwt.Workbook()
sheet1 = f.add_sheet('sheet1',cell_overwrite_ok=True)
row = 0
for dataset,b in zip(dataset_names,bs):
    sheet1.write(row, 1, dataset, set_style('Times New Roman', 220, True))
    row += 1
    col = 0
    sheet1.write(row, col, 'Method', set_style('Times New Roman', 220, True))
    col += 1
    sheet1.write(row, col, 'Backbone', set_style('Times New Roman', 220, True))
    col += 1
    sheet1.write(row, col, 'MAE', set_style('Times New Roman', 220, True))
    col += 1
    sheet1.write(row, col, 'MaxFm', set_style('Times New Roman', 220, True))
    col += 1
    sheet1.write(row, col, 'MeanFm', set_style('Times New Roman', 220, True))
    col += 1
    sheet1.write(row, col, 'AP', set_style('Times New Roman', 220, True))
    col += 1
    sheet1.write(row, col, 'MaxEm', set_style('Times New Roman', 220, True))
    col += 1
    sheet1.write(row, col, 'MeanEm', set_style('Times New Roman', 220, True))
    col += 1
    sheet1.write(row, col, 'Sm', set_style('Times New Roman', 220, True))

    row += 1
    items = []
    for method,meta1,order in zip(method_names,meta1s,b):
        file = os.path.join(res_dir, method + '_' + dataset + '.pth')
        if os.path.exists(file):
            iRes = torch.load(file)
            iRes.pop('Prec')
            iRes.pop('Recall')
            iRes.pop('Fm')
            #iRes.pop('TPR')
            #iRes.pop('FPR')
            #iRes.pop('Em')
            #temp = json.dumps(iRes)
        else:
            iRes = {}
            iRes['MAE'] = 100
            iRes['MaxFm'] = 0
            iRes['MeanFm'] = 0
            iRes['AP'] = 0
            #iRes['AUC'] = 0
            iRes['MaxEm'] = 0
            iRes['MeanEm'] = 0
            iRes['Sm'] = 0
            h=0

        col = 0
        sheet1.write(row, col, method, set_style('Times New Roman', 220, False))
        col += 1
        sheet1.write(row, col, meta1, set_style('Times New Roman', 220, False))
        col += 1
        if iRes['MAE'] != 100:
            sheet1.write(row, col, round(iRes['MAE'],4), set_style('Times New Roman', 220, False,color=order['MAE_color']))
        col += 1
        if iRes['MaxFm'] != 0:
            sheet1.write(row, col, round(iRes['MaxFm'],4), set_style('Times New Roman', 220, False,color=order['MaxFm_color']))
        col += 1
        if iRes['MeanFm'] != 0:
            sheet1.write(row, col, round(iRes[ 'MeanFm'],4), set_style('Times New Roman', 220, False,color=order['MeanFm_color']))
        col += 1
        if iRes['AP'] != 0:
            sheet1.write(row, col, round(iRes['AP'],4), set_style('Times New Roman', 220, False,color=order['AP_color']))
        col += 1
        if iRes['MaxEm'] != 0:
            sheet1.write(row, col, round(iRes['MaxEm'],4), set_style('Times New Roman', 220, False,color=order['MaxEm_color']))
        col += 1
        if iRes['MeanEm'] != 0:
            sheet1.write(row, col, round(iRes['MeanEm'],4), set_style('Times New Roman', 220, False,color=order['MeanEm_color']))
        col += 1
        if iRes['Sm'] != 0:
            sheet1.write(row, col, round(iRes['Sm'],4), set_style('Times New Roman', 220, False,color=order['Sm_color']))


        row += 1

if os.path.exists(out + "/out/MAEs.xls"):
    os.remove(out + "/out/MAEs.xls")
f.save(out + '/out/MAEs.xls')
