---
title: Github协助工作流
tags:
  - GIT
categories: 系统
permalink: githubxie-zhu-gong-zuo-liu
id: 17
updated: '2015-09-24 18:11:13'
date: 2015-08-06 06:45:27
---

## Github协助工作流

### 描述

给Github新手的一个简单的参与开源项目的方法

### 准备工作
Git客户端: [`git-scm`](http://www.git-scm.com/download/) [常称git或 git bash]、[`github for windows`](https://windows.github.com/)

### `Fork` 项目

>首先进入你要参与项目的首页, 网址类似这样的 `https://github.com/${username}/${projectname}`  
>点击右上角的按钮 `Fork`  
>现在你自己的仓库里就`clone`了一个和主项目一样的仓库

### `clone`项目到本地
git bash
>在工作空间右键git bash 打开终端  
>项目右边有输入框:`HTTPS clone URL`点击输入框旁边的按钮`copy to clipboard`  
>把地址复制到 git bash 里回车下载到本地

github[可以在右上的齿轮里登陆帐号]
>打开`github for windows`左上的+号点 `clone` 会刷新自己的项目，选择就下载到本地了


### 修改文件或代码
>已经把代码/文件下载到本地了，随意debug, 新增功能什么的


### 上传文件
>修改新增文件后要用`git add .`标记文件,  (初始化项目是：git init)
>用`git commit -m "message for update" `提交文件(本地缓存),   
>用`git push`上传文件 用git bash的username是github的用户名/密码

注: (密钥方式自己看其它教程配置)

### 请求合并代码
进入自己的首页，进入自己`clone`的项目
在分支与代码目录之间有一个连接`Pull request` 如下图：
![](/images/2015/08/----20150806220439.png)





>点击这连接向主仓库发起一个`Pull request` 请求

![](/images/2015/08/----20150806220942.png)





>填写你的说明：如修改了什么代码或新增了什么功能什么的

![](/images/2015/08/----20150806221008.png)



>成功的截图


![](/images/2015/08/----20150806221500.png)




>成功发起了一个`Pull request` 请求



>对方接收到`Pull request` 请求，如果主仓库接受你的代码的话，主仓库会合并这些代码

![](/images/2015/08/-1-P7BO-Y1-1_LRWJU-T32J.png)
