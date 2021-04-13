---
title: txt小说转epub与mobi
tags:
  - 小说
  - kindle
  - epub
  - mobi
  - kaf-cli
categories: 软件
permalink: txt-converto-epub-and-mobi
id: 14
updated: '2020-03-24 13:02:49'
date: 2019-12-31 13:02:49
---

> 把txt文本转成epub、mobi电子书的工具, 支持电脑和安卓APP。


### 下载
- [Github电脑版下载](https://github.com/ystyle/kaf-cli/releases/latest)
- [Github手机版下载](https://github.com/ystyle/kaf-cli/releases/tag/android)
- [百度网盘下载 `https://pan.baidu.com/s/1EPkLJ7WIJYdYtRHBEMqw0w`](https://pan.baidu.com/s/1EPkLJ7WIJYdYtRHBEMqw0w) 提取码：`h4np`
- Archlinux 可以在aur上安装 [`yay -S kaf-cli`](https://aur.archlinux.org/packages/kaf-cli/)

### 功能

功能|kaf-cli|KAF
:--|:--|:-----
支持平台|windows、linux、mac|Android
自动识别书名和章节|支持|支持
自动识别字符编码(自动解决中文乱码)|支持|支持
自动给章节正文生成加粗居中的标题|支持|支持
段落自动识别|支持|支持
段落自动缩进|支持|支持
自定义书名作者|支持|支持
自定义章节标题识别规则|支持|支持
自定义章节标题对齐方式| |支持
自定义段落缩进字数| |支持
WIFI传书| |支持


### 使用方法
- 电脑版
  1. 解压, 把小说直接拖到 `kaf-cli.exe` 文件上面
  1. 等转换完，目录下会生成epub和mobi文件
  1. 如果没有生成mobi，则复制`kindlegen`到`C:\windows`下面，重试
- 安卓版
![](https://dl.ystyle.top/images/2020-03/kaf1.jpg)

![](https://dl.ystyle.top/images/2020-03/kaf2.jpg)

![](https://dl.ystyle.top/images/2020-03/kaf5.jpg)

![](https://dl.ystyle.top/images/2020-03/kaf6.jpg)

### 效果

![异常生物见闻录](https://github.com/ystyle/kaf-cli/raw/master/2020-01-21_12-02.png)

![](https://dl.ystyle.top/images/2020-03/550b751ed21b0ef466cae53fcac451da80cb3efe.jpg)

### 手动把书转为kindle的mobi格式
>新版如果检测到有kindlegen程序时会自动转为mobi

1. 在官网下载[kindlegen](https://www.amazon.com/gp/feature.html?ie=UTF8&docId=1000765211)
2. 同样放到`d:`盘根目录下， 执行以下命令转换
  ```shell
  cd d:/
  d:/kindlegen.exe d:/全职法师.epub
  ```
3. 在d盘就能找到mobi文件了，复制到kindle的documents目录下，打开kindle就能看到小说了

### 命令行模式

命令行全部参数为：
```$xslt
Usage of E:\Code\Go\bin\kaf-cli.exe:
  -author string
        作者 (default "YSTYLE")
  -bookname string
        书名: 默认为txt文件名
  -filename string
        txt 文件名
  -lang string
        设置语言: en,de,fr,it,es,zh,ja,pt,ru,nl (default "zh")
  -match string
        匹配标题的正则表达式, 不写可以自动识别, 如果没生成章节就参考教程。例: -match 第.{1,8}章 表示第和章字之间可以有1-8个任意文字 (default "自动匹配,可自定义")
  -max uint
        标题最大字数 (default 35)
  -tips
        添加本软件教程 (default true)
```

### 在任意位置执行命令
1. 把`kaf-cli.exe` 和 `kindlegen.exe` 放`c:/windows/`下边
2. 上面第1步只需要做一次，以后可以把小说放任意目录，都可以很简单执行转换，每次转换小说的按下面操作，
   - 打开小说在的文件夹, 按住`Shift键`不放，鼠标右击文件夹空白位置
   - 在右键菜单选择 `用命令行打开` 或 `以PowerShell打开`
   - 执行`kaf-cli.exe -filename 异常生物见闻录.txt`,  现在可以不用写盘符了

把`全职法师.txt`生成epub, 并设置作者名为`乱`
```shell
cd d:/
d:/kaf-cli.exe -author 乱 -filename d:/全职法师.txt
```

>以下全部示例都可以自动识别，不需要自己设定标题格式了， 一般用上用上面的例子就行了

>要自定义标题格式参考以下几个例子

自定义章节匹配, 章节格式为`第x节`: 
```shell
cd d:/
d:/kaf-cli.exe -filename d:/ebbok.txt -match "第.{1,8}节"
```

自定义章节匹配, 章节格式为`Section 1` ~ `Section 100`: 
```shell
cd d:/
d:/kaf-cli.exe -filename d:/ebbok.txt -match "Section \d+"
```

自定义章节匹配, 章节格式为`Chapter xxx`: 
```shell
cd d:/
d:/kaf-cli.exe -filename d:/ebbok.txt -match "Chapter .{1,8}"
```



