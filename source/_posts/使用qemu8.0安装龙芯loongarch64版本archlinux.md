---
title: 使用qemu8.0安装龙芯loongarch64版本archlinux
date: 2023-07-20 10:46:26
updated: 2023-07-20 10:46:26
tags:
- qemu
- loongarch
- archlinux
categories: 系统
permalink: install-loongarch64-archlinux-qemu
---

### 准备
- [Loong Arch Linux官网](https://loongarchlinux.org/pages/download/)
- [qemu镜像下载](https://mirrors.pku.edu.cn/loongarch/archlinux/images/)
  - `QEMU_EFI_8.0.fd`: 固件
  - `archlinux-xfce4-2023.05.10-loong64.qcow2.zst`: 系统镜像, 下载后需要解压出qcow2文件

### 安装依赖
>建议安装`qemu-full`包, 我以前安装的不是这个, 导致gpu加载不了

```shell
sudo pacman -S qemu-full
```

### 启动系统
>注意固件版本和系统镜像版本

```shell
qemu-system-loongarch64 \
    -m 4G \
    -cpu la464-loongarch-cpu \
    -machine virt \
    -smp 4 \
    -bios ./QEMU_EFI_8.0.fd \
    -serial stdio \
    -device virtio-gpu-pci \
    -net nic -net user \
    -device nec-usb-xhci,id=xhci,addr=0x1b \
    -device usb-tablet,id=tablet,bus=xhci.0,port=1 \
    -device usb-kbd,id=keyboard,bus=xhci.0,port=2 \
    -hda archlinux-xfce4-2023.05.10-loong64.qcow2
```

![image](https://github.com/ystyle/ystyle.github.io/assets/4478635/6ccb868a-2fa2-4b8c-8a92-5ca84f4a1e03)

![image](https://github.com/ystyle/ystyle.github.io/assets/4478635/a71528eb-e84c-44b9-b5b9-4f2343e4699f)
