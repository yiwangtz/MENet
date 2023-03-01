# Pixels, Regions, and Objects: Multiple Enhancement for Salient Object Detection

> A majority of salient object detection (SOD) methods interpret images from the perspective of pixels and use a simple end-to-end training method, which leads to incomplete and blurred boundaries of targets in complex scenes. To address this issue, we propose a novel Multiple Enhancement Network (MENet) to simulate the ability of humans to gradually enhance the cognition of complex targets repeatedly from the perspective of pixels, regions, and objects of images. A new multilevel hybrid loss is first designed to compare prediction and ground truth at pixel-, region-, and object-levels. Then, a flexible multiscale feature enhancement module (ME-Module) is proposed to gradually aggregate and refine features through the atrous spatial pyramid pooling and global-local attention. ME-Module can output high- or low-level features by changing the size order of the input feature sequence. Then, two ME-Modules are used as the core of the dual-branch decoder of the MENet to refine salient features by an iterative enhancement strategy that aggregates high- and low-level gradient boundary features and adaptive inner body features alternately, under the supervision of the proposed multilevel hybrid loss. Comprehensive evaluations on six challenging benchmarks show that MENet achieves state-of-the-art results.

<!---

[![NPM Version][npm-image]][npm-url]
[![Build Status][travis-image]][travis-url]
[![Downloads Stats][npm-downloads]][npm-url]

用一两段话介绍这个项目以及它能做些什么。

![](https://github.com/dbader/readme-template/raw/master/header.png)

## Getting Started 使用指南

项目使用条件、如何安装部署、怎样运行使用以及使用演示

### Prerequisites 项目使用条件

你需要安装什么软件以及如何去安装它们。

```
Give examples
```

### Installation 安装

通过一步步实例告诉你如何安装部署、怎样运行使用。

OS X & Linux:

```sh
Give the example
```

Windows:

```sh
Give the example
```

### Usage example 使用示例

给出更多使用演示和截图，并贴出相应代码。

## Deployment 部署方法

部署到生产环境注意事项。

## Contributing 贡献指南

Please read [CONTRIBUTING.md](#) for details on our code of conduct, and the process for submitting pull requests to us.

清阅读 [CONTRIBUTING.md](#) 了解如何向这个项目贡献代码

## Release History 版本历史

* 0.2.1
    * CHANGE: Update docs
* 0.2.0
    * CHANGE: Remove `README.md`
* 0.1.0
    * Work in progress

## Authors 关于作者

* **WangYan** - *Initial work* - [WangYan](https://wangyan.org)

查看更多关于这个项目的贡献者，请阅读 [contributors](#) 

## License 授权协议

这个项目 MIT 协议， 请点击 [LICENSE.md](LICENSE.md) 了解更多细节。
-->
