---
title: 解决手动删除lxss文件夹后提示LX 子系统有安装、卸载或维护操作未完成的问题
date: 2017-11-27 11:38:08
tags:
  - wsl
  - linux
  - win10
categories: 系统
permalink: lx-subsystem-installation-uninstall-or-maintenance-operation-is-not-completed
---
### 出错表现
输入 `lxrun /uninstall /full /y` 出现以下内容
```cmd
PS D:\Code\linux\WSL-Distribution-Switcher> lxrun /uninstall /full /y
这将在 Windows 中卸载 Ubuntu。
这将删除 Ubuntu 环境以及任何修改、新应用程序和用户数据。
正在卸载...
LX 子系统有安装、卸载或维护操作未完成。
```

### 解决方案
- 结束 `bash`进程
- 结束 `lxrun.exe` 进程(同名或相关的都结果掉)
- 重新执行`lxrun /uninstall /full /y`
