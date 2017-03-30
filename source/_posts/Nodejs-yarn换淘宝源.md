---
title: Nodejs yarn换淘宝源
tags:
  - nodejs
  - yarn
categories: 系统
permalink: nodejs-yarnhuan-tao-bao-yuan
id: 39
updated: '2016-10-31 06:38:11'
date: 2016-10-30 18:36:19
---

## Nodejs yarn换淘宝源

如果觉得安装速度慢，安装源和原来 npm 是一样的，可以通用，修改方法如下：
```shell
yarn config get registry
# -> https://registry.yarnpkg.com
```
可以改成 taobao 的源：
```shell
yarn config set registry 'https://registry.npm.taobao.org'
# -> yarn config v0.15.0
# -> success Set "registry" to "https://registry.npm.taobao.org".
# -> Done in 0.04s.
````
然后 yarn install 的速度就快多了
