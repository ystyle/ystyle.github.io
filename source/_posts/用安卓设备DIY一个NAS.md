---
title: 用安卓设备DIY一个NAS
date: 2017-11-30 09:11:33
tags:
  - android
  - linux
  - nas
categories: 系统
permalink: diy-a-nas-with-android-device
---

### 网站地址
- 以安卓IP地址`192.168.1.7`为例
- ssh连接地址: `ssh ystyle@192.168.1.7`
- supervisor 管理地址： [http://192.168.1.7:9001/](http://192.168.1.7:9001/)
- aria2 web ui [http://webui-aria2.ghostry.cn/](http://webui-aria2.ghostry.cn/) 设置-连接设置填写aria2 的rpc地址
- aria2 rpc地址： [192.168.1.7:6800](192.168.1.7:6800)
- syncthing 管理页面：[http://127.0.0.1:8384/](http://127.0.0.1:8384/)

### 安卓设置需要安装的软件
- `kingroot` 设备需要`root`
- `linux deploy` 安装linux

### Linux系统安装软件
- bash completion
- screenfetch
- htop
- vim
- supervisor
- aria2
- syncthing

### 安卓部署Linux记录
- 获取root权限
- 安装linux deploy
- 点右下角的图标进去配置界面
  - 选择好linux发行版与版本
    - 架构用默认的就好，手机64位的可选择arm64之类的
  - 设置用户名和密码
  - 本地化选择zh_CN.UTF-8
  - 启用SSH(若喜欢图形界面可以选择桌面环境和VNC的组合)
  - 退出设置到主界面
- 点右上角三点 选择 安装
- 等待系统安装完毕。其中过程出现 fail,download fail之类的重新执行安装过程
  - 重新安装需要点击主界面的停止，卸载已挂载的文件系统，再点右上菜单的清空
  - 继续执行安装操作
- `>>> deploy ... <<< deploy`之间没出现错误说明安装完成
- 点击主界面的启动，出现`>>> start ... ... <<< start`则启动完成
  - 若启动过程出现 extra/ssh fail 之类的，执行重新安装操作
- 左边三横线新建配置文件后，若需要安装其它系统/或切换系统，则要先点主界面的停止按钮
  - 若要配置多个系统，右下属性里`安装路径`的*.img换成其它名字

### 安装linux 软件
- 在电脑上或手机上安装ssh 客户端
  - 电脑用`xshell`、`git bash ssh`、 `linux/osx` 自带的ssh
  - 安桌下载 `JuiceSSH`
  - 在安卓设备上wifi设置里查看ip
  - 用ssh客户端连接 ip:22 用户名/密码为在配置文件设置的
    - 若登陆不了，用户名试试 android
- 以安装的ubuntu为例
- `apt install bash-completion screenfetch htop vim supervisor aria2`
- 执行 `sudo systemctl enable supervisor`设置自动启动supervisor
  - 若出现问题则执行`/lib/systemd/systemd-sysv-install enable supervisor`
  - 如果重启`linux deploy`没自动启动supervisor则手工执行`sudo supervisord`

  ### 使用示例


  - 执行 `screenfetch`打印系统信息

  ![](https://dl.ystyle.top/qiniu//201717300131-3.png)

- 用htop查看系统负载信息

  ![](https://dl.ystyle.top/qiniu//201717300130-p.png)

- 配置aria2 下载器
```shell
sudo mkdir /etc/aria2    #新建文件夹  
sudo touch /etc/aria2/aria2.session    #新建session文件
sudo chmod 777 /etc/aria2/aria2.session    #设置aria2.session可写
sudo vim /etc/aria2/aria2.conf    #创建配置文件
```

  - aria2.conf文件配置


```conf
## '#'开头为注释内容, 选项都有相应的注释说明, 根据需要修改 ##
## 被注释的选项填写的是默认值, 建议在需要修改时再取消注释  ##

## 基本选项 ##

# 文件的保存路径(可使用绝对路径或相对路径), 默认: 当前启动位置
dir=~/downloads
# 启用磁盘缓存, 0为禁用缓存, 需1.16以上版本, 默认:16M
disk-cache=32M
# 文件预分配方式, 能有效降低磁盘碎片, 默认:prealloc
# 预分配所需时间: none < falloc ? trunc < prealloc
# falloc和trunc则需要文件系统和内核支持
# NTFS建议使用falloc, EXT3/4建议trunc, MAC 下需要注释此项
file-allocation=none
# 断点续传，目前只支持 HTTP/HTTPS/FTP 协议
continue=true
#检查文件完整性，默认：false
check-intergrity=false
#帮助信息分类
#一个标签以#开头
#可用标签: #basic, #advanced, #http, #https, #ftp, #metalink, #bittorrent, #cookie, #hook, #file, #rpc, #checksum, #experimental, #deprecated, #help, #all Default: #basic
#默认为#basic
help=#basic

## 下载连接相关 ##

# 最大同时下载任务数, 运行时可修改, 默认:5
max-concurrent-downloads=1
# 同一服务器连接数, 添加时可指定, 默认:1
max-connection-per-server=5
# 最小文件分片大小, 添加时可指定, 取值范围1M -1024M, 默认:20M
# 假定size=10M, 文件为20MiB 则使用两个来源下载; 文件为15MiB 则使用一个来源下载
min-split-size=10M
# 单个任务最大线程数, 添加时可指定, 默认:5
split=5
# 整体下载速度限制, 运行时可修改, 默认:0
#max-overall-download-limit=0
# 单个任务下载速度限制, 默认:0
#max-download-limit=0
# 整体上传速度限制, 运行时可修改, 默认:0
#max-overall-upload-limit=0
# 单个任务上传速度限制, 默认:0
#max-upload-limit=0
# 禁用IPv6, 默认:false
disable-ipv6=true

## 进度保存相关 ##

# 从会话文件中读取下载任务
input-file=/etc/aria2/aria2.session
# 在Aria2退出时保存`错误/未完成`的下载任务到会话文件
save-session=/etc/aria2/aria2.session
# 定时保存会话, 0为退出时才保存, 需1.16.1以上版本, 默认:0
#save-session-interval=60

## RPC相关设置 ##

# 启用RPC, 默认:false
enable-rpc=true
# 允许所有来源, 默认:false
rpc-allow-origin-all=true
# 允许非外部访问, 默认:false
rpc-listen-all=true
# 事件轮询方式, 取值:[epoll, kqueue, port, poll, select], 不同系统默认值不同
#event-poll=select
# RPC监听端口, 端口被占用时可以修改, 默认:6800
#rpc-listen-port=6800
# 设置的RPC授权令牌, v1.18.4新增功能, 取代 --rpc-user 和 --rpc-passwd 选项
#rpc-secret=<TOKEN>
# 设置的RPC访问用户名, 此选项新版已废弃, 建议改用 --rpc-secret 选项
#rpc-user=<USER>
# 设置的RPC访问密码, 此选项新版已废弃, 建议改用 --rpc-secret 选项
#rpc-passwd=<PASSWD>

## BT/PT下载相关 ##

# 当下载的是一个种子(以.torrent结尾)时, 自动开始BT任务, 默认:true
#follow-torrent=true
# BT监听端口, 当端口被屏蔽时使用, 默认:6881-6999
listen-port=51413
# 单个种子最大连接数, 默认:55
#bt-max-peers=55
# 打开DHT功能, PT需要禁用, 默认:true
enable-dht=false
# 打开IPv6 DHT功能, PT需要禁用
#enable-dht6=false
# DHT网络监听端口, 默认:6881-6999
#dht-listen-port=6881-6999
# 本地节点查找, PT需要禁用, 默认:false
#bt-enable-lpd=false
# 种子交换, PT需要禁用, 默认:true
enable-peer-exchange=false
# 每个种子限速, 对少种的PT很有用, 默认:50K
#bt-request-peer-speed-limit=50K
# 客户端伪装, PT需要
peer-id-prefix=-TR2770-
user-agent=Transmission/2.77
# 当种子的分享率达到这个数时, 自动停止做种, 0为一直做种, 默认:1.0
seed-ratio=0
# 强制保存会话, 话即使任务已经完成, 默认:false
# 较新的版本开启后会在任务完成后依然保留.aria2文件
#force-save=false
# BT校验相关, 默认:true
#bt-hash-check-seed=true
# 继续之前的BT任务时, 无需再次校验, 默认:false
bt-seed-unverified=true
# 保存磁力链接元数据为种子文件(.torrent文件), 默认:false
bt-save-metadata=true
```
  - 配置aria2守护进程
    - `vim /etc/supervisor/conf.d/aria2.conf`
    ```conf
    [program:aria2]
    command=aria2c --conf-path=/etc/aria2/aria2.conf
    autostart=true
    autorestart=true
    startsecs=10
    directory=/etc/aria2
    ```
    - `sudo supervisorctl reload`
    - `sudo vim /etc/supervisor/supervisord.conf` 修改`[inet_http_server]`节点为以下内容，`sudo supervisorctl reload` 重载配置, 然后访问 `ip:9001` 可以管理重启/停止 aria2 进程
    ```conf
    [inet_http_server]
    port=0.0.0.0:9001
    username=user
    password=123456
    ```
    - 进入[http://webui-aria2.ghostry.cn/] `设置-连接设置` 配置rpc地址为： `ip:6800`
    - 点`添加-使用连接`可以下载文件，`使用metelink`可以下载磁力链, `使用种子可以下载` 种子

- 安装syncthing同步工具
  - [官方下载地址](https://github.com/syncthing/syncthing/releases/latest) 下载 `syncthing-linux-arm-vx.xx.xx-.tar.gz` arm版本的
  - 示例：右键复制地址 `wget https://github.com/syncthing/syncthing/releases/download/v0.14.40/syncthing-linux-arm-v0.14.40.tar.gz` 下载，建议下载最新版
  - 解压 `tar -czf syncthing-linux-arm-v0.14.40.tar.gz`
  - `cd syncthing-linux-arm-v0.14.40 && cp syncthing /usr/bin/syncthing`
  - 运行 syncthing 启动完成后按`ctrl +  c`结束掉
  - `vim cat /etc/supervisor/conf.d/syncthing.conf` 配置syncthing守护进程, 建议把以下配置的`syncthing`目录或用户名换成自己配置的用户
  ```conf
  [program:syncthing]
  command = syncthing -no-browser -home="/home/syncthing/.config/syncthing"
  directory = /home/syncthing/
  autorestart = True
  user = syncthing
  environment = STNORESTART="1", HOME="/home/syncthing"
  ```
 - 执行`vim /home/syncthing/.config/syncthing/config.xml` 找到以下内容，把[address]中的地址改为0.0.0.0
   ```xml
   <gui enabled="true" tls="false" debugging="false">
      <address>0.0.0.0:8384</address>
      <user>ystyle</user>
      <password>$2a$10$ZhHTlk3OwM2s7hbFigI/quti97wNT0Y3fpciNE3ngIkJYVmLcyw76</password>
      <apikey>SvgmE6D6i2hNzX6WGh5ZKnDNi6KriMqS</apikey>
      <theme>dark</theme>
  </gui>
   ```
   - `sudo supervisorctl reload` 重载配置，
   - 访问 http://127.0.0.1:8384/ 可以管理同步设备与目录
     - 第一次访问需要设置用户名和密码，会有提示
     - 右上设置-显示id 可以复制添加到其它设备的syncthing【远程设备】中，两设备的目录可以互相同步
     - 简单的使用技巧： aria2 下载文件，syncthing 同步下载目录到 pc, pc同步完成后剪切到其它目录，安卓上的会同步删除
