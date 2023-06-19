# Pixels, Regions, and Objects: Multiple Enhancement for Salient Object Detection

CVPR 2023
[[paper link](https://openaccess.thecvf.com/content/CVPR2023/html/Wang_Pixels_Regions_and_Objects_Multiple_Enhancement_for_Salient_Object_Detection_CVPR_2023_paper.html)]



### Overview


Salient object detection (SOD) aims to mimic the human
visual system (HVS) and cognition mechanisms to identify
and segment salient objects. However, due to the complexity
of these mechanisms, current methods are not perfect.
Accuracy and robustness need to be further improved, particularly
in complex scenes with multiple objects and background
clutter. To address this issue, we propose a novel
approach called Multiple Enhancement Network (MENet)
that adopts the boundary sensibility, content integrity, iterative
refinement, and frequency decomposition mechanisms
of HVS. A multi-level hybrid loss is firstly designed
to guide the network to learn pixel-level, region-level, and
object-level features. A flexible multiscale feature enhancement
module (ME-Module) is then designed to gradually
aggregate and refine global or detailed features by changing
the size order of the input feature sequence. An iterative
training strategy is used to enhance boundary features
and adaptive features in the dual-branch decoder of
MENet. Comprehensive evaluations on six challenging
benchmark datasets show that MENet achieves state-of-theart
results. Both the codes and results are publicly available
at https://github.com/yiwangtz/MENet.


## Usage
### Installation
```
conda create -n menet python=3.8
conda activate menet

pip install torch==1.10.0+cu111 torchvision==0.11.0+cu111 torchaudio==0.10.0 -f https://download.pytorch.org/whl/torch_stable.html
pip install opencv-python==4.7.0.72
pip install matplotlib==3.7.1
pip install tensorboard==2.12.1
pip install setuptools==59.5.0
pip install timm==0.8.21.dev0
pip install xlwt

git clone https://github.com/NVIDIA/apex
cd apex
pip install -v --disable-pip-version-check --no-cache-dir ./
```

### Data Preparation
Download the following datasets and unzip them into `data` folder
- [DUTS](http://saliencydetection.net/duts/)
- [ECSSD](http://www.cse.cuhk.edu.hk/leojia/projects/hsaliency/dataset.html)
- [HKU-IS](https://i.cs.hku.hk/~gbli/deep_saliency.html)
- [DUT-OMRON](http://saliencydetection.net/dut-omron/)
- [PASCAL-S](http://cbi.gatech.edu/salobj/)
 
The overall file structure is as follows:
```shell
data
├── DUTS
│   ├── image
│   ├── mask
│   ├── train.txt
├── DUT-OMRON
│   ├── image
│   ├── mask
│   ├── test.txt
├── DUTS-TE
│   ├── image
│   ├── mask
│   ├── test.txt
├── ECSSD
│   ├── image
│   ├── mask
│   ├── test.txt
├── HKU-IS
│   ├── image
│   ├── mask
│   ├── test.txt
├── PASCAL-S
│   ├── image
│   ├── mask
│   ├── test.txt
```



### Training & Evaluation
- Generate the ground truth into gradient , which will be saved into `data/DUTS/gradient
```shell
    python generate_gradient.py
```
- Training
```shell
    python train_MENet.py
```
- Testing
```shell
    python test_run_all.py
    python plot_excel_choose_model.py
```

### Trained Model
You can download the trained model :[Baidu key:ibjk]( https://pan.baidu.com/s/1Qk8uGKK-m2aVk09hH0UgeA?pwd=ibjk) 


### Saliency Map

saliency maps: [Baidu key:j9wk]( https://pan.baidu.com/s/1PqS17pX1y1GEqPC7I3NdbQ?pwd=j9wk) 




If you find this repo useful, please cite:
```
@inproceedings{wang2023pixels,
  title={Pixels, Regions, and Objects: Multiple Enhancement for Salient Object Detection},
  author={Wang, Yi and Wang, Ruili and Fan, Xin and Wang, Tianzhu and He, Xiangjian},
  booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition},
  pages={10031--10040},
  year={2023}
}
```

