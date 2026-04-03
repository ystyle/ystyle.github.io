---
title: 鸿蒙PC融合开发引擎中编译安装Neovim与AstroNvim配置指南
date: 2026-04-03 21:35:00
updated: 2026-04-03 21:35:00
tags:
- 鸿蒙
- 鸿蒙PC
- neovim
- tree-sitter
- AstroNvim
- 编译安装
- Matebook Pro
categories: 软件
permalink: matebookpro-container-build-neovim
---

# 鸿蒙PC融合开发引擎中编译安装Neovim与AstroNvim配置指南

> 本文记录在鸿蒙PC融合开发引擎的容器环境中，因glibc版本限制从源码编译Neovim和tree-sitter的完整过程，并配置AstroNvim作为开发环境。

## 问题背景

### glibc版本冲突

在鸿蒙PC融合开发引擎的openEuler容器中，尝试安装nvim-treesitter插件时遇到错误：

```
[nvim-treesitter/install/c] error: Error during "tree-sitter build": 
tree-sitter: /usr/lib64/libc.so.6: version `GLIBC_2.39' not found (required by tree-sitter)
```

### 版本检查

```bash
ldd --version
# 输出：ldd (GNU libc) 2.38

cat /etc/os-release
# NAME="openEuler"
# VERSION="24.03 (LTS-SP1)"
```

openEuler 24.03 SP1的glibc是2.38，而nvim-treesitter下载的预编译tree-sitter CLI需要glibc 2.39。

### 根本原因

容器环境共享虚拟机内核，无法升级glibc。解决方案是**从源码编译所有组件**，使用当前系统的glibc版本。

## 解决方案总览

```
1. 安装编译依赖
2. 安装Rust工具链（编译tree-sitter CLI需要）
3. 从源码编译tree-sitter CLI
4. 从源码编译Neovim
5. 配置AstroNvim
```

## 一、安装编译依赖

### 基础工具

```bash
# 安装cmake和ninja
sudo dnf install -y cmake ninja-build

# 验证安装
cmake --version
ninja --version
```

### 其他依赖

```bash
# gcc、make等已预装
gcc --version
make --version
```

## 二、安装Rust工具链

tree-sitter CLI使用Rust编写，需要先安装Rust：

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

## 三、编译tree-sitter CLI

### 获取源码

```bash
export https_proxy=http://192.168.3.6:1080

# 克隆tree-sitter CLI（使用稳定版本v0.24.1）
git clone --depth 1 --branch v0.24.1 \
    https://github.com/tree-sitter/tree-sitter.git \
    ~/tree-sitter-cli
```

### 编译

```bash
cd ~/tree-sitter-cli
cargo build --release
```

编译过程约需1-2分钟。

### 安装

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

## 四、编译Neovim

### 获取源码

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

### 编译

```bash
cd ~/neovim
make CMAKE_BUILD_TYPE=Release
```

编译过程约需3-5分钟，会自动下载并编译所有依赖。

### 安装

```bash
sudo make install

# 验证
nvim --version
# 输出：
# NVIM v0.12.0
# Build type: Release
# LuaJIT 2.1.1774638290
```

### 编译输出位置

```bash
ls ~/neovim/build/bin/nvim
# -rwxr-xr-x 1 user user 10346568 ... nvim
```

## 五、配置AstroNvim

AstroNvim是一个预配置的Neovim发行版，提供完整的IDE体验。

### 备份现有配置

```bash
# 备份旧配置
mv ~/.config/nvim ~/.config/nvim.bak
mv ~/.local/share/nvim ~/.local/share/nvim.bak
mv ~/.local/state/nvim ~/.local/state/nvim.bak
```

### 安装AstroNvim

```bash
# 克隆AstroNvim配置
git clone --depth 1 https://github.com/AstroNvim/AstroNvim \
    ~/.config/nvim

# 复制默认用户配置模板
cp ~/.config/nvim/lua/user_template.lua ~/.config/nvim/lua/user.lua
```

### 首次启动

```bash
nvim
```

首次启动会自动安装所有插件和tree-sitter解析器。由于我们已编译了tree-sitter CLI，treesitter安装不会出现glibc错误。

### 自定义配置

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

### 安装LSP和工具

在Neovim中运行：

```vim
:LspInstall python
:LspInstall lua_ls
:TSInstall python
:TSInstall lua
:MasonInstall prettier
```

## 六、验证tree-sitter工作

### 安装解析器

```vim
:TSInstallInfo
```

查看可用的解析器，选择需要的安装：

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

### 检查状态

```vim
:TSInstallInfo
```

所有解析器应显示为 `✓ installed`。

## 七、总结

### 编译清单

| 组件 | 版本 | 状态 |
|------|------|------|
| cmake | 3.27.9 | ✓ 已安装 |
| ninja | 1.11.1 | ✓ 已安装 |
| Rust | 1.94.1 | ✓ 已安装 |
| tree-sitter CLI | 0.24.1 | ✓ 已编译 |
| Neovim | 0.12.0 | ✓ 已编译 |
| AstroNvim | latest | ✓ 已配置 |

### 关键点

1. **glibc兼容**：从源码编译确保使用当前glibc
2. **Rust依赖**：tree-sitter CLI需要Rust编译
3. **完整流程**：依赖 → Rust → tree-sitter → Neovim → AstroNvim

### 性能表现

编译的Neovim在openEuler容器中运行流畅：

- 启动速度：< 100ms
- LSP响应：快速
- Treesitter高亮：正常
- 插件生态：完整支持

### 避坑指南

1. **不要使用预编译tree-sitter**：mason下载的预编译版本glibc不兼容
2. **记得替换mason的tree-sitter**：否则nvim-treesitter仍会使用预编译版本
3. **使用稳定版本**：避免main分支的不稳定性

## 八、清理构建文件

编译完成后可以清理源码：

```bash
# 可选：保留源码用于后续升级
# 或删除以节省空间
rm -rf ~/tree-sitter-cli
rm -rf ~/neovim
```

建议保留源码目录，方便后续版本升级。

## 九、后续升级

升级Neovim：

```bash
cd ~/neovim
git fetch --tags
git checkout v0.13.0  # 假设新版本
make CMAKE_BUILD_TYPE=Release
sudo make install
```

升级tree-sitter：

```bash
cd ~/tree-sitter-cli
git fetch --tags
git checkout v0.25.0  # 假设新版本
cargo build --release
sudo cp target/release/tree-sitter /usr/local/bin/
```

---

**参考资源**：
- Neovim官网：[https://neovim.io](https://neovim.io)
- tree-sitter项目：[https://tree-sitter.github.io](https://tree-sitter.github.io)
- AstroNvim文档：[https://astronvim.com](https://astronvim.com)
- AstroNvim仓库：[https://github.com/AstroNvim/AstroNvim](https://github.com/AstroNvim/AstroNvim)