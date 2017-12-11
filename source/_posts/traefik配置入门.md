---
title: traefik配置入门
date: 2017-12-08 14:46:26
tags:
- traefik
- linux
categories: 系统
permalink: traefik-getting-start
---

### 添加 /etc/traefik/traefik.toml 配置文件
>traefik会在/etc/traefik 、 $HOME/.traefik/ 或 当前目录查找 traefik.toml 文件。
>所以本文的配置文件都放`/etc/traefik`下面

```toml
logLevel = "WARN"
# 同时支持http和https
defaultEntryPoints = ["http", "https"]
[entryPoints]
  [entryPoints.http]
  address = ":80"
    [entryPoints.http.redirect]
      entryPoint = "https"
  [entryPoints.https]
  address = ":443"
    [entryPoints.https.tls]

# 配置自动Let's Encrypt证书
[acme]
email = "yourname@mail.com"
storage = "/etc/traefik/acme.json"
entryPoint = "https"
onDemand = true

# 开启日志功能
[accessLog]
filePath = "/var/log/traefik/acceslog.txt"

[traefikLog]
filePath = "/var/log/traefik/traefik.log"

# 开启web管理端
[web]
address = ":8080"
readOnly = true
[web.auth.basic]
users = ["test:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/"] #test/test 登陆名/密码 可用openssl生成

# 使用文件盏方式
[file]
directory = "/etc/traefik/rules" # 在指定目录查找配置文件
watch = true
```

### 示例：traefik后台配置域名访问
>编辑`/etc/traefik/rules/traefikadmin.toml`文件

```toml
[backends]
  [backends.traefikadmin]
    [backends.traefikadmin.servers.server1]
    url = "http://localhost:8080"
    weight = 10

[frontends]
  [frontends.traefikadmin]
  backend = "traefikadmin"
    [frontends.traefikadmin.routes.rule_1]
    rule = "Host:traefik.ystyle.top"
```

### 示例：syncthing配置域名访问
>编辑`/etc/traefik/rules/syncthing.toml`文件

```toml
[backends]
  [backends.syncthing]
    [backends.syncthing.servers.server1]
    url = "http://localhost:8384"
    weight = 10

[frontends]
  [frontends.syncthing]
  backend = "syncthing"
    [frontends.syncthing.routes.rule_1]
    rule = "Host:syncthing.ystyle.top"
```
