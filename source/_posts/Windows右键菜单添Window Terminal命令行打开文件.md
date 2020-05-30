---
title: Windows右键菜单添以Window Terminal命令行打开文件
tags:
  - windows
  - Window Terminal
categories: 系统
permalink: open-file-with-windows-terminal-command
updated: '2020-05-31 22:11:48'
date: 2020-05-31 22:11:48
---

>应用场景: 在文件右键打开windows terminal， 并在执行的命令中以选择的文件为参数运行。 

### 先创建一个右键菜单项
```
Windows Registry Editor Version 5.00

[HKEY_CLASSES_ROOT\*\shell\Open with Micro]
"Icon"="E:\\Code\\Go\\bin\\micro-logo-mark.ico"

[HKEY_CLASSES_ROOT\*\shell\Open with Micro\command]
@="C:\\Users\\Administrator\\AppData\\Local\\Microsoft\\WindowsApps\\wt.exe new-tab -p \"Windows PowerShell\"  micro.exe \"%1\""

```
#### 键的说明
- `[HKEY_CLASSES_ROOT\*\shell\Open with Micro]` 中的 `Open with Micro`为右键菜单名
- Icon 是右键菜单项的图标
- command 里的是菜单项点击后要执行的命令
- `wt.exe new-tab -p \"Windows PowerShell\"  micro.exe '%1'` 
  - wt 必需要写全路径，不写会弹出【选择打开文件需要的应用】那个窗口
  - `new-tab` 是打开一个新的windows terminal 页签(不过在我电脑会打开新的一个应用实例)
  - `-p \"Windows PowerShell\"` 是新页签需要用的的shell，可以是windows terminal的配置中的 name或guid
  - `micro.exe \"%1\"` 是需要执行的命令， `\"%1\"`是当前右键的文件占位符
  
