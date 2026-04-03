---
title: 仓颉语言 Neovim 开发环境配置指南
date: 2026-04-03 23:30:00
tags:
- Cangjie
- Neovim
- AstroNvim
- openEuler
categories: 编程
permalink: cangjie-neovim-dev-setup
---

本文档介绍如何在 openEuler (aarch64) 系统上配置 Neovim (AstroNvim) 开发环境，用于仓颉语言开发。

## 目录

- [系统要求](#系统要求)
- [安装仓颉 SDK](#安装仓颉-sdk)
- [安装 Cangjie STDX](#安装-cangjie-stdx)
- [环境变量配置](#环境变量配置)
- [Neovim 配置](#neovim-配置)
- [常见问题](#常见问题)

## 系统要求

- 操作系统：openEuler 2403 SP1 (aarch64)
- GCC 版本：12.3.1 或更高
- Neovim 版本：0.9.0 或更高

## 安装仓颉 SDK

1. 从官方渠道下载仓颉 SDK (aarch64 版本)
2. 解压到 `~/.config/cjvs/store/` 目录

目录结构示例：
```
~/.config/cjvs/
└── store/
    └── 1.1.0-beta.25/
        ├── envsetup.sh
        ├── lib/
        ├── runtime/
        └── ...
```

## 安装 Cangjie STDX

STDX 是仓颉的标准扩展库，需要单独安装：

1. 从发布页面下载：https://gitcode.com/Cangjie/cangjie_stdx/releases/v1.1.0-beta.24.1
2. 选择 `linux_aarch64_cjnative` 版本
3. 解压到 `~/.config/cjvs/stdx/` 目录

目录结构示例：
```
~/.config/cjvs/
└── stdx/
    └── 1.1.0-beta.24/
        └── linux_aarch64_cjnative/
            └── static/
                └── stdx/
                    ├── stdx.cjo
                    └── ...
```

## 环境变量配置

编辑 `~/.zshrc`，添加以下配置：

```bash
# 仓颉 SDK 环境配置
source $HOME/.config/cjvs/store/1.1.0-beta.25/envsetup.sh

# STDX 路径配置
export CANGJIE_STDX_PATH="$HOME/.config/cjvs/stdx/1.1.0-beta.24/linux_aarch64_cjnative/static/stdx"

```

配置完成后执行：
```bash
source ~/.zshrc
```

**说明**：
- `envsetup.sh`：设置仓颉编译器所需的环境变量
- `CANGJIE_STDX_PATH`：指定 STDX 库的路径

### 创建 GCC 运行时库符号链接

由于仓颉链接器脚本默认搜索 `/lib64` 目录，需要创建符号链接：

```bash
sudo ln -sf /usr/lib/gcc/aarch64-openEuler-linux/12/crtbeginS.o /lib64/crtbeginS.o
sudo ln -sf /usr/lib/gcc/aarch64-openEuler-linux/12/crtendS.o /lib64/crtendS.o
sudo ln -sf /usr/lib/gcc/aarch64-openEuler-linux/12/crtbegin.o /lib64/crtbegin.o
sudo ln -sf /usr/lib/gcc/aarch64-openEuler-linux/12/crtend.o /lib64/crtend.o
```

**说明**：解决链接时找不到 `crtbeginS.o` 等运行时库的问题

## Neovim 配置

### 1. 安装 AstroNvim

```bash
git clone --depth 1 https://github.com/AstroNvim/AstroNvim ~/.config/nvim
```

### 2. 配置仓颉 LSP 插件

创建文件 `~/.config/nvim/lua/plugins/cangjie-lsp.lua`：

```lua
return {
  "https://gitcode.com/ystyle/cangjie-nvim",
  dependencies = { "neovim/nvim-lspconfig" },
  opts = { auto_install = true },
  config = function(plugin)
    require("cangjie-nvim").setup(plugin.opts)

    vim.api.nvim_create_autocmd("LspAttach", {
      callback = function(args)
        if vim.bo[args.buf].filetype ~= "Cangjie" then return end
        
        local function map(mode, lhs, rhs, desc)
          vim.keymap.set(mode, lhs, rhs, { buffer = args.buf, desc = desc })
        end

        map("n", "<leader>li", "<cmd>LspInfo<cr>", "LSP Info")
        map("n", "K", vim.lsp.buf.hover, "Hover Document")
        map("n", "<leader>lf", function() vim.lsp.buf.format { async = true } end, "Format Document")
        map("n", "gl", vim.diagnostic.open_float, "Line Diagnostics")
        map("n", "<leader>ld", vim.diagnostic.open_float, "Line Diagnostics")
        map("n", "<leader>lD", vim.diagnostic.setqflist, "All Diagnostics")
        map("n", "gra", vim.lsp.buf.code_action, "Code Actions")
        map("n", "<leader>la", vim.lsp.buf.code_action, "Code Actions")
        map("n", "<leader>lh", vim.lsp.buf.signature_help, "Signature Help")
        map("n", "grn", vim.lsp.buf.rename, "Rename")
        map("n", "<leader>lr", vim.lsp.buf.rename, "Rename")
        map("n", "<leader>ls", vim.lsp.buf.document_symbol, "Document Symbols")
        map("n", "<leader>lG", vim.lsp.buf.workspace_symbol, "Workspace Symbols")
        map("n", "]d", vim.diagnostic.goto_next, "Diagnostic Next")
        map("n", "[d", vim.diagnostic.goto_prev, "Diagnostics Previous")
        map("n", "]e", function() vim.diagnostic.goto_next { severity = vim.diagnostic.severity.ERROR } end, "Error Next")
        map("n", "[e", function() vim.diagnostic.goto_prev { severity = vim.diagnostic.severity.ERROR } end, "Error Previous")
        map("n", "]w", function() vim.diagnostic.goto_next { severity = vim.diagnostic.severity.WARN } end, "Warning Next")
        map("n", "[w", function() vim.diagnostic.goto_prev { severity = vim.diagnostic.severity.WARN } end, "Warning Previous")
        map("n", "gD", vim.lsp.buf.declaration, "Declaration")
        map("n", "gy", vim.lsp.buf.type_definition, "Type Definition")
        map("n", "gd", vim.lsp.buf.definition, "Definition")
        map("n", "gri", vim.lsp.buf.implementation, "Implementation")
        map("n", "grr", vim.lsp.buf.references, "References")
      end,
    })
  end,
}
```

### 3. 启动 Neovim 并安装插件

```bash
nvim
```

AstroNvim 会自动检测并安装 `cangjie-nvim` 插件。首次打开 `.cj` 文件时，插件会自动下载 LSP wrapper 二进制文件。

**LSP Wrapper 地址**：
- 项目地址：https://gitcode.com/ystyle/cangjie-lsp-wrapper
- 自动下载位置：`~/.local/share/nvim/data/cangjie-nvim/bin/`

## 常见问题

### 1. 链接错误：cannot find crtbeginS.o

**错误信息**：
```
/usr/bin/ld: cannot find crtbeginS.o: No such file or directory
```

**解决方案**：
创建 GCC 运行时库符号链接：
```bash
sudo ln -sf /usr/lib/gcc/aarch64-openEuler-linux/12/crtbeginS.o /lib64/crtbeginS.o
sudo ln -sf /usr/lib/gcc/aarch64-openEuler-linux/12/crtendS.o /lib64/crtendS.o
sudo ln -sf /usr/lib/gcc/aarch64-openEuler-linux/12/crtbegin.o /lib64/crtbegin.o
sudo ln -sf /usr/lib/gcc/aarch64-openEuler-linux/12/crtend.o /lib64/crtend.o
```

### 2. LSP 不工作

**检查步骤**：
1. 确认仓颉 SDK 环境变量已加载：`echo $CANGJIE_HOME`
2. 确认 LSP wrapper 已下载：`ls ~/.local/share/nvim/data/cangjie-nvim/bin/`
3. 手动安装 LSP wrapper：
   ```lua
   :lua require("cangjie-nvim").install()
   ```

### 3. 找不到 STDX

**错误信息**：
```
error: cannot find stdx module
```

**解决方案**：
确认 `CANGJIE_STDX_PATH` 环境变量指向正确的目录：
```bash
ls $CANGJIE_STDX_PATH
# 应该能看到 stdx.cjo 文件
```

### 4. 快速事件上下文错误

**错误信息**：
```
E5560: nvim_create_namespace must not be called in a fast event context
```

**解决方案**：
此问题已在 `cangjie-nvim` 插件中修复，请确保使用最新版本。

## 键位映射

| 快捷键 | 功能 |
|--------|------|
| `K` | 显示悬停文档 |
| `gd` | 跳转到定义 |
| `gD` | 跳转到声明 |
| `gy` | 跳转到类型定义 |
| `gri` | 跳转到实现 |
| `grr` | 查找引用 |
| `grn` | 重命名 |
| `<leader>lf` | 格式化文档 |
| `<leader>la` | 代码操作 |
| `<leader>li` | LSP 信息 |
| `]d` / `[d` | 下一个/上一个诊断 |
| `]e` / `[e` | 下一个/上一个错误 |
| `]w` / `[w` | 下一个/上一个警告 |

## 参考链接

- [仓颉语言官网](https://cangjie.org/)
- [AstroNvim 文档](https://astronvim.github.io/)
- [cangjie-nvim 插件](https://gitcode.com/ystyle/cangjie-nvim)
- [cangjie-lsp-wrapper](https://gitcode.com/ystyle/cangjie-lsp-wrapper)
- [Cangjie STDX 发布](https://gitcode.com/Cangjie/cangjie_stdx/releases)