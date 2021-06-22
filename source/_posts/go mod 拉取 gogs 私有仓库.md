---
title: go mod 拉取 gogs 私有仓库
date: 2021-06-22 10:46:26
updated: 2021-06-22 10:46:26
tags:
- git
- gogs
- go
categories: 软件
permalink: go-mod-gogs-private
---

### 环境变量设置
1. 添加环境变量或设置go env
```
export GOPRIVATE=git.hofo.co
# 或者
go env -w GOPRIVATE=git.hofo.co
```

### git设置
1. 在git设置http.extraheader
   - `PRIVATE-TOKEN`生成方式:  在点击gogs右上头像-用户设置-授权应用-生成新的token
```shell
git config --global http.extraheader "PRIVATE-TOKEN: 5737d215af7f9a41a2abe98631d312e9e9311d29d"
```
2. 在git添加url配置, `ystyle:5737d215af7f9a41a2abe98631d312e9e939d29d11`是用户名和上一步生成的token
```shell
git config --global url."https://ystyle:5737d215af7f9a41a2abe98631d312e9e939d29d11@git.hofo.co".insteadOf "https://git.hofo.co"
```
