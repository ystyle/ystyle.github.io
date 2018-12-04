---
title: windows 10 右键用子系统Archlinux打开文件
date: 2018-11-01 15:57:33
permalink: Windows-10-open-with-wsl-Archlinux
tags:
  - Archlinux
  - WSL
categories:
  - 系统
---

### 要求
- windows 10 更新到最新
- 开启 Windows Subsystem for Linux 功能
>过程请看其它文章

### Archlinux简略安装配置过程
- 用[yuk7/ArchWSL](https://github.com/yuk7/ArchWSL/) 安装Archlinux
- 进行[基础设置](https://github.com/yuk7/ArchWSL/wiki/How-to-Setup)
- 安装[spacevim ](https://spacevim.org/)
  `curl -sLf https://spacevim.org/install.sh | bash`
- 安装[zsh](https://github.com/robbyrussell/oh-my-zsh/wiki/Installing-ZSH)
  `pacman -S zsh`
- 安装[oh-my-zsh](https://github.com/robbyrussell/oh-my-zsh)
  `sh -c "$(curl -fsSL https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh)"`


### windows 右键菜单设置
### 以下存为文件 -> `文件夹空白位置右键打开zsh.reg`
```reg
Windows Registry Editor Version 5.00

[HKEY_CLASSES_ROOT\Directory\Background\shell\Open with Arch]
"Icon"="Y:\\Users\\YSTYLE\\Downloads\\Arch\\Arch.exe"

[HKEY_CLASSES_ROOT\Directory\Background\shell\Open with Arch\command]
@="Y:\\Users\\YSTYLE\\Downloads\\Arch\\Arch.exe run zsh"
```
> 修改Arch.exe的位置，记得用\\， 然后右键该文件点合并

### 以下存为文件 -> `文件夹空白位置右键打开vim.reg`
```reg
Windows Registry Editor Version 5.00

[HKEY_CLASSES_ROOT\Directory\Background\shell\Open with Vim]
"Icon"="Y:\\Users\\YSTYLE\\Downloads\\Arch\\Arch.exe"

[HKEY_CLASSES_ROOT\Directory\Background\shell\Open with Vim\command]
@="Y:\\Users\\YSTYLE\\Downloads\\Arch\\Arch.exe run runvim.sh '%V'"
```
>处理方式同上

同时要在Archlinux的/bin下面添加一文件`runvim.sh`
```shell
#!/bin/bash

FILENAME=$1
FILENAME=${FILENAME/:/}
FILENAME=${FILENAME//\\/\/}
FILENAME=/mnt/${FILENAME,}
vim $FILENAME
```
执行命令: `sudo chmod +x /bin/runvim.sh`

### 以下存为文件 -> `文件右键用vim打开.reg`
```reg
Windows Registry Editor Version 5.00

[HKEY_CLASSES_ROOT\*\shell\Open with Vim]
"Icon"="D:\\Application\\Neovim\\bin\\nvim-qt.exe"

[HKEY_CLASSES_ROOT\*\shell\Open with Vim\command]
@="Y:\\Users\\YSTYLE\\Downloads\\Arch\\Arch.exe run runvim.sh '%1'"
```

### 功能测试
三个文件都右键合并到注册表。

- 在文件夹右空白位置右键 可以看到
  - Open with Arch: 可以在Archlinux中打开当前目录
  - Open with Vim： 可以在vim打开当前目录
- 在文件右键可以看到
  - Open with Vim： 可以在vim打开当前选中文件
