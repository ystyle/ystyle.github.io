---
title: tensorflow 在windows 下使用gpu
tags:
  - tensorflow
  - tensorflow-gpu
categories: 编程
permalink: tensorflow-zai-windows-xia-shi-yong-gpu
id: 45
updated: '2017-09-16 10:52:26'
date: 2017-01-06 04:49:17
---

## tensorflow 在windows 下怎么使用gpu

### 需要安装的工具
- python 3.5.x
- tensorflow-gpu (1.13.0)
- Cuda Toolkit 8.0
- cuDNN 6.x
- Visual C++ 2015 64 bit

### 安装 Visual C++ 2015 64 bit
[下载地址](https://www.microsoft.com/zh-cn/download/details.aspx?id=48145)
点页面中间的下载， 然后选择64位
![下载Visual C++ 2015](http://osloqpukl.bkt.clouddn.com/201717161118-r.png)
下载后双击安装就好了

### 安装tensorflow-gpu
```shell
pip install tensorflow-gpu
```

### 安装Cuda Toolkit 8.0
[Cuda Toolkit 8.0下载地址](https://developer.nvidia.com/cuda-downloads)

![Cuda Toolkit 8.0](/images/2017/01/chrome_2017-01-07_23-29-28.png)


>安装前注意更新显示驱动! 下载后安装一路下一步

### 安装cuDNN
- [cuDNN下载地址](https://developer.nvidia.com/cudnn) 点页面中间的`Download`按钮 然后登陆后点击`I Agree To the Terms of the cuDNN Software License Agreement`就能下载了

![cuDNN](http://osloqpukl.bkt.clouddn.com/201717271824-W.png)

- 解压

- 添加bin目录到环境变量PATH

![安装cuDNN](/images/2017/01/atom_2017-01-08_00-17-53.png)

### 测试

![测试1](/images/2017/01/powershell_2017-01-07_23-47-28.png)

![测试2](/images/2017/01/powershell_2017-01-08_00-06-02.png)

![测试3](/images/2017/01/powershell_2017-01-08_00-21-34.png)

>注意1： 如果都安装好但tensorflow没反应的话， 先卸载tensorflow tensorflow-gpu 然后重装

>注意2： 运行报错Couldn't open CUDA library cupti64_80.dll 解决方法：${CUDA_HOME}/extras/CUPTI/lib64 添加到PATH环境变量
