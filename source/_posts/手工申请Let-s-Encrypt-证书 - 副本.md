---
title: "手工申请Let's Encrypt 证书"
date: 2018-05-11 11:30:48
tags:
- ssl
- https
categories: 系统
permalink: apply-lets-encrypt-by-manual
---

>本教程讲如何手工申请证书，并提取出来， 因为有些软件并不能直接使用官方提供的脚本，如堡垒机的防火墙软件

### 安装letsencrypt
```shell
git clone https://github.com/letsencrypt/letsencrypt
cd letsencrypt
./letsencrypt-auto --help
```

### 申请证书
```
./letsencrypt-auto certonly --manual --email lxy5266@live.com -d web.ystyle.top
```

出现以下内容时，打开一个新的终端

```
Saving debug log to /var/log/letsencrypt/letsencrypt.log
Plugins selected: Authenticator manual, Installer None
Obtaining a new certificate
Performing the following challenges:
http-01 challenge for web.ystyle.top

-------------------------------------------------------------------------------
NOTE: The IP of this machine will be publicly logged as having requested this
certificate. If you're running certbot in manual mode on a machine that is not
your server, please ensure you're okay with that.

Are you OK with your IP being logged?
-------------------------------------------------------------------------------
(Y)es/(N)o: Y

-------------------------------------------------------------------------------
Create a file containing just this data:

tzhL9xuoqMj4F57SMCiTvEpno36QM0nlAFwo8SDuHvk.2lxeywshhzsj142WeXRomKhAOmOFM5Iwlkbc5z1jljc

And make it available on your web server at this URL:

http://web.ystyle.top/.well-known/acme-challenge/tzhL9xuoqMj4F57SMCiTvEpno36QM0nlAFwo8SDuHvk

-------------------------------------------------------------------------------
Press Enter to Continue
```

```shell
mkdir -p /tmp/letsencrypt/public_html/.well-known/acme-challenge
cd /tmp/letsencrypt/public_html
printf "%s" tzhL9xuoqMj4F57SMCiTvEpno36QM0nlAFwo8SDuHvk.2lxeywshhzsj142WeXRomKhAOmOFM5Iwlkbc5z1jljc > .well-known/acme-challenge/tzhL9xuoqMj4F57SMCiTvEpno36QM0nlAFwo8SDuHvk
# echo 中的 tzhL9xuoqMj4F57SMCiTvEpno36QM0nlAFwo8SDuHvk.2lxeywshhzsj142WeXRomKhAOmOFM5Iwlkbc5z1jljc 是Create a file containing just this data: 下面那行
# .well-known/acme-challenge/tzhL9xuoqMj4F57SMCiTvEpno36QM0nlAFwo8SDuHvk 是 And make it available on your web server at this URL: 下面那行的url中的
```

然后执行

```shell
sudo python -c \
"import BaseHTTPServer, SimpleHTTPServer; \
s = BaseHTTPServer.HTTPServer(('', 80), SimpleHTTPServer.SimpleHTTPRequestHandler); \
s.serve_forever()"
```
>注意机器的80端口要先关闭

返回之前的窗口按回车，如果证书成功创建，会出现下面的提示：
 - Congratulations! Your certificate and chain have been saved at ...

然后在`/etc/letsencrypt/archive/`目录就能看到申请域名的证书了， 查看把[privkey.pem转成pkcs1格式](./Lets-Encrypt-convert-to-pkcs1)
