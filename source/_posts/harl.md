---
title: harl-鸿蒙应用开发实机热更新工具
date: 2020-10-25 01:30:26
updated: 2020-10-25 01:30:26
tags:
- 鸿蒙
- 工具
categories: 软件
permalink: harl
---

[鸿蒙应用开发实机热更新工具](https://gitee.com/ystyle/harl/)

### 依赖
- debug 版本的hi3516镜像(release版本不支持shell)
- nfs v3
  - [配置过程](https://openharmony.gitee.com/openharmony/docs/blob/master/kernel/NFS.md)
  - [配置过程可能遇到的问题](https://openharmony.gitee.com/openharmony/docs/issues/I1YIBO)
- serial(串口)
- dev tools (可以从鸿蒙编译目录`/out/ipcamera_hi3516dv300/dev_tools/bin`复制到nfs挂载目录)
  - aa (管理APP启动，关闭)
  - bm (安装卸载APP)

### USAGE

```shell
➜ harl.exe
NAME:
   harl - Open Harmony OS Dev tools

USAGE:
   harl.exe [global options] command [command options] [arguments...]

VERSION:
   v0.1.2

COMMANDS:
   init, i    init .harm.yml
   watch, w   watch and reload app
   install    install hap
   uninstall  uninstall hap
   shell      open a shell
   reboot     reboot
   help, h    Shows a list of commands or help for one command

GLOBAL OPTIONS:
   --help, -h     show help (default: false)
   --version, -v  print the version (default: false)
```
- [下载应用](https://gitee.com/ystyle/harl/releases)
- `cd /your-project-dir` 切换到项目目录
- `harl init` 初始化配置文件
- `harl w` 监听项目文件修改
  - 监听时支持输入命令, 若看不到提示符请在调试日志暂停打印时按回车
  - 可以用`^run [command name]`的方式执行command里定义的脚本
    - 如执行示例配置文件的setup脚本， `^run setup`
- 目前命令只支持在项目目录执行

### 配置文件
>.harl.yaml
```yaml
watch: # 监听文件修改并自动编译、安装的参数
  excludes: # 排除的文件
  - .gradle
  - .idea
  - gradle
  - entry/build
  - entry/node_modules
  includes: # 监听的文件类型
  - .css
  - .hml
  - .js
  - .hap
  - .json
  delay: 100 # 监听频率，单位ms
nfs: # nfs 配置
  ldir: H:/bin # 本地nfs挂载目录 
  rdir: /nfs # 远程nfs(开发板)挂载目录
shell: # 开发板连接参数
  com: COM5 # 串口号
command: # 定义常用命令, 在shell或watch里可执行
  setup: # 命令执行方式: ^run setup
    - dhclient eth0 # 命令一行一个, 顺序执行错误不会中断
    - mkdir /nfs
    - mount 192.168.3.12:/nfsshare /nfs nfs
  kill: # 关闭应用
    - cd /nfs
    - ./aa terminate -p top.ystyle.ohos.js.testapp
  start: # 启动应用
    - cd /nfs
    - ./aa start -p top.ystyle.ohos.js.testapp -n default
```

### 支持情况
- 只支持windows
- 只测试过liteWearable项目改的smartVision
- 只在hi3516d上测试过
