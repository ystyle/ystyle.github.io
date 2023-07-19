---
title: 在archlinux aur上提交龙芯loongarch的软件包
date: 2023-07-19 14:46:26
updated: 2023-07-19 14:46:26
tags:
- loongarch
- archlinux
- 龙芯
categories: 系统
permalink: push-loongarch64-app-to-archlinux-aur
---

![image](https://github.com/ystyle/ystyle.github.io/assets/4478635/1813826c-da90-426f-9d19-e9a459f3f262)


>发现安装好龙芯后, laur软件仓库就自带了yay和paru, 可以直接使用pacman安装. 我有一个软件kaf-cli是go写的可以直接编译到龙芯上.本文记录一下PKGBUILD的写法

### PKGBUILD脚本 
脚本基本上和x86上的没什么区别, 只需要
- 在`arch`字段上添加`loong64`构架
- 添加`source_loong64`软件安装包的源
- 添加`sha512sums_loong64`校验值, 还可以是`md5sum_loong64`, `sha1sums_loong64`
```PKGBUILD
# Maintainer: YSTYLE <lxy5266@live.com>

pkgname=kaf-cli
pkgver=v1.3.5
pkgrel=2
epoch=
pkgdesc="把txt文本转成epub与mobi电子书的命令行工具"
arch=('x86_64' 'aarch64' 'loong64')
url="https://github.com/ystyle/kaf-cli"
license=('MulanPSL')
optdepends=('kindlegen: 在x86_64上用于生成标准的mobi格式')
source_x86_64=("https://github.com/ystyle/TmdTextEpub/releases/download/$pkgver/kaf-cli_${pkgver}_linux_amd64.zip")
source_aarch64=("https://github.com/ystyle/TmdTextEpub/releases/download/$pkgver/kaf-cli_${pkgver}_linux_arm64.zip")
source_loong64=("https://github.com/ystyle/TmdTextEpub/releases/download/$pkgver/kaf-cli_${pkgver}_linux_loong64.zip")
sha512sums_x86_64=('29d3f3e0138f2348024d8a3e2a7a19dfe00b0098e9247c2ea364f3e4ab992575fc68bbbf56258be341c335b94e989ecbe37c0c32419b61ee2d45034f5c5e00de')
sha512sums_aarch64=('72d2519dec242be92869d0d2eb7022d836147624ff79ba797ff287eb0444eb3dd33e910c01422e1448d486955dbbea0fbc2166e942213e1be03038993945e28f')
sha512sums_loong64=('c6af9aeb904f934c0fbee06dda83fed02a22c0ec41cccd1b685cbe5e232b5dd66ad5888a91ab2aadeef7007870c94a063a4537a3e32f150d4ea12453cb3f1b54')

package() {
    install -Dm755 kaf-cli "$pkgdir/usr/bin/kaf-cli"
}
```

然后生成安装包清单信息
```shell
makepkg --printsrcinfo > .SRCINFO
```

测试生成安装包
```shell
makepkg -f
```

直接安装软件
```shell
makepkg -si
```


没问题直接用git推送到aur上就可以了
