---
title: 开源鸿蒙网络和hdc连接方法
tags:
  - 鸿蒙
categories: 系统
permalink: openharmonyos-hdc-and-network
date: 2021-06-06 18:10:13
---

### hdc下载
- 如果下载了源码，可以在源码目录找到: developtools/hdc_standard/prebuilt/windows/hdc_std.exe
- 远程仓库地址： https://gitee.com/openharmony/developtools_hdc_standard
- hdc使用手册: https://gitee.com/openharmony/docs/blob/master/zh-cn/device-dev/subsystems/hdc_std-%E4%BD%BF%E7%94%A8%E6%8C%87%E5%AF%BC.md


### 通过usb连接鸿蒙
- 通过hi3516背面的type-c口连接电脑, 目前只有这口能传数据， 底下的口不行
  - 如果成功，可以在电脑 `设备管理-用串行总线设备`下面看到`HDC Device`
- 打开终端， 输入`hdc list targets`列出设备

![](https://dl.ystyle.top/images/2021-06/mmc_2021-06-07_19-52-37.png)
![](https://dl.ystyle.top/images/2021-06/WindowsTerminal_2021-06-07_19-53-25.png)

### 鸿蒙连接本地有线网络
- 插入有线网线
- 在hitool串口中连接上hi3516后执行
  - `/system/xbin/su` 获取root权限
  - `ifconfig eth0 192.168.3.197 netmask 255.255.255.0` 网络IP要换成自己的网段

![](https://dl.ystyle.top/images/2021-06/HiTool_2021-06-06_18-29-05.png)

### 用hdc通过tcp连接鸿蒙
- 在连接hitool串口后执行`hdcd -t`
- 在自己电脑主机上打开终端执行 `hdc tconn 192.168.3.197:10178` 显示 `Connect OK` 就表示连接上了
  - 执行`hdc list targets -v` 显示设备
  - 执行`hdc -t 192.168.3.197:10178 shell` 连接鸿蒙系统的shell， 注： 要用-t指定连接的ip:端口
  - 执行`hdc -t 192.168.3.197:10178 file send localfile remotefile` 发送文件
  - 只有tcp连接才需要`-t ip:port`
  - 其实命令请查看使用手册

![](https://dl.ystyle.top/images/2021-06/HiTool_2021-06-06_18-19-47.png)
![](https://dl.ystyle.top/images/2021-06/WindowsTerminal_2021-06-06_18-30-29.png)
