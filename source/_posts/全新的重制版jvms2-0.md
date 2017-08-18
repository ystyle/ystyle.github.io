---
title: 全新的重制版jvms2.0
date: 2017-07-24 09:22:49
tags:
  - jvms
  - JAVA
categories: 系统
permalink: the-new-heavy-version-of-jvms2.0
---
### 介绍
JDK Version Manager (JVMS) for Windows

Windows下JDK多版本管理器，类似 nvm, nvmw, rvm

[jvms下载地址](https://github.com/ystyle/jvms/releases)

这对JDK不同版本之间切换是非常有用的。例如，如果你想测试一个项目你想使用最新最前沿的版本,却不想卸载JDK的稳定版，这个工具可以很好的解决。

请注意，您需要删掉以前的JAVA_HOME环境变量再安装JVMS。
### 安装

- [Download Now](https://github.com/ystyle/jvms/releases)
- 解压 jvms.zip
- 用管理员身份运行`cmd` 或者 `powershell` (powershell在win10快捷键为`win + X + A`)
- cd 到解压目录
- 执行 `./jvms.exe init`
- 安装成功！
![安装方法](https://github.com/ystyle/jvms/raw/new/images/powershell_2017-07-23_00-38-13.png)

### 使用
```shell
NAME:
   jvms - JDK Version Manager (JVMS) for Windows

USAGE:
   jvms.exe [global options] command [command options] [arguments...]

VERSION:
   2.0.0

COMMANDS:
     init        Initialize config file
     list, ls    List the JDK installations.
     install, i  Install remote available jdk
     switch, s   Switch to use the specified version.
     remove, rm  Remove a specific version.
     rls         Show a list of versions available for download.
     proxy       Set a proxy to use for downloads.
     help, h     Shows a list of commands or help for one command

GLOBAL OPTIONS:
   --help, -h     show help
   --version, -v  print the version
```
以安装jdk 1.8.0_31为例
- 用管理员身份运行`cmd` 或者 `powershell`(`win + X + A`)
- `jvms rls` 列出可以在线安装的jdk版本
- `jvms install 1.8.0_31` 安装 jdk 1.8.0_31
- `jvms ls` 列出本地已安装的jdk版本
- `jvms switch 1.8.0_31` 切换jdk 版本为 1.8.0_31

![切换jdk](https://github.com/ystyle/jvms/raw/new/images/powershell_2017-07-23_01-26-40.png)
