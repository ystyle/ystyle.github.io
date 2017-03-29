---
title: docker + swarm 集群
tags:
  - docker
  - swarm
categories: 系统
permalink: docker-swarm-ji-qun
id: 31
updated: '2016-03-19 00:14:10'
date: 2016-03-18 23:22:51
---

### token方式

>以虚拟机方式搭建集群练练手

### 安装swarm
```shell
docker run --rm swarm create
6a2d606bb3155b4428d0dc483cff6800
```

### 创建Docker虚拟机
```shell
docker-machine.exe create -d virtualbox swarm-master
docker-machine.exe create -d virtualbox swarm-node1
docker-machine.exe create -d virtualbox swarm-node2
```

### 搭建swarm集群

创建swarm-master

```
eval $(docker-machine.exe env swarm-master)
docker run -d -p 3376:3376 -t \
-v /var/lib/boot2docker:/carts:ro swarm manage \
-H 0.0.0.0:3376 \
--tlsverify --tlscacert=/certs/ca.pem \
--tlscert=/certs/server.pem \
--tlskey=/certs/server-key.pem \
token://6a2d606bb3155b4428d0dc483cff6800

docker run -d swarm join --addr=$(docker-machine.exe ip swarm-master):2376 token://6a2d606bb3155b4428d0dc483cff6800
```

创建swarm-node

```shell
eval $(docker-machine.exe env swarm-node1)
docker run -d swarm join --addr=$(docker-machine.exe ip swarm-node1):2376 token://6a2d606bb3155b4428d0dc483cff6800

eval $(docker-machine.exe env swarm-node2)
docker run -d swarm join --addr=$(docker-machine.exe ip swarm-node2):2376 token://6a2d606bb3155b4428d0dc483cff6800

```

### 管理Swarm集群
```shell
export DOCKER_HOST=$(docker-machine ip swarm-master):3376
docker info
```
