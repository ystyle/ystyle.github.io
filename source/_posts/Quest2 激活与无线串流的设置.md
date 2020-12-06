---
title: Quest2 激活与无线串流的设置
date: 2020-12-06 01:30:26
updated: 2020-12-06 01:30:26
tags:
- quest2
- 工具
categories: 软件
permalink: quest2
---

# Quest2 激活与无线串流的设置

### 连网激活
> 需要可上网，与tcp、udp转发， 激活更新系统时需要udp转发才能正常更新系统, 本方法完美支持，不需要路由插件什么的， 其它支持udp的方法是需要一个root的安卓， 支持安装插件的路由器，详情看参考里的第二个链接《使用指南》


  - [Netch](https://github.com/NetchX/Netch)： socket5、ss、vmess(v2ray) 转wifi
    - 打不开可能需要安装`.NET Framework 4.8`和`Visual C++ 运行库`
  - 安装[TAP-Windows](https://build.openvpn.net/downloads/releases/tap-windows-9.21.2.exe) 虚拟网卡驱动
  - 打开Netch, 添代理，然后选择tun/tap 绕过局域网， 启动
  - 在win10开启wifi移动热点
  - 在网络适配器管理界面，把带tap的网卡，右键属性-切换到分享， 把第一个勾上，下拉选择wifi热点的网卡
  - 在quest2连接热点，等一会后，联网界面下的确定按钮亮了之后，会进入系统更新
  - 更新系统后，可以切回wifi+http代理方式玩(wifi连接输入密码，下边点高级，可以填入http代理)
  ![](https://dl.ystyle.top/images/2020-12/Netch_2020-12-06_16-44-00.png)
  ![](https://dl.ystyle.top/images/2020-12/explorer_2020-12-06_16-35-08.png)
  ![](https://dl.ystyle.top/images/2020-12/chrome_2020-12-06_20-40-12.png)
  
### 开发者模式
  - [注册开发者帐号](ttps://dashboard.oculus.com)或进入别人的开发者团队
  - [下载adb驱动](https://developer.oculus.com/downloads/package/oculus-adb-drivers), 解压后右键【androidwinusb.inf】选择安装即可。
  - 安装手机[oculus app](https://rawapk.com/oculus-apk-download/)
  - 用数据线连接quest2和电脑
  - 在手机oculus app上连接quest2, 并在设置开启开发者模板
  ![](https://dl.ystyle.top/images/2020-12/BE9BEC5F78EDD4C97982C8353CFE1D13.jpg)
  ![](https://dl.ystyle.top/images/2020-12/27EDA36DBCB42C960E77A19FB20F1557.jpg)
  
### virtual desktop
  - 在quest2上购买`virtual desktop`
    - `virtual desktop`必需买，sidequest上的只是个串流用的插件
  - 在电脑上安装`virtual desktop streamer`串流软件， [官方网站](https://www.vrdesktop.net/)直接免费下载
  - 用数据线连接电脑
  - 安装[sidequest](https://sidequestvr.com/setup-howto), 用它给quest2安装串流插件`virtual desktop vr patch`
  ![](https://dl.ystyle.top/images/2020-12/SideQuest_2020-12-06_16-41-36.png)
  
### 购买virtual desktop
  - 注册paypal
  - 绑定支持银联的银行卡(我用的是邮政的储蓄卡，只有银联，没其它标识)
  - 在`oculus home`、`oculus网站`、或`手机oculus app`绑定paypal
  - 在上述软件中搜索`virtual desktop`点购买，如果出现执行查询出现错误就`更换代理节点`(我用美国节点的会出现这个)
    - 按汇率，卡里需要`137RMB`
    - steam 里的`virtual desktop`不支持quest2

### 串流设置
  - 连接到与电脑同wifi（激活时用的热点也可以用的）
  - 打开电脑上的`virtual desktop streamer`，并在username填写自己的oculus帐户名
  - 在quest2上打开`virtual desktop`软件
  - 这时会显示一个巨大的电脑屏幕， 打开支持`steam vr`或`oculus home`的游戏，会自动串流到quest2里
    - 这时可以愉快的玩耍了
![](https://dl.ystyle.top/images/2020-12/VirtualDesktop.Streamer_2020-12-06_16-38-19.png)

### 参考
 - [Oculus Quest / Quest2 如何设置 VirtualDesktop 实现无线串流【详细教程】_kasaiki的博客-CSDN博客](https://blog.csdn.net/kasaiki/article/details/109145902)
 - [Oculus Quest 国内玩家无障碍使用指南 - VR42](http://vr42.com/t/187)
   - 本文的Netch是此文中方案4的Sstap替代品，sstap已经多年不更新了
 - [【干货】Oculus quest 2电脑连接串流教程｜有线+无线_哔哩哔哩 (゜-゜)つロ 干杯~-bilibili](https://b23.tv/9rEP0A)
