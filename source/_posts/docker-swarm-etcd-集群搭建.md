---
title: docker + swarm + etcd 集群搭建
tags:
  - docker
  - swarm
  - etcd
categories: 系统
permalink: docker-swarm-etcd-ji-qun-da-jian
id: 32
updated: '2016-03-19 00:13:36'
date: 2016-03-18 23:16:21
---

## 安装Swarm集群

### 环境信息
服务器:

- 192.168.99.100 centos-node1
- 192.168.99.101 centos-node2
- 192.168.99.102 centos-node3

集群信息:

- etc服务器: 192.168.99.100:2379
- swarm manage: 192.168.99.101:3376
- swarm-node1: 192.168.99.100:2375
- swarm-node2: 192.168.99.101:2375
- swarm-node3: 192.168.99.102:2375

### 准备

- 在所有的机器上安装dokcer
- 在centos-node1 上`docker pull ystyle/etcd` (官方的下载不了,自己做了个一样的)
- 在所有机器上`dokcer pull swarm`
- 以上三步可以用`docker-machine`完成
- **开放所有机器的`2375`端口, `centos-node1`的`2379`端口,`centos-node2`的`3376`端口**

### 安装etcd `k-v`数据库
在centos-node1上执行:

```shell
# 设置当前host的ip
export HOSTIP=192.168.99.100

# 启动etcd `k-v`服务器
docker run -d -v /etc/ssl/certs:/etc/ssl/certs -p 4001:4001 -p 2380:2380 -p 2379:2379 \
 --name etcd ystyle/etcd \
 -name etcd0 \
 -advertise-client-urls http://${HOSTIP}:2379,http://${HOSTIP}:4001 \
 -listen-client-urls http://0.0.0.0:2379,http://0.0.0.0:4001 \
 -initial-advertise-peer-urls http://${HOSTIP}:2380 \
 -listen-peer-urls http://0.0.0.0:2380 \
 -initial-cluster-token etcd-cluster-1 \
 -initial-cluster etcd0=http://${HOSTIP}:2380 \
 -initial-cluster-state new
```

### 加入集群

1. 在centos-node1执行:
```shell
docker run -d swarm join --addr=192.168.99.100:2375 etcd://192.168.99.100:2379/swarm
```

2. 在centos-node2执行:
```shell
docker run -d swarm join --addr=192.168.99.101:2375 etcd://192.168.99.100:2379/swarm
```

3. 在centos-node3执行:
```shell
docker run -d swarm join --addr=192.168.99.102:2375 etcd://192.168.99.100:2379/swarm
```

### 启动swarm manage
在centos-node2上执行
```shell
# 启动swarm manage
docker run -d -p 3376:3376 -t \
 swarm manage \
-H 0.0.0.0:3376 \
etcd://192.168.99.100:2379/swarm

# 检查swarm节点列表
docker run --rm swarm list etcd://192.168.99.100:2379/swarm

# 查看swarm集群信息
export DOCKER_HOST=192.168.99.101:3376
docker info

# 测试
docker run --rm -p 8080:80 nginx:alpine
docker ps -a # 查看nginx安装到哪台机器上了

curl -L http://nginx_host:8080  
```

### 记录
1. 如果docker info 出现`Error: ID duplicated. `删掉`/etc/docker/key.json`文件(我的虚拟机是直接复制出来的)


### 参考资料
https://docs.docker.com/v1.5/swarm/discovery/#using-etcd

https://docs.docker.com/engine/userguide/networking/get-started-overlay/

https://github.com/docker/swarm

https://github.com/coreos/etcd

https://docs.docker.com/engine/installation/linux/centos/
