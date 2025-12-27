---
title: 鸿蒙PC Matebook Pro上安装仓颉编译器每日构建版
date: 2025-12-27 15:00:00
updated: 2025-12-27 15:00:00
tags:
- 鸿蒙
- 鸿蒙PC
- 仓颉
- cangjie
- cangjie-lang
- matebook pro
categories: 软件
permalink: matebookpro-run-cangjie-compiler
---

![使用示例](https://dll.ystyle.top/images/2025-12/5e398f57bb264562850d933612e65a3d.png)

## 准备工作
- 在鸿蒙PC上使用应用商店安装CodeArts IDE
- 下载仓颉编译器每日构建版本: [cangjie-sdk-ohos-aarch64-1.1.0-alpha.2025xxxxxxxxxxxxx.tar.gz](https://gitcode.com/Cangjie/nightly_build/releases)

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

## 安装仓颉编译器
- 把下载的仓颉编译器复制到个人目录(文件管器和下载目录同级)
- 打开终端解压 `tar -xzf cangjie-sdk-ohos-aarch64-1.1.0-alpha.2025xxxxxxxxxxxxx.tar.gz` 换自己下载的版本
- 打开`cangjie/envsetup.sh`把首行的`#!/bin/bash`换成`#!/bin/sh`
- 把以下脚本保存为`sign-cangjie.sh`并复制到`cangjie`目录下和`envsetup.sh`同级
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
- 在终端切换到`cangjie`目录下，执行`chmod +x sign-cangjie.sh` 并执行 `./sign-cangjie.sh`
- 终端切换到`third_party/llvm/bin` 目录， 执行 `rm ld.lld && cp lld ld.lld`
  - 这一步是为了解决 cjc 编译过程中找不到`ld.lld`的问题， 原因是仓颉编译器看不到软链接的 `ld.lld`


## 使用仓颉编译器
现在就可以按仓颉教程的两种方法使用仓颉了
- 第一种，临时使用
  - 打开终端 `source ~/.cangjie/envsetup.sh` 然后就可以在当前终端窗口执行`cjc -v`

- 第二种，永远使用
  - 把`source $HOME/.cangjie/envsetup.sh` 添加到 `~/.zshrc` 里，之后打开的新终端都可以使用仓颉命令了

## 编译并执行项目
- 写一个`hello_world.cj`
```cj
main(){
	println("你好，仓颉\n你好鸿蒙")
}
```
- 编译 `cjc hello_world.cj`
- 签名 `binary-sign-tool sign -inFile "./main" -outFile "./main-signed" -selfSign 1`
- 授权 `chmod +x ./main-signed`
- 执行 `./main-signed` , 如无意外就能看到输出了

