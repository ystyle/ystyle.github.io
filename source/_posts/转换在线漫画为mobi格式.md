---
title: 转换在线漫画为mobi格式
date: 2020-09-04 12:46:26
updated: 2020-09-04 12:46:26
tags:
- mobi
- kindle
- 漫画
categories: 软件
permalink: comic-cli
---
>转换在线漫画为mobi格式的工具

### 支持的网站
- 动漫之家
- 喵同人


### 使用方法
- 必需安装`谷歌浏览器chrome`
- 下载[comic-cli: https://pan.baidu.com/s/1EPkLJ7WIJYdYtRHBEMqw0w](https://pan.baidu.com/s/1EPkLJ7WIJYdYtRHBEMqw0w), 提取码:h4np
- 新建一个文件文件
```text
# 注释:  以#号或//开头的行会被忽略，空行也会被忽略
// 本文件会生成三个漫画文件

// 下载整个动漫，直接写列表地址
https://www.dmzj.com/info/wodenvpengyouyoudianqiguaidanshihenkeai.html

// 也可以载指定的章节，填写需要下载的章节地址，同一漫画的章节会合并成同一个文件
https://www.dmzj.com/view/benghuai3rd/102129.html#@page=1
https://www.dmzj.com/view/benghuai3rd/101570.html
// 这行地址的章节会被忽略
# https://www.dmzj.com/view/benghuai3rd/101013.html

// 喵同人网站的写列表地址就好了
https://zh.nyahentai.site/g/326699/
```
- 然后把文件拖到comic-cli里边就会自动把漫画转为mobi格式
- 如果没有生成则把`kindlegen.exe`放到`c:/windows`里再试试

![图文教程](https://dl.ystyle.top/images/2020-09/WindowsTerminal_2020-09-05_12-04-06.png)

### 目前存在的问题
- 转换工程文件到mobi格式时，可能失败，kindlegen没输出原因和错误内容，目前无法解决， 只能多次重试了。

### 其它工具
- [txt文件转epub和mobi的工具TmdTextEpub和kaf](https://ystyle.top/2019/12/31/txt-converto-epub-and-mobi/)
- 喵同人在线转换为mobi格式[hcc](https://hcc.ystyle.top/)
