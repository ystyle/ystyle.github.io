---
title: 使用docker 1.12 搭建多主机docker swarm集群
tags: docker
categories: 系统
permalink: shi-yong-docker-1-12-da-jian-duo-zhu-ji-docker-swarmji-qun
id: 34
updated: '2016-09-01 20:47:15'
date: 2016-07-02 07:03:32
---

## 使用docker 1.12 搭建多主机docker swarm集群
### 准备
> 1. 准备至少两台的centos 7 主机(全新最小安装, 可以使用虚拟机安装)
1. 开放端口2377 tcp端口, 7946 4789 tcp udp 端口
> 1. 本文使用192.168.99.101(hostname:centos-node4) 作为swarm manager
1. 192.168.99.102(hostname:centos-node5) 作为swarm agent1

### 安装docker engine 1.12
在每台机器上执行以下命令
```shell
# sudo tee /etc/yum.repos.d/docker.repo <<-'EOF'
[dockerrepo]
name=Docker Repository
baseurl=https://yum.dockerproject.org/repo/main/centos/7/
enabled=1
gpgcheck=1
gpgkey=https://yum.dockerproject.org/gpg
EOF

# sudo yum install docker-engine
# sudo systemctl enable docker
# sudo systemctl start docker
```
安装完后查看docker 版本
```shell
[root@centos-node4 ~]# docker version
Client:
 Version:      1.12.0
 API version:  1.24
 Go version:   go1.6.3
 Git commit:   8eab29e
 Built:        
 OS/Arch:      linux/amd64

Server:
 Version:      1.12.0
 API version:  1.24
 Go version:   go1.6.3
 Git commit:   8eab29e
 Built:        
 OS/Arch:      linux/amd64
```
开放端口相关命令
```shell
firewall-cmd --zone=public --add-port=2377/tcp --permanent
firewall-cmd --zone=public --add-port=7946/tcp --permanent
firewall-cmd --zone=public --add-port=7946/udp --permanent
firewall-cmd --zone=public --add-port=4789/tcp --permanent
firewall-cmd --zone=public --add-port=4789/udp --permanent
firewall-cmd --reload
```


### 新版docker swarm 命令详情
有关集群的docker命令如下：

1. docker swarm：集群管理，子命令有init, join,join-token, leave, update
1. docker node：节点管理，子命令有demote, inspect,ls, promote, rm, ps, update
1. docker service：服务管理，子命令有create, inspect, ps, ls ,rm , scale, update
1. docker stack/deploy：试验特性，用于多应用部署

### 创建swarm 集群
- 查看docker swarm 命令说明

```shell
[root@centos-node4 ~]# docker swarm -h
Flag shorthand -h has been deprecated, please use --help

Usage:	docker swarm COMMAND

Manage Docker Swarm

Options:
      --help   Print usage

Commands:
  init        Initialize a swarm
  join        Join a swarm as a node and/or manager
  join-token  Manage join tokens
  update      Update the swarm
  leave       Leave a swarm

Run 'docker swarm COMMAND --help' for more information on a command.
```

- 在swarm manager(centos-node4:192.168.99.101)初始化swarm集群

用`--listen-addr`指定监听的ip与端口
```shell
#命令格式: docker swarm init --listen-addr <MANAGER-IP>:<PORT>
[root@centos-node4 ~]# docker swarm init --listen-addr 192.168.99.101:2377
Swarm initialized: current node (a60d5c3ttymvtozr46uvk17q4) is now a manager.
```
查看结果

```shell
[root@centos-node4 ~]# docker node ls
ID                           HOSTNAME      MEMBERSHIP  STATUS  AVAILABILITY  MANAGER STATUS
a60d5c3ttymvtozr46uvk17q4 *  centos-node4  Accepted    Ready   Active        Leader
```

- 把swarm-agent1(centos-node5: 192.168.99.102)添加到swarm集群

在swarm-agent1上执行:
```shell
#命令格式: docker swarm join <MANAGER-IP>:<PORT>
[root@centos-node5 ~]# docker swarm join 192.168.99.101:2377
This node joined a Swarm as a worker.
```

- 在swarm manager查看结果

```shell
[root@centos-node4 ~]# docker node ls
ID                           HOSTNAME      MEMBERSHIP  STATUS  AVAILABILITY  MANAGER STATUS
0ypcw58hjlcvr0xqbtizmau62    centos-node5  Accepted    Ready   Active
a60d5c3ttymvtozr46uvk17q4 *  centos-node4  Accepted    Ready   Active        Leader
```

### 创建一个overlay 跨主机网络
- 查看原有网络

```shell
[root@centos-node4 ~]# docker network ls
NETWORK ID          NAME                DRIVER              SCOPE
abec77415f48        bridge              bridge              local
e2fff9d572a6        docker_gwbridge     bridge              local
166bd71f7d0e        host                host                local
9gr6bfff1rv9        ingress             overlay             swarm
1d2bfc590294        none                null                local
```
>可以看到在swarm上默认已有一个名为ingress的overlay 网络,默认在swarm里使用，本文会创建一个新的

- 创建一个新的overlay网络

```shell
 [root@centos-node4 ~]# docker network create --driver overlay docker-net
aoqs3p835s5glx69hi46ou2dw
 [root@centos-node4 ~]# docker network ls
NETWORK ID          NAME                DRIVER              SCOPE
abec77415f48        bridge              bridge              local
aoqs3p835s5g        docker-net          overlay             swarm
e2fff9d572a6        docker_gwbridge     bridge              local
166bd71f7d0e        host                host                local
9gr6bfff1rv9        ingress             overlay             swarm
1d2bfc590294        none                null                local
```
> 新的网络(docker-net)已创建

### 在新的跨主机overlay 网络(docker-net)上创建应用

- 部署

用`alpine`镜像在`docker-net`网络上启动两个实例, 并编排为一组服务

```shell
[root@centos-node4 ~]# docker service create --replicas 2 --name helloworld --network=docker-net  alpine ping docker.com
5lgdq3ihiez0o7h2uegu4fgd3
```

- 查看部署结果

```shell
[root@centos-node4 ~]# docker service ls
ID            NAME        REPLICAS  IMAGE   COMMAND
5lgdq3ihiez0  helloworld  0/2       alpine  ping docker.com
[root@centos-node4 ~]# docker service tasks helloworld
ID                         NAME          SERVICE     IMAGE   LAST STATE          DESIRED STATE  NODE
eul3bus45qz3b555wekotdmo5  helloworld.1  helloworld  alpine  Running 14 seconds  Running        centos-node5
55uhq6xxcv53xlkqv2f0be9b9  helloworld.2  helloworld  alpine  Running 14 seconds  Running        centos-node4
```
> 可以看到两个实例分别运行在两个节点上

### 测试两个主机的网络是否能互通
- 分别查看两个实例的名称

```shell
# 在swarm-manager 上执行
[root@centos-node4 ~]# docker ps -a
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS                    PORTS               NAMES
f4a197abdb0b        alpine:latest       "ping docker.com"        42 minutes ago      Up 42 minutes                                 helloworld.2.55uhq6xxcv53xlkqv2f0be9b9

# 在swarm-agnet1 上执行
[root@centos-node5 ~]# docker ps -a
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
39cc35cd54b5        alpine:latest       "ping docker.com"   50 seconds ago      Up 49 seconds                           helloworld.1.eul3bus45qz3b555wekotdmo5
```

- 在swarm-manager 上测试

```shell
[root@centos-node4 ~]# docker exec -ti helloworld.2.55uhq6xxcv53xlkqv2f0be9b9 sh
/ # ping helloworld.1.eul3bus45qz3b555wekotdmo5
PING helloworld.1.eul3bus45qz3b555wekotdmo5 (10.0.9.3): 56 data bytes
64 bytes from 10.0.9.3: seq=0 ttl=64 time=0.514 ms
64 bytes from 10.0.9.3: seq=1 ttl=64 time=0.508 ms
64 bytes from 10.0.9.3: seq=2 ttl=64 time=0.381 ms
64 bytes from 10.0.9.3: seq=3 ttl=64 time=0.408 ms
^C
--- helloworld.1.eul3bus45qz3b555wekotdmo5 ping statistics ---
4 packets transmitted, 4 packets received, 0% packet loss
round-trip min/avg/max = 0.381/0.452/0.514 ms

```

- 在swarm-agent1 上测试

```shell
[root@centos-node5 ~]# docker ps -a
CONTAINER ID        IMAGE               COMMAND             CREATED             STATUS              PORTS               NAMES
39cc35cd54b5        alpine:latest       "ping docker.com"   50 seconds ago      Up 49 seconds                           helloworld.1.eul3bus45qz3b555wekotdmo5
[root@centos-node5 ~]# docker exec -ti  helloworld.1.eul3bus45qz3b555wekotdmo5 sh
/ # ping helloworld.2.55uhq6xxcv53xlkqv2f0be9b9
PING helloworld.2.55uhq6xxcv53xlkqv2f0be9b9 (10.0.9.4): 56 data bytes
64 bytes from 10.0.9.4: seq=0 ttl=64 time=0.892 ms
64 bytes from 10.0.9.4: seq=1 ttl=64 time=0.463 ms
64 bytes from 10.0.9.4: seq=2 ttl=64 time=0.462 ms
64 bytes from 10.0.9.4: seq=3 ttl=64 time=0.478 ms
64 bytes from 10.0.9.4: seq=4 ttl=64 time=0.468 ms
64 bytes from 10.0.9.4: seq=5 ttl=64 time=0.459 ms
^C
--- helloworld.2.55uhq6xxcv53xlkqv2f0be9b9 ping statistics ---
6 packets transmitted, 6 packets received, 0% packet loss
round-trip min/avg/max = 0.459/0.537/0.892 ms
```

> 现在新版的docker swarm 管理非常简单, 可以快速的搭建起一个跨主机的集群并部署应用

### dokcer swarm自带的负载均衡
创建一组服务
```shell
docker service create --replicas 2 --name whoami -p 8080:80 daocloud.io/nginx:alpine
```

访问服务(可以多执行几次)
```shell
# 访问地址格式: swarm-manager.ip + (-p映射的端口)
curl -v 192.168.99.101:8080
```

然后用docker logs 查看容器中nginx的访问日志, 可以现两个容器都有访问记录
