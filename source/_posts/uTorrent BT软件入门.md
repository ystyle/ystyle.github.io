---
title: uTorrent BT软件入门
date: 2020-04-25 22:36:26
updated: 2020-04-25 22:36:26
tags:
- uTorrent
- BT
categories: 软件
permalink: getting-start-utorrent
---

>软件设置并不能解决百分百的问题，BT是有死链的概念的，这种怎么设置都无法下载，还有些冷门内容速度慢是无法解决的，但大家可以尽量少用讯雷下载。 讯雷p2p只上传给自己的服务器，别的下载工具得不到p2p加速，并且还免费给讯雷做下载点

>如果遇到喜欢的资源，想让更多的人知道、下载就多给种子挂【做种】吧，下载完后默认就开了的，建议分享率大于1时再关，有条件的可以一直挂着

### 全局设置
- 连接设置
  - 监听端口部分照着设置就行
  - 代理服务器: 代理ip和端口看你用的代理工具，要勾上使用代理进行主机名查询
  ![](https://dl.ystyle.top/images/2020-04/uTorrent_2020-04-25_21-59-01.png)
  
- 任务设置
  - DHT和UDP tracker一定要勾上
  - 传出连接选择强制, 去掉[允许传入旧式中接]
  - 建议按我的设置
  ![](https://dl.ystyle.top/images/2020-04/uTorrent_2020-04-25_22-07-54.png)

- 去广告
  - 把以下设置为false
    - offers.sponsored_torrent_offer_enabled
    - offers.left_rail_offer_enabled
    - gui.show_plus_upsell
  ![](https://dl.ystyle.top/images/2020-04/uTorrent_2020-04-25_22-11-06.png)

### 下载任务设置
> 主要是开DHT,和设置tracker, DHT开在连接上面的任务里说过了

- Tracker是什么
  >一般下载文件是用http/ftp/smb无协议的域名或ip来明确指向文件存放在哪个IP的服务器上， 但BT是用识别码来标识文件，而没有明确的文件地址。 所以为了找到文件就需要有一个机制来确定目标文件在哪些机器上能下载到。 DHT和Tracker服务器都能做到文件寻址。

  - DHT: 是内嵌在BT软件里边的，会和电脑能识别并能连接上的BT网络进行数据交换和查询，从而找到文件需要到哪个IP去下载。
  - Tracker: 是运行在别人搭建好的服务器上，你只需要在下载时填写别人提供的Tracker连接就好了，BT软件会连接服务器进行文件查询并取到下载文件的IP地址


- 设置Tracker
  - 在任务上右键-属性
  - 打开[`https://github.com/ngosang/trackerslist`](https://github.com/ngosang/trackerslist)
    - 把 `trackers_best_ip.txt` 或 `trackers_all.txt` 的内容复制到tracker里
    - trackers_best_ip 如果部分tracker被墙了域名，可以用这个试试
    - trackers_all 一般是域名的，如果墙了域名的可能连接不上，破解方法在上面 【全局设置 - 连接设置 - 设置代理】
    - 终极方法是启用全局代理，但梯子月费比较贵，流量也少，所以以上都用不了时才开来下载
  - 一般是勾上了DHT的，没有勾的，自行勾上
  ![](https://dl.ystyle.top/images/2020-04/uTorrent_2020-04-25_22-12-56.png)

### 制作种子或磁力链接
![](https://dl.ystyle.top/images/2020-04/uTorrent_2020-04-25_22-26-24.png)

![](https://dl.ystyle.top/images/2020-04/uTorrent_2020-04-25_22-29-50.png)
- 点击`文件-制作新的torrent` 或 工具栏 箭头那个图标
- 在选择源添加文件或目录
- 有必要时在Tracker里添加新的链接
- 勾选【开始做种】， 默认已经选上
- 点创建，选择种子保存位置， 这种子可以发给别人
- 生成磁力链接: 在【做种中】界面 右键任务 - 【复制Magnet链接】

### 边下边播功能
![](https://dl.ystyle.top/images/2020-04/qimgv_2020-04-25_23-45-43.png)
- 选择正在下载的任务
- 在下面板选择文件
- 在下载中的文件右键复制串流地址
- 打开其它支持播放url的播放器 打开这网址，就能实现边下边播放的功能了
