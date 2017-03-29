---
title: Git单文件恢复到历史版本
tags:
  - GIT
categories: 系统
permalink: gitdan-wen-jian-hui-fu-dao-li-shi-ban-ben
id: 14
updated: '2015-06-29 09:14:00'
date: 2015-06-29 07:02:49
---

### 查看commit_id
```
git log $filename
```
### 重置文件
```
git reset $commit_id
```
### 恢复文件
```
git checkout $filename
```
