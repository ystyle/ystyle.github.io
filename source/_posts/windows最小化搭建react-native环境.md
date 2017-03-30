---
title: windows最小化搭建react-native环境
tags:
  - react
  - react-native
categories: 系统
permalink: windowszui-xiao-hua-da-jian-react-nativehuan-jing
id: 35
updated: '2016-08-18 10:11:50'
date: 2016-07-30 22:09:37
---

### 准备

- [git for windows](#git)
- [java](#java)
- [gradle](#gradle)
- [node.js](#nodejs)
- [react-native-cli](#reactnativecli)
- [android-sdk](#androidsdk)

### 安装git

[下载git](https://git-scm.com/download)

### 安装java

配置好`JAVA_HOME`环境变量,并把`JAVA_HOME/bin`添加到`path`里

[JDK版本管理工具](http://www.lxy520.net/2015/12/02/windows-jdk-ban-ben-guan-li-qi-jvms-fa-bu/)

### 安装gradle
[下载gradle](https://services.gradle.org/distributions/gradle-2.14.1-all.zip): (若安装过idea之类的工具可以看看`~/.gradle/wrapper/dists`目录下有没有)

配置`GRADLE_HOME`环境变量, 并把`GRADLE_HOME/bin`添加到`path`里

### 安装node.js
[下载Node.js](https://nodejs.org/dist/v4.4.7/node-v4.4.7-x64.msi)

[nvm node版本管理工具](https://github.com/coreybutler/nvm-windows)

### 安装react-native-cli
```shell
# 打开git bash
npm isntall -g react-native-cli
```

### 安装android-sdk
- [下载地址](http://sdk.android-studio.org/)

- 配置`ANDROID_HOME`环境变量, 并把`%ANDROID_HOME%/tools` `%ANDROID_HOME%/platform-tools`添加到`path`里

- 打开sdk-manager下载以下组件
  - Tools/Android SDK toll
  - Tools/Android SDK Platform-tools
  - Tools/Adnroid SDK Build-tools 23.0.1
  - Android 6.0(API 23)/SDK Platform 23
  - Android 6.0(API 23)/Google APIs
  - Extras/Android Support Repository 35
  - Extras/Google USB Driver
> [换android 的源](http://mirrors.neusoft.edu.cn/more.we#android) 看最后一段

### 测试
1. 用USB连接手机
2. 打开`git bash` 初始化项目
```shell
react-native init demo
cd demo
react-native start
react-natve run-android
```

然后用喜欢的编辑器或IDE 打开项目开发即可

### 配置调试环境
用chrome 浏览器打开, `http://localhost:8081/debugger-ui`

按F12 打开开发控制台

拿走打机摇一摇, 在弹出的开发者菜单上选择`Debug JS Remotely`

> 启用代码热更新, 如果想电脑上改js,手机限时生效可以把`Enable live Reload` 和 `Enable Hot Reloading` 打开

再次打开手机的开发者菜单, 选择`reload `

如果网页上最后一行显示为: `Status: Debugger session #0 active.` 时说明已经连接上了调试环境.

转到chrome开发者控制台Rouces页签上,在左边debuggerWorker.js 下载找到要调试的js文件,
加上断点,即可调试


### 注意事项

1. 若一开始就显示红屏, 不能下载js之类的, 在手机可以打开react-native应用的开发者菜单(摇一摇手机), 选择`dev setting`, 在最后一项设置电脑的ip与端口.

2. 若手机是android 5.0以上红屏的话,在`git bash`上执行`adb reverse tcp:8081 tcp:8081`
