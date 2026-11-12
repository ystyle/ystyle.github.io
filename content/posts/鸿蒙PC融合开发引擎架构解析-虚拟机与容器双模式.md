---
title: 鸿蒙PC融合开发引擎架构解析：虚拟机与容器双模式
date: 2026-04-03 21:30:00
lastmod: 2026-11-12 18:20:00
tags:
- 鸿蒙
- 鸿蒙PC
- StratoVirt
- OzoneC
- 融合开发引擎
- Matebook Pro
categories: 软件
slug: matebookpro-fusion-dev-engine-architecture
---
> 鸿蒙 PC 上那个能跑 Linux 的「融合开发引擎」，底下是虚拟机套容器。这篇是我怎么一步步探出来的。

## 起因 {#起因}

鸿蒙 PC 自带的开发环境里有个「融合开发引擎」，打开就能用 openEuler 的命令行。官方文档只说是「提供 Linux 兼容环境」，没讲怎么实现的。

我想知道它到底跑在什么上面。原因很实际：**不清楚这一层是什么，就没法判断哪些东西能装、哪些装不了**。

下面是我探测的过程，和我最后得出的结论。所有判断都有命令输出支撑，你可以自己复现。

## 三条证据 {#三条证据}

### 一、`/sys/firmware` 里有 QEMU 的痕迹 {#一sysfirmware里有qemu的痕迹}

```bash
ls -la /sys/firmware/
# 输出里有：qemu_fw_cfg
```

`qemu_fw_cfg` 是 QEMU 的固件配置接口。它出现在这里，说明当前这个「环境」跑在一台虚拟机里，不是宿主机本身。

### 二、内核启动参数指向一个鸿蒙自己的 init {#二内核启动参数}

```bash
cat /proc/cmdline
# console=hvc0 root=/dev/vda ro reboot=k panic=1 init=/usr/sbin/HSLd
```

四个信息点：

- `console=hvc0` —— virtio 控制台，虚拟机才有的设备
- `root=/dev/vda` —— 根文件系统在虚拟块设备上
- `panic=1` —— 内核 panic 后 1 秒重启
- **`init=/usr/sbin/HSLd`** —— 启动的不是 systemd，而是 `HSLd`（HarmonyOS Linux daemon）

最后这条是关键：**鸿蒙在 Linux 内核启动后接管了一部分初始化工作**，不是丢一个通用发行版进去就完事。

### 三、根文件系统是 overlay，路径里有 OzoneC {#三根文件系统}

```bash
cat /proc/mounts | head -3
# overlay / overlay rw,dirsync,nodev,relatime,
#   lowerdir=/var/lib/OzoneC/overlay2/rgm_openEuler/lower,
#   upperdir=/var/lib/ozonec/bundle/openeuler2203.../diff,
#   workdir=/var/lib/ozonec/bundle/openeuler2203.../work
```

三个结论：

- 根文件系统是 **overlay**（分层镜像），不是直接挂一块盘
- 路径里的 `OzoneC` 是容器运行时（后面会说它是什么）
- `lower` 层叫 `rgm_openEuler`，说明底层镜像是 openEuler

`lowerdir` 只读、`upperdir` 可写——这正是容器镜像的标准分层。所以你在这个环境里装的东西都落在 `upperdir`，**删容器就没了**。

### 拼起来是什么 {#拼起来是什么}

三条证据指向同一个结构：

```
鸿蒙 PC（微内核）
  └─ StratoVirt 虚拟机（跑 Linux 6.6 内核）
       └─ OzoneC 容器（openEuler 用户空间）
            └─ 你看到的命令行
```

虚拟机负责「跑 Linux」这件事本身，容器负责「隔离不同应用环境」。两层叠起来。

## StratoVirt 是什么 {#stratovirt是什么}

华为开源的轻量虚拟机，Rust 写的，属于 openEuler 项目。

它对标的是 QEMU，但**只做云和边缘场景需要的那部分**——不做完整的 PC 硬件模拟，所以启动快、内存占用小。

鸿蒙 PC 选它，大概有两个原因：

1. **Rust 写的**：内存安全漏洞少。虚拟机跑在内核下面，出问题影响面大
2. **轻**：桌面设备上不能为了「兼容 Linux」吃掉几个 G 内存

它有两种机型：

```bash
# microvm：精简机型，启动最快
./stratovirt -machine microvm \
    -kernel /path/to/kernel \
    -append "console=ttyAMA0 root=/dev/vda" \
    -drive file=/path/to/rootfs,id=rootfs \
    -device virtio-blk-device,drive=rootfs \
    -serial stdio

# virt：标准机型，设备更全
./stratovirt -machine virt \
    -kernel /path/to/kernel \
    -drive file=/path/to/firmware,if=pflash \
    -device virtio-blk-pci,drive=rootfs \
    -serial stdio
```

鸿蒙 PC 上跑的是哪一种，我没法直接确认（看不到虚拟机启动命令）。但从 `hvc0` 和 `virtio-blk-device`（非 PCI）看，**更像 microvm**。

## OzoneC 是什么 {#ozonec是什么}

StratoVirt 项目里的容器运行时，也是 Rust 写的，符合 OCI 标准。

命令和 docker 那套对得上：

```bash
ozonec create  <container-id>   # 创建
ozonec start   <container-id>   # 启动
ozonec state   <container-id>   # 查状态
ozonec kill    <container-id>   # 终止
ozonec delete  <container-id>   # 删除
ozonec exec    <container-id>   # 在容器里执行命令
```

**为什么虚拟机里还要再套一层容器？**

如果只跑虚拟机，那整个 Linux 环境是一个整体：你在里面装的东西、跑的进程，全混在一起。想要第二个干净环境，就得再起一台虚拟机，成本高。

套一层容器之后，多个开发环境可以共用同一个 Linux 内核，各自有独立的文件系统。

代价是**容器共享内核**，所以内核相关的操作做不了——下面会讲。

## 这套设计的代价 {#这套设计的代价}

我在实际使用里撞到三条限制：

| 限制 | 表现 | 能不能绕 |
| --- | --- | --- |
| 换不了内核 | 虚拟机内核固定在 6.6.0，容器跟着它 | 不能 |
| glibc 版本受限 | 要用某个软件，它要求的 glibc 比容器里的新 | 能，见下 |
| 装不了内核模块 | `insmod` 之类直接失败 | 不能 |

第二条最常撞。三个绕过办法：

**从源码编译** —— 用容器自带的 glibc 编译你需要的软件。适合开源、依赖不复杂的项目。

**静态链接** —— 编译时把库都塞进二进制，摆脱对系统 glibc 的依赖。缺点是这个二进制会变大，而且有些库静态链接很麻烦。

**隔离环境** —— conda、nix 这类工具能自己管依赖和解释器，不碰系统 glibc。适合 Python 生态，其他语言要看情况。

## 和 WSL 的差别 {#和wsl的差别}

两件事都是「Windows/Linux 桌面里跑 Linux」，但底层不一样：

| | 鸿蒙融合开发引擎 | WSL2 |
| --- | --- | --- |
| 层次 | 虚拟机 + 容器 | 虚拟机（单层） |
| 内核 | Linux 6.6.0 | 微软自编译内核 |
| 容器 | OzoneC | Docker（另装） |
| 镜像来源 | 鸿蒙生态预置 | Docker Hub |

**多一层容器**意味着可以同时有多个隔离环境，这是 WSL2 默认没有的（WSL2 要自己装 Docker）。

但镜像来源是鸿蒙预置的，不像 Docker Hub 那样想拉什么拉什么。

## 实际怎么用 {#实际怎么用}

知道结构之后，几个判断就清楚了：

**当普通 Linux 用**：装包（`dnf`）、跑服务（nginx/redis）、编译代码，都没问题。它就是个 openEuler。

**数据要往外存**：容器删了 `upperdir` 就没了，重要文件放在宿主机目录，通过挂载点访问。

**别指望改内核**：想调内核参数、装内核模块、换内核版本，这条路上没有出口。

**glibc 冲突先想静态链接**：实在不行再上 conda/nix，别去动系统库——动了整个环境可能起不来。

## 参考资料 {#参考资料}

- [StratoVirt 源码](https://gitcode.com/openeuler/stratovirt)（OzoneC 在 `ozonec/` 目录下）
- [openEuler 官网](https://openeuler.org)
