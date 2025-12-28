---
title: 鸿蒙PC Matebook Pro上全局安装GIT
date: 2025-12-28 10:30:00
updated: 2025-12-28 10:30:00
tags:
- 鸿蒙
- 鸿蒙PC
- git
- matebook pro
categories: 软件
permalink: matebookpro-install-git
---

## 准备工作
- 在鸿蒙应用商店安装 CodeArts IDE

## 从CodeArts IDE提取签名工具
打开IDE, 随便创建一个项目打开，在终端执行以下命令
```shell
# 复制签名工具
cp /data/app/toolchains.org/toolchains_1.0/lib//binary-sign-tool .
# 对签名工具签名
binary-sign-tool sign -inFile "./binary-sign-tool" -outFile "./binary-sign-tool-signed" -selfSign 1
# 添加可执行权限
chmod +x binary-sign-tool-signed
# 测试，如果没弹授权弹窗和帮忙输出，需要重新签名和添加可执行权限
./binary-sign-tool-signed

# 复制到用户安装目录
mkdir -p ~/.local/bin
cp ./binary-sign-tool-signed ~/.local/bin/binary-sign-tool
```

最后在`~/.zshrc`添加`export PATH=$HOME/.local/bin:$PATH`

## 保存签名脚本
把以下保存为`~/.local/bin/hm-sign-all.sh`， 并执行`chmod +x ~/.local/bin/hm-sign-all.sh`
```shell
#!/bin/sh

# 递归查询当前目录及其子目录下的所有文件
find . -type f | while read -r file; do
    # 使用 file 命令检查文件类型
    if file "$file" | grep "shared object"; then
        echo "Found executable or shared object: $file"
        
        # 确保文件具有可执行权限
        chmod +x "$file"
        
        # 签名文件
        echo "Signing file: $file"
        binary-sign-tool sign -inFile "$file" -outFile "$file" -selfSign 1
    fi
done
```

## 从CodeArts IDE提取git
打开IDE, 随便创建一个项目打开，在终端执行以下命令
```
# 创建安装目录
mkdir -p ~/.local/opt

# 切换到安装目录， 并复制git
cd ~/.local/opt
cp -r /data/app/git.org/git_1.2/ . 

# 对git可执行文件签名
hm-sign-all.sh

# 创建bin的软件链接
ln -s $HOME/.local/opt/git_1.2/bin/git $HOME/.local/bin/ 
ln -s $HOME/Users/currentUser/.local/opt/git_1.2/bin/git-lfs $HOME/.local/bin/
```

## 配置git环境
在`~/.zshrc`添加以下内容
```shell
# git
export GIT_EXEC_PATH=$HOME/.local/opt/git_1.2/libexec/git-core
export GIT_TEMPLATE_DIR=$HOME/.local/opt/git_1.2/share/git-core/templates
```
## 测试
可以看到，可以正常clone仓库
```shell
➜ cd Documents/DevEcoStudioProjects 																																																																																																																																														✓
YSTYLE ❯ [10:35] ❯ ~/Documents/DevEcoStudioProjects
➜ git clone https://github.com/ystyle/paimon.git																																																																																																																																		✓
Cloning into 'paimon'...
remote: Enumerating objects: 99, done.
remote: Counting objects: 100% (99/99), done.
remote: Compressing objects: 100% (68/68), done.
remote: Total 99 (delta 19), reused 94 (delta 16), pack-reused 0 (from 0)
Receiving objects: 100% (99/99), 2.59 MiB | 3.19 MiB/s, done.
Resolving deltas: 100% (19/19), done.
YSTYLE ❯ [10:36] ❯ ~/Documents/DevEcoStudioProjects
➜ cd paimon 																																																																																																																																																																						✓
YSTYLE ❯ [10:47] ❯ ~/Documents/DevEcoStudioProjects/paimon
➜ git status																																																																																																																																																																						✓
fatal: detected dubious ownership in repository at '/storage/Users/currentUser/Documents/DevEcoStudioProjects/paimon'
To add an exception for this directory, call:

								git config --global --add safe.directory /storage/Users/currentUser/Documents/DevEcoStudioProjects/paimon
YSTYLE ❯ [10:47] ❯ ~/Documents/DevEcoStudioProjects/paimon
➜ git config --global --add safe.directory /storage/Users/currentUser/Documents/DevEcoStudioProjects/paimon																																																																			✗ 128
YSTYLE ❯ [10:47] ❯ ~/Documents/DevEcoStudioProjects/paimon
➜ git status																																																																																																																																																																						✓
On branch master
Your branch is up to date with 'origin/master'.

nothing to commit, working tree clean
YSTYLE ❯ [10:47] ❯ ~/Documents/DevEcoStudioProjects/paimon
➜ git log  																																																																																																																																																																							✓
error: cannot run less: No such file or directory
commit a0dffbac91fab1d1da50709d9e4b34f5a1ef0771 (HEAD -> master, tag: 2025-10-20, origin/master, origin/HEAD)
Author: ystyle <lxy5266@live.com>
Date:   Mon Oct 20 14:06:30 2025 +0800

    feat: 优化代码
```
