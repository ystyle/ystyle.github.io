---
title: electron-react-boilerplate 开环境搭建
permalink: electron-react-boilerplate-kai-huan-jing-da-jian
tags:
  - electron
  - react
categories: 系统
id: 47
updated: '2017-02-28 19:27:08'
date: 2017-02-24 15:14:13
---

>因为electron下载被墙的原因, electorn很难下载成功, electorn的react, redux的开发插件也装不上, 本文记录了解决这些问题时的方法

### 安装electron
 1. 在[淘宝镜像](https://npm.taobao.org/mirrors/electron/)上下载`package.json`对应版本的`electron-vx.x.xx-win32-x64.zip`文件与`SHASUMS256.txt`文件
 2. windows 64位一般下载electron-vx.x.xx-win32-x64.zip的包
 3. 下载的`electron-vx.x.xx-win32-x64.zip`包放到用户目录`~/.electron`下面
 4. `SHASUMS256.txt` 同上, 并把文件名改为`SHASUMS256.txt-x.x.xx` x.x.xx为package.json里的对应版本

 >随便说一下: chromedriver如果npm没安装成功, 可以在[淘宝镜像](https://npm.taobao.org/mirrors/chromedriver)上下载放到用户目录`~/.electron`下面

### 安装electron的开发插件[React Developer Tools, Redux DevTools]
把插件解压并复制到`~/AppData/Roaming/Electron/extensions`目录下

- 方式一
>下载chrome官方插件
[React Developer Tools](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi)
和 [Redux DevTools](https://chrome.google.com/webstore/detail/redux-devtools/lmhkpmbekcpmknklioeibfkpmmfibljd)

- 方式二
>复制chrome安装后的插件目录, 使用全盘搜索 `fmkadmapgofadopljbjfkapdkoienihi`,`lmhkpmbekcpmknklioeibfkpmmfibljd` 然后复制到electron的插件目录


- 方式三
>直接从githut上clone后自己构建[React Developer Tools](https://github.com/facebook/react-devtools) [Redux DevTools](https://github.com/zalmoxisus/redux-devtools-extension)

ps: 如果复制的`fmkadmapgofadopljbjfkapdkoienihi`这种目录下有版本号, 要把版本号目录里边的东西剪切到和版本号目录同级

安装好的目录结构是这样的:
```
 ~/AppData/Roaming/Electron/extensions
$ tree . -L 2
.
|-- IDMap.json
|-- fmkadmapgofadopljbjfkapdkoienihi
|   | ......
|   |-- manifest.json
|   `-- panel.html
`-- lmhkpmbekcpmknklioeibfkpmmfibljd
    |-- _metadata
    |-- ......
    |-- remote.html
    `-- manifest.json
```


### 安装依赖并启动
- 安装依赖: npm install
- 启动: 执行electron-react-boilerplate提供的命令npm run dev
- 如果再webpack打包和electron启动分开可以分别在两个终端执行`npm run hot-server`, `npm run start-hot`
