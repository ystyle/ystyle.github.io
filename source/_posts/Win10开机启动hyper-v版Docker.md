---
title: Win10开机启动hyper-v版Docker
date: 2018-01-23 09:23:00
tags:
  - Docker
  - hyper-v
  - win10
categories: 系统
permalink: Win10-auto-start-hyper-v-version-of-Docker
---

### 简介
>当前的Dcoker for windows hyper-v版本不能开机自动启动，自己解决了这问题，记录一下解决方法

### 解决步骤
- `win + s` 搜索 `计划任务` 按回车
- 在`任务计划程序库` 右键 `创建任务`
- 在弹出窗口，名称 填写 `开机启动Docker`
- 选择 `触发器` 页签 `新建` 在开始任务选择`启动时` 确认
- 在` 操作` 页签 `新建` 操作选择`启动程序` 在程序或脚本填写Docker文件位置
  - 选择开始菜单的局势方式也行` "C:\ProgramData\Microsoft\Windows\Start Menu\Docker for Windows.lnk" ` 引号也要复制

### 详细步骤图
![](https://dll.ystyle.top/qiniu//20180123/0946-u.png)

![](https://dll.ystyle.top/qiniu//20180123/0947-b.png)

![](https://dll.ystyle.top/qiniu//20180123/0947-x.png)

![](https://dll.ystyle.top/qiniu//20180123/0948-Y.png)
