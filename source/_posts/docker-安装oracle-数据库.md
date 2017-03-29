---
title: docker 安装oracle 数据库
tags: docker
categories: 系统
permalink: docker-install-oracle
id: 15
updated: '2015-09-24 18:12:12'
date: 2015-07-16 20:16:58
---

docker安装oracle 11G 数据库：

docker-oracle-xe-11g
============================

环境：

`Oracle Express Edition 11g Release 2 与 Ubuntu 14.04.1 LTS`

**Dockerfile**  [地址](https://registry.hub.docker.com/u/wnameless/oracle-xe-11g/) 在 [Docker中央库](https://registry.hub.docker.com/).

### 安装
```
docker pull wnameless/oracle-xe-11g
```

以22(sshd), 1521(oracle)号端口启动容器:
```
docker run -d -p 49160:22 -p 49161:1521 wnameless/oracle-xe-11g
```

数据库连接信息:
```
hostname: localhost
port: 49161
sid: xe
username: system
password: oracle
```

oracle的`SYS` 和 `SYSTEM`用户密码:
```
oracle
```

用ssh连接docker容器
```
ssh root@localhost -p 49160
password: admin
```
