---
title: docker 1.12 的服务自动发现
permalink: docker-1-12-de-fu-wu-zi-dong-fa-xian
id: 37
updated: '2016-09-03 23:12:03'
date: 2016-09-03 02:26:07
tags: docker
categories: 系统
---

### 介绍
>docker 1.12 的swarm 集群的自动发现有两种方式, virtual IP address (VIP) 与 DNS round-robin, 本文使用的是VIP的方式

### 准备
1. 安装docker 1.12 以上版本
1. 初始化swarm集群
3. 创建一个名为`docker-net` 的overlay网络
4. 开放`7946 TCP/UDP` , `4789 UDP` 端口
>初始化swarm集群部份可看我之前的博客[使用docker 1.12 搭建多主机docker swarm集群](http://www.lxy520.net/2016/07/02/shi-yong-docker-1-12-da-jian-duo-zhu-ji-docker-swarmji-qun/)


### 创建overlay网络
查看当前的网络
```shell
[root@swarm-manager ~]# docker network ls
NETWORK ID          NAME                DRIVER              SCOPE
376f5b337bfc        bridge              bridge              local                                    
166bd71f7d0e        host                host                local               
9gr6bfff1rv9        ingress             overlay             swarm               
```
> `ingress` 也是一个overlay网络, 可以跨主机通信, 本教程会创建一个新的

创建网络
```shell
docker network create \
  --driver overlay \
  --opt encrypted \ ## 是否使用加密
  my-network
```
查看
```shell
[root@swarm-manager ~]# docker network ls
NETWORK ID          NAME                DRIVER              SCOPE
376f5b337bfc        bridge              bridge              local                                    
166bd71f7d0e        host                host                local               
9gr6bfff1rv9        ingress             overlay             swarm       
aoqs3p835s5g        docker-net          overlay             swarm        
```

### 在swarm上用overlay 网络创建一个服务
```shell
docker service create \
  --replicas 3 \
  --name my-web \ # 服务名为my-web
  --network docker-net \
  daocloud.io/nginx:alpine # 使用国内的镜像, alpine版的体积很小,下载会快点
```
查看服务
```shell
# 本次只起了一个manager节点, 所以容器都跑在这台机器上了
[root@swarm-manager ~]# docker service ps my-web
ID                         NAME          IMAGE                     NODE           DESIRED STATE  CURRENT STATE            ERROR
bavjn0xhxi35nx6n9kn33yfga  my-web.1      daocloud.io/nginx:alpine  swarm-manager  Running        Running 31 minutes ago   
cibuo8zqp78z1xb8cu3v4pkmj  my-web.2      daocloud.io/nginx:alpine  swarm-manager  Running        Running 31 minutes ago   
0pkg1eoa0onku71cbp1hqtcv5  my-web.3      daocloud.io/nginx:alpine  swarm-manager  Running        Running 31 minutes ago   
```

在一个网络上有哪些容器可以在network inspect的Containers节点看到
```
[root@swarm-manager ~]# docker network inspect docker-net
[
    {
        "Name": "docker-net",
        "Id": "aoqs3p835s5glx69hi46ou2dw",
        ....
        "Containers": {
            "1c87aae81449b448983924017fc4037b7b1e9e1eaa03bc55745b0167ab4e495b": {
                "Name": "my-web.1.bavjn0xhxi35nx6n9kn33yfga",
                "EndpointID": "2ab6c7e698ce69ec318a211dd0386533de1a0d8f2070bd4ee6cdc43cb94dcd0a",
                "MacAddress": "02:42:0a:00:09:03",
                "IPv4Address": "10.0.9.3/24",
                "IPv6Address": ""
            },
            .....
        },
        .....
    }
]

```

查看服务使用的vip
```shell
[root@swarm-manager ~]#  docker service inspect --format='{{.Endpoint.VirtualIPs}}'   my-web
[{aoqs3p835s5glx69hi46ou2dw 10.0.9.2/24}]
```

### 演示使用服务名访问nginx
先创建一个同样使用docker-net的overlay网络 的服务

```shell
docker service create \
  --name my-busybox \
  --network docker-net \
  busybox \
  sleep 3000
```

等待服务启动后, 用docker exec 连接进busybox的容器里

```shell
[root@swarm-manager ~]# docker service ps my-busybox
ID                         NAME              IMAGE    NODE           DESIRED STATE  CURRENT STATE                ERROR
7ftv4wj1g3vu8g7mfghx8du65  my-busybox.1      busybox  swarm-manager  Running        Running about a minute ago   
[root@swarm-manager ~]# docker exec -ti my-busybox.1.7ftv4wj1g3vu8g7mfghx8du65 sh
```

在busybox容器. 向DNS查询nginx服务的vip
```shell
[root@swarm-manager ~]# docker exec -ti my-busybox.1.7ftv4wj1g3vu8g7mfghx8du65 sh
/ # nslookup my-web
Server:    127.0.0.11
Address 1: 127.0.0.11

Name:      my-web
Address 1: 10.0.9.2 10.0.9.2 # 和在外面看到的一样
```
在busybox容器. 向DNS查询nginx服务所有容器的ip地址
```shell
/ # nslookup tasks.my-web
Server:    127.0.0.11
Address 1: 127.0.0.11

Name:      tasks.my-web
Address 1: 10.0.9.5 my-web.3.0pkg1eoa0onku71cbp1hqtcv5.docker-net
Address 2: 10.0.9.4 my-web.2.cibuo8zqp78z1xb8cu3v4pkmj.docker-net
Address 3: 10.0.9.3 my-web.1.bavjn0xhxi35nx6n9kn33yfga.docker-net
```

在busybox容器, 通过服务名访问nginx
```shell
/ # wget -O- my-web
Connecting to my-web (10.0.9.2:80)
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
<style>
    body {
        width: 35em;
        margin: 0 auto;
        font-family: Tahoma, Verdana, Arial, sans-serif;
    }
</style>
</head>
<body>
<h1>Welcome to nginx!</h1>
<p>If you see this page, the nginx web server is successfully installed and
working. Further configuration is required.</p>
.....
```
### 结语
通过实验可以看出, 在swarm集群中使用overlay网络时, 不同服务之间可以使用服务名(docker service name)互相访问
