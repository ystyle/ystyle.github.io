---
title: 鸿蒙PC融合开发引擎中编译安装Neovim与AstroNvim配置指南
date: 2026-04-03 21:35:00
lastmod: 2026-11-12 18:20:00
tags:
- 鸿蒙
- 鸿蒙PC
- neovim
- tree-sitter
- AstroNvim
- 编译安装
- Matebook Pro
categories: 软件
slug: matebookpro-container-build-neovim
---
> 鸿蒙 PC 融合开发引擎的 openEuler 容器里，glibc 是 2.38；nvim-treesitter 下载的预编译 tree-sitter 要 2.39，装解析器直接报错。这篇是绕开的办法：自己编译 tree-sitter CLI 和 Neovim，再接上 AstroNvim。

## 装插件时报的那一行错 {#问题背景}

### 触发点是 nvim-treesitter 装解析器 {#glibc版本冲突}

在鸿蒙 PC 融合开发引擎的 openEuler 容器里，装 nvim-treesitter 后第一次触发 tree-sitter 构建就停了：

```
[nvim-treesitter/install/c] error: Error during "tree-sitter build": 
tree-sitter: /usr/lib64/libc.so.6: version `GLIBC_2.39' not found (required by tree-sitter)
```

报错的是 `tree-sitter` 这个可执行文件本身，不是编出来的解析器。nvim-treesitter 动手前要先调它，这一步就没起来。

### 容器里的 glibc 是 2.38 {#版本检查}

查一下版本就知道差在哪：

```bash
ldd --version
# 输出：ldd (GNU libc) 2.38

cat /etc/os-release
# NAME="openEuler"
# VERSION="24.03 (LTS-SP1)"
```

openEuler 24.03 SP1 的 glibc 是 2.38，预编译的 tree-sitter CLI 要 2.39，差一个小版本。

### 升级 glibc 这条路走不通 {#根本原因}

容器共享虚拟机内核，容器里的 glibc 跟着镜像走，没法就地升。能改的只有另一边：把要用的组件按容器自带的 glibc 自己编一遍。

## 整条链路五步 {#解决方案总览}

```
1. 安装编译依赖
2. 安装Rust工具链（编译tree-sitter CLI需要）
3. 从源码编译tree-sitter CLI
4. 从源码编译Neovim
5. 配置AstroNvim
```

五步之间是顺序依赖，原因写在第七节。

## 一、装 cmake 和 ninja {#一、安装编译依赖}

### cmake 和 ninja 一起装 {#基础工具}

在哪个目录执行都行，装的是系统包：

```bash
# 安装cmake和ninja
sudo dnf install -y cmake ninja-build

# 验证安装
cmake --version
ninja --version
```

`make CMAKE_BUILD_TYPE=Release` 底下调的是 CMake，ninja 是它可用的构建后端。`dnf` 拉不到包，先确认容器里能出网。

### gcc 和 make 镜像里自带 {#其他依赖}

这个镜像里 gcc 和 make 都已经有了，确认版本就行，缺了再补：

```bash
# gcc、make等已预装
gcc --version
make --version
```

## 二、装 Rust：先有 cargo 才编得了 tree-sitter {#二、安装Rust工具链}

用 rustup 装到用户目录，不碰系统包：

```bash
# 设置代理（可选）
export https_proxy=http://192.168.3.6:1080

# 安装Rust
curl --proto '=https' -sSf https://sh.rustup.rs | sh -s -- -y

# 加载环境
source ~/.cargo/env

# 验证
cargo --version
rustc --version
```

`sh -s -- -y` 让安装脚本不提问，装到 `~/.cargo`；两条 `--version` 有输出，说明 `~/.cargo/bin` 进了 PATH。

`source ~/.cargo/env` 只对当前 shell 有效，换窗口要再 source 一次；漏了的话 `cargo build` 报的是找不到 `cargo`。

## 三、自己编一份 tree-sitter CLI {#三、编译tree-sitter-CLI}

### 拉 v0.24.1 的源码 {#获取源码}

```bash
export https_proxy=http://192.168.3.6:1080

# 克隆tree-sitter CLI（使用稳定版本v0.24.1）
git clone --depth 1 --branch v0.24.1 \
    https://github.com/tree-sitter/tree-sitter.git \
    ~/tree-sitter-cli
```

`--branch` 钉的是 tag `v0.24.1`，`--depth 1` 只带一个提交。拉不动先看 `https_proxy`。

### cargo build --release {#编译}

```bash
cd ~/tree-sitter-cli
cargo build --release
```

约 1-2 分钟。**必须在 `~/tree-sitter-cli` 里执行**：`cargo` 靠当前目录的 `Cargo.toml` 找项目，在别处跑会说找不到清单文件；产物在 `target/release/`。

### 装到哪：系统路径还是 mason 目录 {#安装}

```bash
# 系统安装
sudo cp ~/tree-sitter-cli/target/release/tree-sitter /usr/local/bin/

# 或替换mason的预编译版本
cp ~/tree-sitter-cli/target/release/tree-sitter \
    ~/.local/share/nvim/mason/packages/tree-sitter-cli/tree-sitter-linux-arm64

# 验证
tree-sitter --version
# 输出：tree-sitter 0.24.1
```

两条 `cp` 放的不是一个地方：`/usr/local/bin` 那份是系统级，shell 里直接敲 `tree-sitter` 就能用；mason 目录那份才是 nvim-treesitter 在 Neovim 里调的，要换的是它。

mason 这条路有个前提：`nvim` 和 mason 先装过 `tree-sitter-cli`，目录才存在。这时候还没装（第五节才装 AstroNvim）就先跳过，装完回来补。

`tree-sitter --version` 打出 `0.24.1`，说明 `/usr/local/bin` 这份是好的；Neovim 里还报 glibc 错，就是 mason 那份没换。

## 四、编译 Neovim {#四、编译Neovim}

### 先看要编哪个版本 {#获取源码-1}

```bash
export https_proxy=http://192.168.3.6:1080

# 查看最新版本
git ls-remote --tags https://github.com/neovim/neovim.git | \
    grep -v '\^{}' | grep 'v0\.1[0-2]' | tail -5

# 克隆最新稳定版v0.12.0
git clone --depth 1 --branch v0.12.0 \
    https://github.com/neovim/neovim.git \
    ~/neovim
```

第一条 `git ls-remote` 只列远端 tag，不落盘：`grep -v '\^{}'` 去掉 peeled 引用，`grep 'v0\.1[0-2]'` 只留 v0.10 到 v0.12，`tail -5` 取最后五条。第二条才真正拉代码。

### make CMAKE_BUILD_TYPE=Release {#编译-1}

```bash
cd ~/neovim
make CMAKE_BUILD_TYPE=Release
```

约 3-5 分钟，中间会自动下载并编译依赖。

**这一步要联网**：前面几个 `export https_proxy` 只对当时的 shell 有效，换过窗口就在这里重新设一次。

### sudo make install，再验证版本 {#安装-1}

```bash
sudo make install

# 验证
nvim --version
# 输出：
# NVIM v0.12.0
# Build type: Release
# LuaJIT 2.1.1774638290
```

`make install` 往 `/usr/local/bin` 和运行时目录写文件，所以要 sudo。`nvim --version` 打出 `NVIM v0.12.0`、`Build type: Release` 就对了；还是老版本就先 `which nvim`。

### 产物就在 build/bin 下 {#编译输出位置}

```bash
ls ~/neovim/build/bin/nvim
# -rwxr-xr-x 1 user user 10346568 ... nvim
```

`sudo make install` 之前它就存在，可以直接拿去跑。

## 五、接上 AstroNvim {#五、配置AstroNvim}

AstroNvim 是别人维护好的一套 Neovim 配置，颜色方案、选项、插件、LSP 行为都在 `user.lua` 里配。它不含 Neovim，靠上一步装好的 `nvim`；插件和 LSP 也不在仓库里，首次启动才下。

### 先把旧配置挪走 {#备份现有配置}

```bash
# 备份旧配置
mv ~/.config/nvim ~/.config/nvim.bak
mv ~/.local/share/nvim ~/.local/share/nvim.bak
mv ~/.local/state/nvim ~/.local/state/nvim.bak
```

三个目录各管一件事：`~/.config/nvim` 是配置，`~/.local/share/nvim` 是插件和 mason 装的工具，`~/.local/state/nvim` 是运行时状态。

第二条会把 `mason` 目录一起挪走。前面替换过 mason 那份 tree-sitter 的，装完 AstroNvim 要再补一次（见第七节）。

### 克隆配置，复制出 user.lua {#安装AstroNvim}

```bash
# 克隆AstroNvim配置
git clone --depth 1 https://github.com/AstroNvim/AstroNvim \
    ~/.config/nvim

# 复制默认用户配置模板
cp ~/.config/nvim/lua/user_template.lua ~/.config/nvim/lua/user.lua
```

配置目录必须叫 `~/.config/nvim`，Neovim 启动只认这个位置；`user.lua` 是从模板复制出来的，你改的东西写在这里，仓库更新盖不掉。

### 第一次启动会自己装插件 {#首次启动}

```bash
nvim
```

插件不在仓库里，首次启动才去下，要等，也要网络。前面编的 tree-sitter CLI 就是给这一刻用的：解析器要现场编译，调的是它，不会再出 glibc 错。

### user.lua 里改什么 {#自定义配置}

编辑 `~/.config/nvim/lua/user.lua`：

```lua
return {
  -- 自定义颜色方案
  colorscheme = "catppuccin-mocha",
  
  -- 自定义选项
  options = {
    opt = {
      relativenumber = true, -- 相对行号
    },
  },
  
  -- 自定义插件
  plugins = {
    "rebelot/kanagawa.nvim",
    -- 添加更多插件...
  },
  
  -- LSP配置
  lsp = {
    formatting = {
      format_on_save = true,
    },
    servers = {
      -- 添加LSP服务器...
    },
  },
}
```

四块内容：颜色方案、编辑器选项、额外插件、LSP 行为。`format_on_save = true` 是保存时自动格式化，得先有格式化工具，后面 `:MasonInstall prettier` 装的就是它。

### LSP 和工具为什么得单独装 {#安装LSP和工具}

在 Neovim 里执行：

```vim
:LspInstall python
:LspInstall lua_ls
:TSInstall python
:TSInstall lua
:MasonInstall prettier
```

`:LspInstall` 装 LSP 服务器本体，`:MasonInstall prettier` 装格式化工具，都是独立的外部可执行文件，落在 `~/.local/share/nvim/mason/packages/` 下——和第三节替换的 tree-sitter 是同一个目录。AstroNvim 只负责把它们接到 Neovim 上，程序本身不替你下载，这几条得自己跑。

`:TSInstall` 走的是另一套：解析器归 nvim-treesitter 管，负责语法高亮；LSP 负责补全和诊断。

## 六、确认解析器是用新 CLI 编的 {#六、验证tree-sitter工作}

### 先看有哪些解析器 {#安装解析器}

```vim
:TSInstallInfo
```

列表里能看到装没装、要不要编，挑需要的装：

```vim
:TSInstall vimdoc
:TSInstall lua
:TSInstall python
:TSInstall javascript
:TSInstall html
:TSInstall css
:TSInstall json
:TSInstall markdown
```

### 装完核对状态 {#检查状态}

```vim
:TSInstallInfo
```

所有解析器应显示为 `✓ installed`。

这一步不报 `GLIBC_2.39`，说明 nvim-treesitter 调的是你编的 tree-sitter；没到 `✓ installed` 的重跑对应 `:TSInstall`，报错会直接打出来。

## 七、版本清单和踩过的坑 {#七、总结}

### 装完的版本 {#编译清单}

| 组件 | 版本 | 状态 |
|------|------|------|
| cmake | 3.27.9 | ✓ 已安装 |
| ninja | 1.11.1 | ✓ 已安装 |
| Rust | 1.94.1 | ✓ 已安装 |
| tree-sitter CLI | 0.24.1 | ✓ 已编译 |
| Neovim | 0.12.0 | ✓ 已编译 |
| AstroNvim | latest | ✓ 已配置 |

cmake 和 ninja 用 dnf 装，Rust 用 rustup 装，tree-sitter CLI 和 Neovim 自己编，AstroNvim 是 clone 下来的配置。

### 顺序为什么不能换 {#关键点}

三条依赖决定顺序：

1. **tree-sitter CLI 是 Rust 项目**：没有 `cargo` 就没有 `cargo build --release`。
2. **解析器要等首次启动才编**：Neovim 和 AstroNvim 就位后，`nvim` 第一次启动才去调 CLI 编解析器，所以 CLI 得赶在这次启动之前装好。
3. **AstroNvim 只是配置**：`git clone` 到 `~/.config/nvim` 就算装好，插件、解析器、LSP 都是启动之后才下载。

顺序反了，每一步都要回头补前一步的活。

### 用起来怎么样 {#性能表现}

编出来的 Neovim 在 openEuler 容器里没有卡顿：启动在 100ms 以内，LSP 响应快，treesitter 高亮正常，插件生态完整可用。

### 三个容易踩的坑 {#避坑指南}

1. **别用 mason 下载的预编译 tree-sitter**：它要的 glibc 比容器里的新，一装解析器就报 `GLIBC_2.39' not found`。
2. **替换 mason 那份要补在最后**：`~/.local/share/nvim/mason/packages/tree-sitter-cli/tree-sitter-linux-arm64` 得等 mason 装过才存在，而第五节的 `mv` 会把 `~/.local/share/nvim` 整个挪走。顺序是「装完 AstroNvim → 首次启动 → 再 `cp` 一次」。
3. **版本按 tag 钉住**：v0.24.1 和 v0.12.0，别跟 main 分支。

## 八、源码目录留不留 {#八、清理构建文件}

想省空间可以删：

```bash
# 可选：保留源码用于后续升级
# 或删除以节省空间
rm -rf ~/tree-sitter-cli
rm -rf ~/neovim
```

但下一节的升级要用这两个目录，删了得重新 clone，留着更省事。

## 九、以后升级 {#九、后续升级}

升级 Neovim：

```bash
cd ~/neovim
git fetch --tags
git checkout v0.13.0  # 假设新版本
make CMAKE_BUILD_TYPE=Release
sudo make install
```

升级 tree-sitter：

```bash
cd ~/tree-sitter-cli
git fetch --tags
git checkout v0.25.0  # 假设新版本
cargo build --release
sudo cp target/release/tree-sitter /usr/local/bin/
```

两条 `git checkout` 的版本号是占位的，先 `git fetch --tags` 看实际有哪些 tag。升级 tree-sitter 那段只 `cp` 到 `/usr/local/bin`，mason 那份要一起换就按第三节再来一遍。

## 参考资源 {#参考资源}

- Neovim官网：[https://neovim.io](https://neovim.io)
- tree-sitter项目：[https://tree-sitter.github.io](https://tree-sitter.github.io)
- AstroNvim文档：[https://astronvim.com](https://astronvim.com)
- AstroNvim仓库：[https://github.com/AstroNvim/AstroNvim](https://github.com/AstroNvim/AstroNvim)
