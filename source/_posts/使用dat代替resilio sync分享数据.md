---
title: 使用dat代替resilio sync分享数据
date: 2018-12-03 15:57:33
permalink: Use-dat-instead-of-resilio-sync-to-share-data
tags:
  - dat
  - resilio sync
categories:
  - 软件
---
>用btsync/resilio sync绝大部分原因就是用来做文件分享，只要简单添加个文件夹，把key复制出去就好了，同步用户数上来后甚至可以把软件关掉也不会影响分享

>在我看来btsync/resilio sync是个绝佳的分享软件，后来那些号称代替它的都只是同步软件或者网盘，核心并不是用来分享也不太适合用来做分享

### windows 安装方法
- 下载安装[Node.js](http://nodejs.cn/download/)
- 然后按`win + s` 搜索`powershell` 打开
- 执行`npm install -g dat`

### linux 和 mac 安装方法
>linux 和 mac 有桌面版, 当然也可以用windows的安装方法， 但有界面更好操作
- [mac](https://github.com/dat-land/dat-desktop/releases/download/v2.0.0/dat-desktop-2.0.0.dmg)
- [linux](https://github.com/dat-land/dat-desktop/releases/download/v2.0.0/dat-desktop-2.0.0-x86_64.AppImage)

![](https://dl.ystyle.top/images/2018-11/screenshot.png)

### 分享文件
- 在要分享的文件夹按着`shift` 点击右键 - `在此处打开powerShell窗口`(也可能是命令行窗口)都可以
![](https://dl.ystyle.top/images/2018-12/explorer_2018-12-04_10-21-44.png)
- 方法一
  - 在窗口输入命令 `dat create` 以创建共享文件夹
![](https://dl.ystyle.top/images/2018-12/powershell_2018-12-04_10-27-04.png)
  - 在窗口输入命令 `dat share` 共享文件夹， 等待进度知完成， 按`ctrl + c` 结束
![](https://dl.ystyle.top/images/2018-12/powershell_2018-12-04_10-27-59.png)
- 即时修改文件
  - 在窗口输入命令 `dat sync` 在共享目录删除、修改、新增文件时会自动分享， 这个可以一直挂着， 要结束可以按`ctrl + c`
![](https://dl.ystyle.top/images/2018-12/powershell_2018-12-04_10-28-39.png)
    >注意看我选中的那行 `dat://0406903bdf62a99da7edb01ccb0c950f33d5c099f444be22afaeb6bb24ffa8a5`
    >分享的文件只有自己机器上能修改， 别人下载后是无法修改的， 相当于resilio sync的只读分享

### 在线查看分享的文件列表
- 打开网站[https://datbase.org](https://datbase.org)
- 在左上角搜索 `dat create`、`dat share`、 `dat sync`、或者`dat status`打印出来的以 `dat://xxx`开头的地址
![](https://dl.ystyle.top/images/2018-12/chrome_2018-12-04_10-30-08.png)

### 下载别人分享的文件
- 在要保存文件的文件夹按着`shift` 点击右键 - `在此处打开powerShell窗口`
- 执行 `dat clone dat://0406903bdf62a99da7edb01ccb0c950f33d5c099f444be22afaeb6bb24ffa8a5 测试2`
- 结尾的`测试2`为存放的文件名字，如果没写，文件夹的名称为那串很长的key
  ![](https://dl.ystyle.top/images/2018-12/powershell_2018-12-04_10-36-59.png)
  ![](https://dl.ystyle.top/images/2018-12/explorer_2018-12-04_10-38-02.png)

### 与别人分享的文件保持同步
- 在已经下载的文件夹按着`shift` 点击右键 - `在此处打开powerShell窗口`
- 输入 `dat sync` 开启同步
![](https://dl.ystyle.top/images/2018-12/powershell_2018-12-04_10-40-34.png)
