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

### 全局设置
- 连接设置
  - 监听端口部分照着设置就行
  - 代理服务器: 代理ip和端口看你用的代理工具，要勾上使用代理进行主机名查询
  ![](https://dl.ystyle.top/images/2020-04/uTorrent_2020-04-25_21-59-01.png)
  
- 任务设置
  - DHT和UDP tracler一定要勾上
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
