---
title: 安装flutter
date: 2019-01-23 18:47:21
tags:
  - android
  - flutter
categories: 编程
permalink: install-flitter-without-android-studio
---
# 安装flutter
> 因为不想安装Android Studio， 所以只安装了安装Android sdk

### 安装安卓sdk
到[https://developer.android.google.cn/studio/](https://developer.android.google.cn/studio/) 下载 Android-sdk-tools命令行工具

![chrome_2019-01-23_17-25-00.png](https://dl.ystyle.top/images/2019-01/chrome_2019-01-23_17-25-00.png)

下载后直接解压就行了，如图。 解压后其实只有`tools`一个文件夹, 我已经执行过安装其它工具的命令了，所以有那么多文件夹

![explorer_2019-01-23_17-26-32.png](https://dl.ystyle.top/images/2019-01/explorer_2019-01-23_17-26-32.png)

在`android-sdk-windows`目录打开终端(按着shift 右键打开命令行)
```
.\tools\bin\sdkmanager.bat --licenses
.\tools\bin\sdkmanager.bat "build-tools;28.0.3"
.\tools\bin\sdkmanager.bat "platforms;android-28"
.\tools\bin\sdkmanager.bat "platform-tools"
```
>如果需要代理在每句命令后面加上`--no_https --proxy=http --proxy_host=mirrors.neusoft.edu.cn --proxy_port=80`

![powershell_2019-01-23_17-30-42.png](https://dl.ystyle.top/images/2019-01/powershell_2019-01-23_17-30-42.png)

过程中有提示确认的全部输入`y`再按回车键

### 安装fluter
到官网[Windows install - Flutter](https://flutter.io/docs/get-started/install/windows)下载安装包，然后直接解压就行

![explorer_2019-01-23_17-45-01.png](https://dl.ystyle.top/images/2019-01/explorer_2019-01-23_17-45-01.png)

### 设置环境变量
- 设置`ANDROID_HOME`变量
![SystemPropertiesAdvanced_2019-01-23_17-45-44.png](https://dl.ystyle.top/images/2019-01/SystemPropertiesAdvanced_2019-01-23_17-45-44.png)
- 设置flutter的变量
![Boostnote_2019-01-23_17-47-12.png](https://dl.ystyle.top/images/2019-01/Boostnote_2019-01-23_17-47-12.png)

### gradle 换源
- 放一个init.gradle 文件到USER_HOME/.gradle/目录下
- 放一个后缀是.gradle的文件到 USER_HOME/.gradle/init.d/ 目录下.
- 放一个后缀是.gradle的文件到 GRADLE_HOME/init.d/ 目录下.
- `init.gradle`如下
```gradle
allprojects {
    repositories {
        mavenLocal()
        maven { url 'http://maven.aliyun.com/nexus/content/repositories/central/' }
    }
}
```
- 另一个方法是在当前项目下修改build.gradle
```gradle
repositories {
    mavenLocal()

    maven { url 'http://maven.aliyun.com/nexus/content/repositories/central/' }

    mavenCentral()
}
```

然后打包时会自动执行项目下的`./gradlew`, 会启用上面的源。如果没安装gradle的话会自动下载， 下载很慢， 可以自己去Gradle官网下载然解压配置到环境变量

### 测试
![powershell_2019-01-23_18-14-17.png](https://dl.ystyle.top/images/2019-01/powershell_2019-01-23_18-14-17.png)

如图，安装编译工具链已经安装完成，！号的表示可选操作安装

之后就可以用喜欢的编辑器或IDE开发fluter了， 而不需要安装android stuiod,
特别是只做编译一下的

### 编译测试
![powershell_2019-01-23_18-43-50.png](https://dl.ystyle.top/images/2019-01/powershell_2019-01-23_18-43-50.png)
