---
title: Docker 搭建redis 集群
tags:
  - redis
  - docker
categories: 系统
id: 25
updated: '2015-11-09 20:48:43'
date: 2015-10-20 15:47:13
---

## Docker 搭建redis 集群
### 准备工作
创建一个目录用保存redis-slave的配置文件
```shell
mkdir/data/docker/redis/
wget https://raw.githubusercontent.com/antirez/redis/3.0/redis.conf \
-O /data/docker/redis/redis.conf
```
### 安装redis
```shell
docker pull redis
```

### 修改redis-slave配置文件
```shell
# 修改 /data/docker/redis/redis.conf 的slaveof属性为redis-master 6379
cd /data/docker/redis/
sed -i 's/# slaveof <masterip> <masterport>/slaveof redis-master 6379/g' redis.conf
```

### 启动服务
启动`redis-master`、 `redis-slave1`、 `redis-slave2`、 `redis-slave3`
```
docker run --name redis-master -p 6379:6379 -d redis

docker run --link redis-master:redis-master -v /data/docker/redis/redis.conf:/usr/local/etc/redis/redis.conf --name redis-slave1 -d redis redis-server /usr/local/etc/redis/redis.conf

docker run --link redis-master:redis-master -v /data/docker/redis/redis.conf:/usr/local/etc/redis/redis.conf --name redis-slave2 -d redis redis-server /usr/local/etc/redis/redis.conf

docker run --link redis-master:redis-master -v /data/docker/redis/redis.conf:/usr/local/etc/redis/redis.conf --name redis-slave3 -d redis redis-server /usr/local/etc/redis/redis.conf
```

### 测试
用本地的redis-cli 连接到 master
```
redis-cli
127.0.0.1:6379> info # 查看详细信息
```
