---
title: VBox虚拟机安装Remix OS
tags:
  - vbox
  - RemixOS
categories: 系统
permalink: vboxxu-ni-ji-an-zhuang-remix-os
id: 30
updated: '2016-08-26 10:14:01'
date: 2016-03-04 23:59:42
---

## VBox虚拟机安装Remix OS

### 下载
[下载Remix](http://www.jide.com/remixos-for-pc#downloadNow)

### 创建虚拟机
选择64位的

![](/images/2016/03/1.png)

内存1G以上

![](/images/2016/03/2.png)

![](/images/2016/03/3.png)

一定要VHD的vdi的启动时会卡在命令行界面

![](/images/2016/03/4.png)

硬盘看着给

![](/images/2016/03/5-1.png)

创建要虚拟机里在设置里把显存调成最大,并启用3D加速

![](/images/2016/03/6.png)

在光盘里添加linux的安装镜像

![](/images/2016/03/7.png)

然后选中控制器IDE再新增一个光驱, 选择留空

![](/images/2016/03/8.png)

### 安装RemixOS
启动虚拟机

![](/images/2016/03/9.png)

用lsblk查看添加的硬盘名称是什么, 一般是sda, 然后运行cfdisk (图片的A是截图不小心按到的)

```shell
lsblk
cfdisk
```
![](/images/2016/03/10.png)

进来用左右键选择`New`然后回车, 再选择`Write`回车输入`yes`回车, 然后再选择`Qite`退出

![](/images/2016/03/11.png)

然后格式化分区, 执行`mkfs.ext4 /dev/sda1` (忘记截图了)

在虚拟机菜单分配光盘, 在没有选择iso的那个添加Remix的镜像

![](/images/2016/03/12.png)

接下来挂载分区

```shell
# 新建目录以挂载iso和虚拟硬盘
mkdir /mnt/remix
mkdir /mnt/cdrom
lsblk ## 用lsblk 可看SIZE列为2.5G的NAME字段是sr1,所以/dev/sr1就是Remix的ios镜像 (查看下图)
# 挂载镜像和目录
mount /dev/sda1 /mnt/remix
mount /dev/sr1 /mnt/cdrom

## 如果上面完成了， 接下来直接复制下面的命令执行就行了。
## 目的是拷贝iso里的文件到虚拟机的硬盘里。
## 拷贝这些文件到虚拟硬盘
cp /mnt/cdrom/system.img /mnt/remix
cp /mnt/cdrom/initrd.img /mnt/remix
cp /mnt/cdrom/ramdisk.img /mnt/remix
cp /mnt/cdrom/kernel /mnt/remix

## 创建data分区（其实就是虚拟机硬盘的一个目录，不是分区）
cd /mnt/remix/
mkdir data
chmod 777 -R /mnt/remix/data
```

![](/images/2016/03/13.png)

安装grub引导

```
grub-install --root-directory=/mnt/remix /dev/sda
# 新建grub.cfg文件, 添加启动项
vim /mnt/remix/boot/grub/grub.cfg
```

文本如下

```
set default=0
set timeout=3
set gfxmode=1024x768
terminal_output gfxterm

menuentry 'Remix OS For PC' --class android-x86 {
        search --file --no-floppy --set=root /kernel
        linux /kernel root=/dev/ram0 androidboot.hardware=remix_cn_x86_64 androidboot.selinux=permissive quiet SRC=/ DATA=/data
        initrd /initrd.img
}
```

![](/images/2016/03/15-1.png)

安装好后目录是这样的

```
cd /mnt/remix
ls
```
![](/images/2016/03/14.png)

### 重启进入RemixOS

直接退出关闭虚拟机,然后在设置里移除两个iso镜像

启动RemixOS
![](/images/2016/03/16.png)
