---
title: Windows JDK 版本管理器 jvms 0.0.2 发布
tags:
  - jvms
  - JAVA
categories: 系统
permalink: windows-jdk-ban-ben-guan-li-qi-jvms-fa-bu
id: 27
updated: '2016-02-22 18:01:35'
date: 2015-12-03 11:57:21
---

JDK Version Manager (JVMS) for Windows

Windows下JDK多版本管理器，类似 nvm, nvmw, rvm

[jvms下载地址](https://github.com/ystyle/jvms/releases)

本软件源于 [nvm-windows](https://github.com/coreybutler/nvm-windows)

这对JDK不同版本之间切换是非常有用的。例如，如果你想测试一个项目你想使用最新最前沿的版本,却不想卸载JDK的稳定版，这个工具可以很好的解决。

本软件配备了一个安装程序（和卸载），因此安装是很容易的。请注意，您需要删掉以前的JAVA_HOME环境变量再安装JVMS。

欢迎提交其它版本的下载地址:  [提交jdk版本下载链接](https://github.com/ystyle/jvms/blob/master/submit.md)

软件介绍:

 - `jvms ls` 查看受jvms管理的jdk
 - `jvms ls-remote ` 查看jvms源里提供下载的jdk版本
 - `jvms install <version>` 从jvms源里安装jdk
 - `jvms uninstall <version>` 删除受jvms管理的jdk
 - `jvms use <version>` 使用指定版本的jdk
 - `jvms version` 可看jvms的版本

安装jdk1.6示例
```shell
jvms install 1.6.0_43  ## 安装jdk1.6
jvms use 1.6.0_43 ## 启用jdk1.6
jvm list ## 查看当前使用的版本
```
![](https://github.com/ystyle/jvms/raw/master/dist/images/installlatest.png)


![](https://github.com/ystyle/jvms/raw/master/dist/images/installjdk.png)

![](https://github.com/ystyle/jvms/raw/master/dist/images/use.png)

![](https://github.com/ystyle/jvms/raw/master/dist/images/installer.png)

0.0.2更新:

 - path放到环境变量最前面
 - 源里添加了1.6 jdk64位
