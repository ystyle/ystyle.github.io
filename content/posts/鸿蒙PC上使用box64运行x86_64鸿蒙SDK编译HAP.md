---
title: 鸿蒙PC上使用box64运行x86_64鸿蒙SDK编译HAP
date: 2026-06-30 22:00:00
lastmod: 2026-11-12 18:20:00
tags:
- 鸿蒙
- 鸿蒙PC
- box64
- SDK
- HAP
- 编译
- Matebook Pro
categories: 软件
slug: matebookpro-box64-harmony-sdk
---
> 鸿蒙 PC 的融合开发引擎给的是一个 aarch64 的 openEuler 容器，而鸿蒙官方命令行工具只发 x86_64 版。这篇是怎么在容器里把这套工具跑起来、最后编出 HAP 的。

## 为什么不能直接跑 {#背景}

鸿蒙 PC（HarmonyOS PC）的融合开发引擎提供的是 openEuler aarch64 容器环境，但鸿蒙官方命令行工具（command-line-tools）只有 x86_64 版本。要在 aarch64 上编译鸿蒙项目，有两种方案：

1. **QEMU 用户态模拟**：完整模拟 x86_64，可靠但性能损失大
2. **box64**：轻量级 x86_64 兼容层，只转换二进制指令，性能损失小

装 box64 本身只要两三行命令，麻烦的是它要的 x86_64 系统库——容器没有多架构支持，这些库得自己从 x86_64 仓库拆出来。试下来，box64 配合正确的 x86_64 系统库可以顺利完成编译。

## 跑通时的环境 {#环境说明}

| 项 | 值 |
| --- | --- |
| 系统 | openEuler 24.03 SP1 (aarch64) |
| CPU | ARM64 Cortex-A53 |
| box64 版本 | 0.4.2 |
| SDK 版本 | command-line-tools-linux-x64-6.1.1.290 (API 24) |

## 用 Nix 装 box64 {#安装box64}

```bash
# 通过Nix安装
source ~/.nix-profile/etc/profile.d/nix.sh
nix profile install nixpkgs#box64

# 验证
box64 --version
# Box64 arm64 v0.4.2
```

看到 `Box64 arm64 v0.4.2` 就算装好了。Nix 把可执行文件放在 `~/.nix-profile/bin/box64`，后面 wrapper 里 `exec` 的就是这个路径——profile 换位置，wrapper 也得跟着改。

## 缺 x86_64 的 glibc 和 libstdc++：去 x86_64 仓库拆 rpm {#准备x86-64系统库}

box64 运行 x86_64 二进制需要对应的系统库。openEuler aarch64 没有多架构支持，装不了 x86_64 的包，只能从 openEuler x86_64 仓库手动下载 rpm 再提取。

```bash
# 创建目录
mkdir -p /tmp/x86_64-libs && cd /tmp/x86_64-libs

base="https://repo.openeuler.org/openEuler-24.03-LTS-SP1/everything/x86_64/Packages"

# 下载基本系统库
for pkg in glibc-2.38-47.oe2403sp1 libgcc-12.3.1-62.oe2403sp1 \
           libstdc++-12.3.1-62.oe2403sp1; do
  url=$(curl -sL "$base/" | grep -oP "href=\"${pkg}[^\"]*x86_64\.rpm\"" | head -1 | sed 's/href="//;s/"//')
  [ -n "$url" ] && curl -sLO "$base/$url" && rpm2cpio "${pkg}.rpm" | cpio -idm
done
```

`rpm2cpio | cpio -idm` 是就地解包，文件落在当前目录下的 `lib64/`、`usr/lib64/` 等目录里。这些库后面要进 box64 的搜索路径。

## SDK 解到 /opt，先把属主改回来 {#SDK部署}

```bash
# 解压到/opt
sudo mkdir -p /opt/command-line-tools
sudo unzip command-line-tools-linux-x64-6.1.1.290.zip -d /opt/
sudo chown -R user:user /opt/command-line-tools
```

解压用了 `sudo`，解出来的文件属主是 root，紧跟的 `chown` 把权限交回普通用户；不然后面跑构建写不动。

SDK 目录结构：

```
/opt/command-line-tools/
├── bin/              # ohpm, hvigorw, hstack, codelinter
├── ohpm/             # 包管理器
├── hvigor/           # 构建工具
├── sdk/default/      # SDK
│   ├── openharmony/  # OpenHarmony SDK (API 24)
│   ├── hms/          # HMS SDK
│   └── sdk-pkg.json
└── tool/node/        # 自带x86_64 node（不使用）
```

## 换掉 SDK 自带的 x86_64 node {#Node-js配置}

SDK 自带的 node 是 x86_64 版本。hvigor 和 ohpm 都是 Node 程序，用它跑，每轮构建都要过一遍 box64；换成 fnm 装的原生 aarch64 版本就没这层开销：

```bash
fnm install 24
fnm default 24
```

然后在 `~/.zshrc` 里让 `DEVECO_NODE_HOME` 指过去：

```bash
export DEVECO_NODE_HOME="$HOME/.local/share/fnm/node-versions/v24.14.1/installation"
```

这里写死的是带补丁号的目录（`v24.14.1`），`fnm install 24` 装的却是 24 这一系列里的某个具体版本。对不上，路径就是空的，等于没设。

## 配置 box64：库路径和自动调用 {#box64配置}

box64 装好了还差两件事：让它找得到那些 x86_64 的 .so，以及让系统知道遇到 x86_64 的可执行文件该交给谁。

### 把 SDK 里散落的 x86_64 .so 收进一个目录 {#收集x86-64库}

SDK 里带了不少 x86_64 动态库，散在各个子目录下，需要统一收进一个目录：

```bash
mkdir -p /opt/x86_64-sdk-libs

# SDK中所有x86_64的.so
find /opt/command-line-tools/sdk -type f \( -name "*.so" -o -name "*.so.*" \) \
  -exec file {} \; 2>/dev/null | grep x86-64 | cut -d: -f1 | \
  while read f; do cp -f "$f" "/opt/x86_64-sdk-libs/$(basename $f)"; done

# 加入openEuler x86_64系统库
cp -n /tmp/x86_64-libs/usr/lib64/libGL* /opt/x86_64-sdk-libs/
cp -n /tmp/x86_64-libs/usr/lib64/libX* /opt/x86_64-sdk-libs/
cp -n /tmp/x86_64-libs/usr/lib64/libxcb* /opt/x86_64-sdk-libs/
```

`find` 那一段用 `file` 逐个判断，只留识别成 x86-64 的——SDK 里混着 aarch64 的二进制，不筛会拿到错架构的库。后面三个 `cp -n` 补的是 openEuler x86_64 仓库里的 OpenGL/X11 库，`-n` 表示同名文件已存在就不覆盖，所以 SDK 自带的版本优先。库是按文件名压平收进去的，不同目录下的同名 .so 只留一个。

### 注册 binfmt_misc，让 x86_64 二进制自动走 box64 {#注册binfmt-misc}

库齐了，还得让这些 x86_64 程序能被直接执行。这件事交给 binfmt_misc：

```bash
# 挂载
sudo mount binfmt_misc -t binfmt_misc /proc/sys/fs/binfmt_misc

# 创建wrapper脚本，设置库搜索路径
sudo tee /usr/local/bin/box64-wrapper << 'EOF'
#!/bin/bash
export BOX64_LD_LIBRARY_PATH="/opt/x86_64-sysroot/lib64:/opt/x86_64-sysroot/usr/lib64:/opt/x86_64-sdk-libs"
exec /home/user/.nix-profile/bin/box64 "$@"
EOF
sudo chmod +x /usr/local/bin/box64-wrapper

# 注册
echo ':box64:M::\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x3e\x00:\
\xff\xff\xff\xff\xff\xff\xfe\xff\xff\xff\xff\xff\xff\xff\xff\xff\xfe\xff\xff\xff:\
/usr/local/bin/box64-wrapper:F' | sudo tee /proc/sys/fs/binfmt_misc/register
```

那串字节是 ELF 头的前 20 个字节和对应的 mask，`\x3e` 是 x86_64 的机器类型号：只有 x86_64 的二进制会被拦下来，aarch64 的程序（比如 fnm 装的 node）照常直接执行。wrapper 存在的理由是 binfmt_misc 直接 exec，没有别的地方能替程序设环境变量，只能由 wrapper 先把库路径导出，再交给 box64。注册项写在 `/proc` 里，不在磁盘上，容器重建之后要重新挂载、重新注册。

## 真正编译：`hvigorw assembleHap` {#编译项目}

```bash
# 配置环境变量
export DEVECO_SDK_HOME="/opt/command-line-tools/sdk"
export DEVECO_NODE_HOME="$HOME/.local/share/fnm/node-versions/v24.14.1/installation"
export OHPM_HOME="/opt/command-line-tools"
export PATH="/opt/command-line-tools/bin:$PATH"
export BOX64_LD_LIBRARY_PATH="/opt/x86_64-sysroot/lib64:/opt/x86_64-sysroot/usr/lib64:/opt/x86_64-sdk-libs"

# 编译
cd ohos_project
hvigorw assembleHap --no-daemon
```

`DEVECO_SDK_HOME`、`OHPM_HOME`、`DEVECO_NODE_HOME` 分别给出 SDK、ohpm 和 node 的位置，`PATH` 里加上 `bin` 才能直接在项目目录里敲 `hvigorw`。末尾的 `BOX64_LD_LIBRARY_PATH` 和 wrapper 里设的是同一份路径：wrapper 管被 binfmt_misc 拦下的程序，shell 里这份管手动调 `box64`。

### 一次编译里哪几步过 box64 {#编译流程详解}

编译过程依次执行以下任务：

1. **CompileResource** — 编译资源文件
   - 使用 `restool` 处理图片等资源
   - 需要 box64 + x86_64 的 libGL/libX11 库支持
   - 依赖链：restool → dlopen(libimage_transcoder_shared.so) → libskia_canvaskit.so → libGL.so.1 → libGLX → libX11 → libxcb → libXau
  
2. **CompileArkTS** — 编译 ArkTS 代码
   - 使用 Node.js（原生 aarch64，不需要转换）
   - 不走 box64，性能良好

3. **PackageHap** — 打包 HAP
   - 需要 Java 17 支持
   
4. **SignHap** — 签名（可选）
   - 需要宿主机开发环境中的签名证书（.p12 文件）
   - 可先生成 unsigned HAP，后续通过 DevEco Studio 签名

四个任务里只有第一步过 box64：ArkTS 编译走原生 node，打包走原生 Java。资源编译挂掉通常是 `Cannot dlopen`；打包阶段报 `spawn java ENOENT`，就是没装 Java。

### unsigned HAP 里没有 HNP，得手动塞进去 {#添加HNP（Native-Plugin）}

编译生成的 unsigned HAP 默认不包含 HNP，需要手动添加：

```bash
cd ohos_project
zip -r entry/build/default/outputs/default/entry-default-unsigned.hap \
  hnp/arm64-v8a/neovim.hnp
```

`zip -r` 是往已有的 hap 包里追加，所以这一步得等 `assembleHap` 跑完之后再做。

### 产物在哪 {#编译结果}

unsigned HAP 生成位置：
```
entry/build/default/outputs/default/entry-default-unsigned.hap
```

## 撞过的四个坑 {#避坑指南}

### 一、资源编译报 `Cannot dlopen`，缺的是整条 OpenGL/X11 链 {#1-库依赖链}

编译资源时需要完整的 OpenGL/X11 库依赖链：

```
libimage_transcoder_shared.so
  → libskia_canvaskit.so
      → libGL.so.1
          → libGLX.so.0
          → libX11.so.6
              → libxcb.so.1
                  → libXau.so.6
          → libXext.so.6
          → libGLdispatch.so.0
      → libjsoncpp.so
      → libsec_shared.so
      → libstdc++.so.6
```

这条链上任何一个缺失都报 `Cannot dlopen`，得顺着链一段段对过去。

### 二、打包阶段报 `spawn java ENOENT`：容器里没有 Java {#2-Java缺失}

如果遇到 `spawn java ENOENT` 错误：

```bash
sudo dnf install -y java-17-openjdk
```

### 三、签名要证书，三条路挑一条 {#3-签名证书}

编译时的签名步骤会读取 `build-profile.json5` 里的证书路径。证书在宿主机上时，可以：

- 跳过签名，用 unsigned HAP：测试够用
- 把证书复制到容器内对应路径：位置要跟配置里写的一致
- 改 `signingConfigs`：指向容器里能访问的地方

### 四、box64 认 `BOX64_LD_LIBRARY_PATH`，不认 `LD_LIBRARY_PATH` {#4-环境变量}

box64 的库搜索路径由 `BOX64_LD_LIBRARY_PATH` 控制，不是 `LD_LIBRARY_PATH`——只设后者，box64 不会去那些目录找库。binfmt_misc 注册成功时，每次执行 x86_64 二进制都由 wrapper 设好这个变量；手动调 `box64` 时得自己在 shell 里设。

## 实际跑起来的速度 {#性能}

- 资源编译（restool）：约2-3秒（需要 box64 转换）
- ArkTS 编译（Node.js）：原生 aarch64，无损失
- HAP 打包（Java）：原生 aarch64，无损失

相比 QEMU 用户态模拟，box64 的启动速度和执行效率都要快得多。

## 跑完之后还剩什么手工活 {#总结}

拿到的是 `entry-default-unsigned.hap`。剩下两件手工活：HNP 要自己 `zip` 进包里，签名要么在容器里备好证书，要么回 DevEco Studio 做。这两步和 box64 没关系，box64 只负责把 x86_64 的工具跑起来。

---

**环境变量配置（~/.zshrc）参考**：

```bash
# HarmonyOS SDK
export DEVECO_SDK_HOME="/opt/command-line-tools/sdk"
export DEVECO_NODE_HOME="$HOME/.local/share/fnm/node-versions/v24.14.1/installation"
export OHPM_HOME="/opt/command-line-tools"
export PATH="/opt/command-line-tools/bin:$PATH"

# box64
export BOX64_LD_LIBRARY_PATH="/opt/x86_64-sysroot/lib64:/opt/x86_64-sysroot/usr/lib64:/opt/x86_64-sdk-libs"
```
