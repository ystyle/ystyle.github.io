---
title: 移植lua到鸿蒙 - 首个移植成功的编程语言
date: 2020-11-07 23:52:26
updated: 2020-11-07 23:52:26
tags:
- 编程语言
- 鸿蒙
- lua
categories: 软件
permalink: porting-Lua-to-openharmony
---

### 惯例先放hello world
![hello world](https://dl.ystyle.top/images/2020-11/WindowsTerminal_2020-11-07_23-28-08.png)

- 本项目地址: https://gitee.com/ystyle/lua
- [下载二进制文件](https://gitee.com/ystyle/lua/releases/v5.4.2)


### 准备环境
- 安装 docker
- docker pull ystyle/open-harmony

ps: 本文使用与鸿蒙系统一同编译的方法。 如果自己有本地环境，可以把lua项目放鸿蒙代码目录里(或者使用软接连)

### 下载lua官方代码
```shell
mkdir -p ~/code/ohos/
cd ~/code/ohos/
git clone https://github.com/lua/lua.git
```

### 编写BUILD.gn文件
>因为要与系统一起编译， 为了方便，直接用替换掉示例的方法，这样就只需要写一个BUILD.gn就好了


```gn
# Copyright (c) 2020 YSTYLE(lxy5266@live.com)
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import("//build/lite/config/component/lite_component.gni")
import("//build/lite/ndk/ndk.gni")

static_library("hello_world") {
    sources = [
        "lapi.c",
        "lauxlib.c",
        "lbaselib.c",
        "lcode.c",
        "lcorolib.c",
        "lctype.c",
        "ldblib.c",
        "ldebug.c",
        "ldo.c",
        "ldump.c",
        "lfunc.c",
        "lgc.c",
        "linit.c",
        "liolib.c",
        "llex.c",
        "lmathlib.c",
        "lmem.c",
        "loadlib.c",
        "lobject.c",
        "lopcodes.c",
        "loslib.c",
        "lparser.c",
        "lstate.c",
        "lstring.c",
        "lstrlib.c",
        "ltable.c",
        "ltablib.c",
        "ltests.c",
        "ltm.c",
        "lua.c",
        "lundump.c",
        "lutf8lib.c",
        "lvm.c",
        "lzio.c"
    ]

    include_dirs = [
        "include",
    ]
}

lite_component("camera_app") {
    target_type = "executable"

    features = [
        ":hello_world",
    ]
}

ndk_lib("app_sample") {
    deps = [
        ":hello_world"
    ]
    head_files = [
        "include"
    ]
}

```

>static_library里的source参照lua/makefile

### 编译脚本
创建编译脚本`build-ohos.sh`文件

```shell
cd ~/code/ohos/lua
touch build-ohos.sh
chmod +x build-ohos.sh
```

文件内容如下
```shell
set -e
rm -rf ./out ./bin
docker run --rm -ti \
  -e HARDWARE=ipcamera_hi3516dv300 \
  -v ${PWD}/out:/OpenHarmony/out \
  -v ${PWD}:/OpenHarmony/applications/sample/camera/app \
  ystyle/open-harmony
mkdir -p ./bin
cp ./out/ipcamera_hi3516dv300/bin/camera_app ./bin/lua
tar -zcf lua-5.4.2-ohos.tar.gz ./bin
echo 'build success!'
```
与鸿蒙一起编译，这里使用我之前的[docker镜像](https://ystyle.top/2020/09/10/compile-openharmony-indokcer/)
```shell
cd ~/code/ohos/lua
./build-ohos.sh
# 看到 ohos ipcamera_hi3516dv300 build success! build success! 就编译成功了。

```



>编译后软件在鸿蒙的 ./out/ipcamera_hi3516dv300/bin/camera_app  
>脚本会把lua单独打包出来  
>单独的lua可执行文件在bin目录 

### 演示
![io操作](https://dl.ystyle.top/images/2020-11/WindowsTerminal_2020-11-07_23-46-45.png)

![官方测试用例1](https://dl.ystyle.top/images/2020-11/WindowsTerminal_2020-11-07_23-48-58.png)

![官方测试用例2](https://dl.ystyle.top/images/2020-11/WindowsTerminal_2020-11-07_23-50-10.png)

![官方测试用例3](https://dl.ystyle.top/images/2020-11/WindowsTerminal_2020-11-07_23-51-01.png)
