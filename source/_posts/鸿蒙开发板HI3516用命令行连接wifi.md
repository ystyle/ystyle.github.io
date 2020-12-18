---
title: 鸿蒙开发板HI3516用命令行连接wifi
tags:
  - 鸿蒙
  - wifi
categories: 系统
permalink: hi3516-connect-wifi
id: 21
updated: '2020-12-18 20:11:48'
date: 2020-12-18 20:11:48
---

>鸿蒙的HI3516编译里已经有wpa_supplicant相关工程了，但编译时没有包进去, 所以只要修改配置文件后就能编译出来了

主要修改文件: [communication/BUILD.gn#L17-18](https://gitee.com/openharmony/applications_sample_camera/blob/master/communication/BUILD.gn#L17-18) 行之间添加， 以下第2行
```gn
    features = [
       "wpa_supplicant:wpa_sample",
    ]
```

### 编译过程
```shell
docker run --rm -ti -e HARDWARE=ipcamera_hi3516dv300 -v ${PWD}/out:/OpenHarmony/out ystyle/open-harmony bash
sed -i '17a\ \ \ \ \ \ "wpa_supplicant:wpa_sample",' applications/sample/camera/communication/BUILD.gn
python build.py ${HARDWARE} -b debug
```

>然后wpa_supplicant在编译目录`/out/ipcamera_hi3516dv300/bin/`， 把wpa_supplicant复制出来就可以直接使用


### 使用方法
先创建配置文件，wpa_supplicant.conf

```text
country=GB
ctrl_interface=udp
network={
    #要连接的SSID
    ssid="example"
    #如果不需要加密就写key_mgmt=NONE
    #key_mgmt=NONE
    #如果需要加密就写这行密码
    psk="AA123456"
}
```

把wpa_supplicant和配置文件复制到hi3516， 执行以下命令连接wifi
```shell
cd /nfs/wifi
./wpa_supplicant -i wlan0 -c ./wpa_supplicant.conf
```
