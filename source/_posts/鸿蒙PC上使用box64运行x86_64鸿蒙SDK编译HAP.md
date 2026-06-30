---
title: 鸿蒙PC上使用box64运行x86_64鸿蒙SDK编译HAP
date: 2026-06-30 22:00:00
updated: 2026-06-30 22:00:00
tags:
- 鸿蒙
- 鸿蒙PC
- box64
- SDK
- HAP
- 编译
- Matebook Pro
categories: 软件
permalink: matebookpro-box64-harmony-sdk
---

# 鸿蒙PC上使用box64运行x86_64鸿蒙SDK编译HAP

> 本文记录在鸿蒙PC融合开发引擎的openEuler aarch64容器中，通过box64模拟x86_64兼容层，运行鸿蒙命令行工具编译HAP的完整过程。

## 背景

鸿蒙PC（HarmonyOS PC）的融合开发引擎提供的是openEuler aarch64容器环境，但鸿蒙官方命令行工具（command-line-tools）只有x86_64版本。要在aarch64上编译鸿蒙项目，有两种方案：

1. **QEMU用户态模拟**：完整模拟x86_64，可靠但性能损失大
2. **box64**：轻量级x86_64兼容层，仅转换二进制指令，性能损失小

经过测试，box64配合正确的x86_64系统库可以顺利完成编译。

## 环境说明

- 系统：openEuler 24.03 SP1 (aarch64)
- CPU：ARM64 Cortex-A53
- box64版本：0.4.2
- SDK版本：command-line-tools-linux-x64-6.1.1.290 (API 24)

## 安装box64

```bash
# 通过Nix安装
source ~/.nix-profile/etc/profile.d/nix.sh
nix profile install nixpkgs#box64

# 验证
box64 --version
# Box64 arm64 v0.4.2
```

## 准备x86_64系统库

box64运行x86_64二进制需要对应的系统库。由于openEuler aarch64没有多架构支持，需要从openEuler x86_64仓库手动下载并提取。

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

提取的库文件会分布在 `lib64/` 和 `usr/lib64/` 等目录中，后续统一配置到box64的库搜索路径。

## SDK部署

```bash
# 解压到/opt
sudo mkdir -p /opt/command-line-tools
sudo unzip command-line-tools-linux-x64-6.1.1.290.zip -d /opt/
sudo chown -R user:user /opt/command-line-tools
```

SDK目录结构：

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

## Node.js配置

SDK自带的node是x86_64版本，使用fnm安装原生aarch64版本替代：

```bash
fnm install 24
fnm default 24
```

在 `~/.zshrc` 中设置 `DEVECO_NODE_HOME` 指向fnm的node：

```bash
export DEVECO_NODE_HOME="$HOME/.local/share/fnm/node-versions/v24.14.1/installation"
```

## box64配置

### 收集x86_64库

SDK中包含了大量x86_64动态库，需要统一收集到一个目录：

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

### 注册binfmt_misc

通过binfmt_misc让系统自动识别x86_64二进制并调用box64：

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

## 编译项目

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

### 编译流程详解

编译过程依次执行以下任务：

1. **CompileResource** — 编译资源文件
   - 使用`restool`处理图片等资源
   - 需要box64 + x86_64的libGL/libX11库支持
   - 依赖链：restool → dlopen(libimage_transcoder_shared.so) → libskia_canvaskit.so → libGL.so.1 → libGLX → libX11 → libxcb → libXau
  
2. **CompileArkTS** — 编译ArkTS代码
   - 使用Node.js（原生aarch64，不需要转换）
   - 性能良好，无需box64介入

3. **PackageHap** — 打包HAP
   - 需要Java 17支持
   
4. **SignHap** — 签名（可选）
   - 需要宿主机开发环境中的签名证书（.p12文件）
   - 可先生成unsigned HAP，后续通过DevEco Studio签名

### 添加HNP（Native Plugin）

编译生成的unsigned HAP默认不包含HNP。需要手动添加：

```bash
cd ohos_project
zip -r entry/build/default/outputs/default/entry-default-unsigned.hap \
  hnp/arm64-v8a/neovim.hnp
```

### 编译结果

unsigned HAP生成位置：
```
entry/build/default/outputs/default/entry-default-unsigned.hap
```

## 避坑指南

### 1. 库依赖链

编译资源时需要完整的OpenGL/X11库依赖链：

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

任何一个缺失都会导致 `Cannot dlopen` 错误。

### 2. Java缺失

如果遇到 `spawn java ENOENT` 错误：

```bash
sudo dnf install -y java-17-openjdk
```

### 3. 签名证书

编译时的签名步骤会读取 `build-profile.json5` 中的证书路径。如果证书在宿主机上，可以：

- 跳过签名，使用unsigned HAP
- 或将证书文件复制到容器内对应路径
- 或修改 `build-profile.json5` 中的 `signingConfigs` 配置

### 4. 环境变量

box64的库搜索通过 `BOX64_LD_LIBRARY_PATH` 控制，不是 `LD_LIBRARY_PATH`。如果binfmt_misc注册成功，每次执行x86_64二进制时wrapper脚本会自动设置该变量。

## 性能

box64在编译场景下的性能表现：

- 资源编译（restool）：约2-3秒（需要box64转换）
- ArkTS编译（Node.js）：原生aarch64，无损失
- HAP打包（Java）：原生aarch64，无损失

相比QEMU用户态模拟，box64的启动速度和执行效率都要快得多，适合SDK场景。

## 总结

通过box64 + binfmt_misc的组合，可以在鸿蒙PC的aarch64容器中顺利运行x86_64的鸿蒙命令行工具，完成HAP的编译。关键点在于：

1. **box64配合binfmt_misc**：自动识别x86_64二进制，无需手动调用
2. **完整的x86_64系统库**：OpenGL/X11库链是资源编译的必需依赖
3. **原生Node.js**：SDK的核心构建工具（hvigor）基于Node.js，使用fnm安装aarch64版本即可
4. **签名分离**：编译和签名可以分开处理，unsigned HAP也可用于测试

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
