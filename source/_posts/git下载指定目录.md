---
title: git下载指定目录
date: 2017-08-01 18:02:02
tags:
  - git
categories: 系统
permalink: git-download-the-specified-directory
---

>Git1.7.0以后加入了Sparse Checkout模式，这使得Check Out指定文件或者文件夹成为可能。

### 具体实现如下
```shell
#照常创建新项目
mkdir project_name
cd project_name
git init
git remote add origin <url>
#接下来，在Config中允许使用Sparse Checkout模式
git config core.sparsecheckout true
#比较只需要下载src目录与README.md 文件
echo "src" >> .git/info/sparse-checkout
echo "README.md" >> .git/info/sparse-checkout
#不下载src/test目录
echo "!src/test" >> .git/info/sparse-checkout
#最后拉取项目
git pull origin master
```
