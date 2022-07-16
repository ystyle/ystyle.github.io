---
title: Linux kde文件管理器连接华为Share
date: 2020-09-03 10:46:26
updated: 2020-09-03 10:46:26
tags:
- linux
- kde
- 华为Share
- Samba
categories: 软件
permalink: kde-dolphin-smb
---

### 华为手机设置 
- 打开华为Share
- 长按华为Share图标进入华为分享
- 打开共享至电脑选项

### Linux 设置 
- 检查文件夹没有就创建一个
```shell
mkdir ~/.smb
vim ~/.smb/smb.conf
```
- 然后在文件填写
```ini
[global]
client min protocol = NT1
```
- 打开Dolphin
- 选择网络在文件管理地址栏填写手机ip: `smb://192.168.3.129`  回车
- 在弹窗填写用户名和密码
- 右键添加到标签(下次直接在标签点击就能访问了)

![访问华为Share](https://dll.ystyle.top/images/2020-09/2020-09-03_14-33.png)
![修改标签名称](https://dll.ystyle.top/images/2020-09/2020-09-03_14-31.png)
