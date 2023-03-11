---
title: k3s云上master+内网agent的部署方式.
date: 2023-03-11 21:02:26
updated: 2023-03-11 21:02:26
tags:
- k3s
- kubernetes
- wireguard-native
- wireguard
categories: 运维
permalink: k3s-master-in-cloud-agent-in-local-intranet
---

>公网master和内网agent使用`wireguard-native`通信， 只要在所有节点上安装了`wireguard`模块，k3s会自动处理所有通信流量

### 准备
- 在云端master开放
	- `tcp` `6443` 端口，
	- `udp` `51820` 端口
- 先在所有机器上安装`wireguard-native`， [点击查看安装命令](https://www.wireguard.com/install/)
- 如果内网有防火墙，需要开放master公网ip的`6443`和`51820`端口

### 在云上安装master
>需要替换下面的master_public_ip为master公网ip, 能正常起来一般就没问题了
```shell
export INSTALL_KAS_EXEC="--node-external-ip=master_public_ip --flannel-backend=wireguard-native --flannel-external-ip"
curl -sfL https://rancher-mirror.rancher.cn/k3s/k3s-install.sh | INSTALL_K3S_MIRROR=cn sh -
```
>INSTALL_KAS_EXEC的参数是最少的开启`wireguard-native`功能的参数

>在msater上执行`cat /var/lib/rancher/k3s/server/node-token`获取token, 等下子节点需要用

### 在内网安装agent
>我是在树苺派上安装的。  
>下面的token需要换成上一步获取的， 然后把x.x.x.x换成上面的`master_public_ip`的master公网ip

```
export TOKEN=K1004a306bd3e78de0bfb4e9a485659e847dd16be3192b5b16407f53f991dc7d7f7::server:58dcf4e6e4fd7c6023976c331d1xxxxxx
curl -sfL https://rancher-mirror.rancher.cn/k3s/k3s-install.sh | INSTALL_K3S_MIRROR=cn K3S_URL=https://x.x.x.x:6443 K3S_TOKEN=${TOKEN} sh -s - --docker --node-external-ip=x.x.x.x
```

>只需要添加`--node-external-ip`参数就能启用`wireguard-native`功能了 。 如果没加这参数，是普通的节点，公网master和内网agent就不能正常通信

### 验证方法
1. 先查看节点是否正常，不需要重启master或agent的服务，如果重启后才看到的话，可能没安装成功
	```
	 $ kubelct get node
	NAME                      STATUS   ROLES                  AGE    VERSION
	ubuntu-20.04   Ready    control-plane,master   14d    v1.25.6+k3s1
	archlinux-rpi             Ready    <none>                 156m   v1.25.6+k3s1
	```
2. 用nodeSelector分别在master和内网机器上部署nginx的deploy， 再分别创建对应的service
3. 再在其中一个deploy的pod里执行curl 另一个deploy的service名称，如果能请求到nginx默认界面，说明是通的
