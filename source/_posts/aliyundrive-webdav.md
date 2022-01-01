---
title: 阿里云网盘映射本地硬盘
date: 2021-01-01 22:46:26
updated: 2021-01-01 22:46:26
tags:
- 阿里云网盘
- webdav
categories: 软件
permalink: aliyundrive-webdav
---

### 下载aliyundrive-webdav
- 下载地址: [https://github.com/messense/aliyundrive-webdav/releases/latest](https://github.com/messense/aliyundrive-webdav/releases/latest)
- 解压并放在一个目录里
  ![](https://dl.ystyle.top/images/2022-01/explorer_2022-01-01_23-16-55.png)
  
### 准备脚本
>把以下内容存为run.ps1

```powershell
$env:REFRESH_TOKEN="484b469b3ef74dcaba5cf21aeadae2ca"
$env:WEBDAV_AUTH_USER="admin"
$env:WEBDAV_AUTH_PASSWORD="123456"
Start-Process -FilePath aliyundrive-webdav.exe -ArgumentList ("--port=8080") -Wait -WindowStyle Hidden
```

脚本配置说明:

- `$env:REFRESH_TOKEN`: 为阿里云网盘登陆后的token
  - [获取阿里云网盘REFRESH_TOKEN的方法](https://github.com/messense/aliyundrive-webdav#%E8%8E%B7%E5%8F%96-refresh_token)
- `$env:WEBDAV_AUTH_USER`： webdav用户名
- `$env:WEBDAV_AUTH_PASSWORD`: webdav密码
- `--port=8080` 为webdav的访问端口，被占用时可以换成其它的

![](https://dl.ystyle.top/images/2022-01/kate_2022-01-01_23-18-47.png)

### 设计开机启动
- `win + s`搜索`任务计划程序`打开
- 在打开界面选择`任务计划程序库`
- 在右边点创建基本任务，输入名字: `aliyundrive-webdav` (名字可以随意写)
  ![](https://dl.ystyle.top/images/2022-01/mmc_2022-01-01_23-12-57.png
- 下一步选择: 计算机启动时
  ![](https://dl.ystyle.top/images/2022-01/mmc_2022-01-01_23-13-35.png
- 下一步选择: 启动程序
  - 下一步： 在【程序或者脚本】写: `powershell.exe`
  - 在【添加参数】填写: -WindowStyle Hidden -file run.ps1
  - 在【起始于】填写：存放`run.ps1`和 `aliyundrive-webdav`的目录
  ![](https://dl.ystyle.top/images/2022-01/mmc_2022-01-01_23-13-52.png)
  ![](https://dl.ystyle.top/images/2022-01/chrome_2022-01-01_23-15-31.png
- 下一步点击：完成
  ![](https://dl.ystyle.top/images/2022-01/mmc_2022-01-01_23-16-10.png)
- 启动服务: 在服务列表选择`aliyundrive-webdav`并在右边选项里选择启动
  ![](https://dl.ystyle.top/images/2022-01/mmc_2022-01-01_23-20-07.png)

### 映射本地硬盘
- 打开文件管理器，在此电脑右键-选择映射网络驱动器
  ![](https://dl.ystyle.top/images/2022-01/explorer_2022-01-01_23-22-35.png)
- 在弹窗选择一个盘符，并在文件夹填写: `http://127.0.0.1:8080`, 点完成，在弹窗输入用户名和密码
  ![](https://dl.ystyle.top/images/2022-01/explorer_2022-01-01_23-23-39.png)
  ![](https://dl.ystyle.top/images/2022-01/chrome_2022-01-01_23-25-44.png)
  ![](https://dl.ystyle.top/images/2022-01/explorer_2022-01-01_23-25-13.png)
  
