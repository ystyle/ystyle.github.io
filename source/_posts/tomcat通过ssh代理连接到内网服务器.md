---
title: tomcat通过ssh代理连接到内网数据库服务器
date: 2017-05-26 12:58:54
tags:
  - ssh
  - 代理
  - tomcat
  - java
categories: 系统
permalink: tomcat-through-ssh-proxy-connected-to-the-internal-network
---

>项目的测试数据库服务器是在某内网的，
>现在要通过ssh的代理隧道，连接到内网的数据库


### 解决方法：
- 用xshell连接到ssh服务器
- 打开查看-隧道窗体
- 新建转移规则
  - 类型： Local(Outgoing)
  - 源主机： localhost(自己开发电脑的ip)
  - 侦听端口： 1521
  - 目标主机： 192.168.101.102(ssh的局域网ip都可以)
  - 目标端口： 1521
- 这一步linux可以直接执行：`ssh -L 1521:192.168.101.102:1521 sshserverip` -L代表本地转移到远程
- java的数据库连接配置改`jdbc:oracle:thin:@localhost:1521:orcl`
- 启动项目连接成功
