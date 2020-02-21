---
title: KDE添加右键菜单
tags:
  - linux
  - kde
categories: 系统
permalink: add-custom-context-menu-to-kde-dolphin
id: 21
updated: '2020-02-21 15:11:48'
date: 2020-02-21 15:11:48
---

## KDE添加右键菜单
### 文件存放位置
- $HOME/.local/share/kservices5/
- /usr/share/kservices5/

### 示例
```xml
[Desktop Entry]
Actions=OptimisePNG;
MimeType=image/png;
Type=Service
X-KDE-ServiceTypes=KonqPopupMenu/Plugin
Icon=tools-wizard.png

[Desktop Action OptimisePNG]
Name=Optimise PNG Image
Icon=tools-wizard.png
Exec=optipng -o7 %f
```

### 说明
- [Desktop Entry]
  - `Actions`: 在该菜单中的菜单项，多个用英文分号隔开
  - `MimeType`: 在指定的文件类型中启动该菜单
    - `inode/directory` 在目录中启用
    - `image/png` 只在png图片启用
    - `all/allfiles`在所有文件中启用（不包括文件夹）
    - `image/allfiles` 在所有图片启用
  - Type=Service: 表示服务，不会在开始菜单中显示， 改为Application表示应用，会显示在开始菜单
  - `X-KDE-ServiceTypes=KonqPopupMenu/Plugin`: 只在kde中支持，  表示显示在`右键-动作`下边
  - `X-KDE-Priority=TopLevel` 表示显示在顶级菜单中，右键直接显示
  - `Icon` Type=Service 时图标不会显示
- [Desktop Action OptimisePNG]
  - `OptimisePNG`为自定义的动作，填写在上边的`Actions`里
  - `Name`菜单项名称
  - `Icon`菜单显示图标
  - `Exec`点击菜单时执行的命令
    - %f 文件列表。用于可一次打开多个本地文件的应用程序。每个文件都作为单独的参数传递给可执行程序。
    - %F 即使选择了多个文件，也只有一个文件名（包括路径）。读取桌面条目的系统应认识到所讨论的程序无法处理多个文件参数，并且如果该程序无法处理其他文件参数，则应该为每个选定文件生成并执行该程序的多个副本。如果文件不在本地文件系统上（即，在HTTP或FTP位置），则文件将被复制到本地文件系统，%f并将展开以指向临时文件。用于不了解URL语法的程序。
  - `[Desktop Action XXXX]` 的条目在一个文件中可以有多个
- 如果新建无误后显示不出来的话， 执行一下`kbuildsycoca5`如果有错误会有提示`
