---
title: kde在更新系统后不想重启怎么办
date: 2019-12-12 15:24:26
updated: 2019-12-12 15:24:26
tags:
- Linux
- KDE
- Archlinux
categories: 系统
permalink: donot-restart-kde-after-update-system
---

>用Archlinux经常更新系统， 如果遇到kde更新了的话，不重启系统的话很多kde的应用会打不开， 如果不想重启应该怎么办？


### 不重启系统情况下重启KDE5
在更新系统完成后输入: 
```shell
# kquitapp5 plasmashell && kstarts plasmashell
```
太长了不好记建议在.zshrc添加以下内容: 
```shell
alias kr="kquitapp5 plasmashell && kstarts plasmashell"
```
以后更新完后输入`kr`就好了， kde重启后还会有日志输出，直接把终端关了就好了
