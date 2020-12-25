---
title: 使用Docker快速上手鸿蒙
date: 2020-09-11 01:00:26
updated: 2020-12-25 16:40:26
tags:
- 鸿蒙
- docker
categories: 系统
permalink: compile-openharmony-indokcer
---

### 准备

- 在机器上安装好Docker

### 编译鸿蒙系统镜像

- 打开终端执行以下命令

```shell
mkdir ~/OpenHarmony
cd ~/OpenHarmony
docker run --rm -ti -v ${PWD}/out:/OpenHarmony/out ystyle/open-harmony
```

- 编译成功后各镜像在out目录下面, 默认编译的是`Hi3861`开发板的系统镜像, 可自行烧录到固定测试
- 如果要编译其它板子可以设置dokcer镜像的环境变量`HARDWARE` 目前支持: `wifiiot`、`ipcamera_hi3516dv300`、`ipcamera_hi3518ev300`

### 更新代码并编译
```
mkdir ~/OpenHarmony
cd ~/OpenHarmony
docker run --rm -ti -e HARDWARE=ipcamera_hi3516dv300 -v ${PWD}/out:/OpenHarmony/out ystyle/open-harmony bash
repo sync -c
python build.py ${HARDWARE} -b debug
```

### 编写应用程序

- 示例在这[Hi3861开发板第二个示例程序](https://openharmony.gitee.com/openharmony/docs/blob/master/quick-start/Hi3861%E5%BC%80%E5%8F%91%E6%9D%BF%E7%AC%AC%E4%BA%8C%E4%B8%AA%E7%A4%BA%E4%BE%8B%E7%A8%8B%E5%BA%8F.md)
- 创建一个代码目录: `my_first_app`
- 新建文件`hello_world.c`

  ```c
  #include "ohos_init.h"
  #include "ohos_types.h"

  void HelloWorld(void)
  {
      printf("[DEMO] Hello world.\n");
  }
  SYS_RUN(HelloWorld);
  ```
- 新建文件`BUILD.gn`

  ```c
  static_library("myapp") {
    sources = [
        "hello_world.c"
    ]
    include_dirs = [
        "//utils/native/liteos/include"
    ]
  }
  ```
- 新建文件`APP_BUILD.gn`
- ```c
  import("//build/lite/config/component/lite_component.gni")

  lite_component("app") {
      features = [
          "my_first_app:myapp",
      ]
  }
  ```
- 现在的目录结构为

  ```shell
  .
  ├── APP_BUILD.gn
  ├── BUILD.gn
  └── hello_world.c
  ```

### 编译代码

```shell
docker run --rm \
  -e HARDWARE=wifiiot \
  -v ${PWD}/out:/OpenHarmony/out \
  -v ${PWD}/APP_BUILD.gn:/OpenHarmony/applications/sample/wifi-iot/app/APP_BUILD.gn \
  -v ${PWD}:/OpenHarmony/applications/sample/wifi-iot/app/my_first_app \
  ystyle/open-harmony
```

> 编译后的文件在out目录
```
.
├── APP_BUILD.gn
├── BUILD.gn
├── hello_world.c
└── out
    └── wifiiot
```


### 其它问题
- 如果实际开发，建议直接替换掉 整个`/OpenHarmony/applications/sample/wifi-iot/app/` 目录, 目录里边的都是示例代码.
- 如果要修改启动编译的命令的话，可以写好shell 脚本， run时指定cmd命令
  - 构建命令为: `python build.py ${HARDWARE} -b debug`
  - `docker run --rm -v ${PWD}/mybuild.sh:/OpenHarmony/mybuild.sh ystyle/open-harmony /OpenHarmony/mybuild.sh`
- 更新鸿蒙代码: 用修改镜像启动命令的方法，在`/OpenHarmony`目录执行`repo sync -c` 命令
- 其它驱动开发或系统组件开发也可以用挂载的方式把工程目录映射到容器，开发并编译

### 本文所使用Docker镜像的dockerfile文件
>参考`@keithyau`[所写的Dockerfile](https://openharmony.gitee.com/keithyau/build_lite/blob/master/Dockerfile20.04)修改而来


```dockerfile
FROM ubuntu:20.04 AS build-env
LABEL version=2020-10-15

# Set your hardware
ENV HARDWARE=wifiiot
# Prevent interactive
ENV DEBIAN_FRONTEND=noninteractive

# Setting up the build environment
RUN sed -i 's/archive.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && \
    apt-get clean -y && \
    apt-get -y update && \
    apt-get remove python* -y && \
    apt-get install git curl build-essential libdbus-glib-1-dev libgirepository1.0-dev -y && \
    apt-get install zip libncurses5-dev pkg-config -y && \
    apt-get install python3-pip -y && \
    apt-get install scons dosfstools mtools mtd-utils default-jdk default-jre -y && \
    rm -rf /var/lib/apt/lists/*

# Setup python
# Make sure python install on the right python version path
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.8 1 && \
    pip3 install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple && \
    pip3 install ninja kconfiglib pycryptodome ecdsa -i https://mirrors.aliyun.com/pypi/simple && \
    pip3 install six --upgrade --ignore-installed six -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    rm -rf /var/cache/apt/archives

#Fix Dash
RUN rm -rf /bin/sh && \
    ln -s /bin/bash /bin/sh

#Setup gn
ENV PATH /tools/gn:$PATH
RUN mkdir /tools && \
    cd /tools && \
    curl -LO https://repo.huaweicloud.com/harmonyos/compiler/gn/1523/linux/gn.1523.tar && \
    tar xvf /tools/gn.1523.tar && \
    rm -rf /tools/gn.1523.tar

#Setup LLVM
#ADD ./llvm-linux-9.0.0-34042.tar /tools
ENV PATH /tools/llvm/bin:$PATH
RUN cd /tools && \
    curl -LO https://repo.huaweicloud.com/harmonyos/compiler/clang/9.0.0-34042/linux/llvm-linux-9.0.0-34042.tar && \
    tar xvf /tools/llvm-linux-9.0.0-34042.tar && \
    rm -rf /tools/llvm-linux-9.0.0-34042.tar

#Setup hc-gen
ENV PATH /tools/hc-gen:$PATH
RUN cd /tools && \
    curl -LO https://repo.huaweicloud.com/harmonyos/compiler/hc-gen/0.65/linux/hc-gen-0.65-linux.tar && \
    tar xvf /tools/hc-gen-0.65-linux.tar && \
    rm -rf /tools/hc-gen-0.65-linux.tar
    
    
#Setup hmos_app_packing_tool and hapsigntool // 必需是这目录，编译脚本写死了
ENV PATH /root/developtools/:$PATH
RUN mkdir /root/developtools/ && cd /root/developtools/ && \
    curl -LO https://repo.huaweicloud.com/harmonyos/develop_tools/hmos_app_packing_tool.jar && \
    curl -LO https://repo.huaweicloud.com/harmonyos/develop_tools/hapsigntoolv2.jar

#Setup gcc_riscv32
ENV PATH /tools/gcc_riscv32/bin:$PATH
RUN cd /tools && \
    curl -LO http://tools.harmonyos.com/mirrors/gcc_riscv32/7.3.0/linux/gcc_riscv32-linux-7.3.0.tar.gz && \
    tar xvf /tools/gcc_riscv32-linux-7.3.0.tar.gz && \
    rm -rf /tools/gcc_riscv32-linux-7.3.0.tar.gz

#Create work dir
RUN mkdir /OpenHarmony
WORKDIR /OpenHarmony

# Gitee Repo tool and download
# Make sure requests install at the right location
RUN curl https://gitee.com/oschina/repo/raw/fork_flow/repo-py3 > /usr/bin/repo && \
    chmod a+x /usr/bin/repo && \
    pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple requests

#Download source, update to your info
RUN git config --global user.email "lxy5266@live.com" && \
    git config --global user.name "ystyle" && \
    git config --global color.ui false && \
    git config --global credential.helper store && \
    repo init -u https://gitee.com/openharmony/manifest.git -b master --repo-branch=stable --no-repo-verify && \
    repo sync -c

# compile
ENV LANGUAGE en
ENV LANG en_US.utf-8
RUN export|grep LANG
CMD ["/bin/bash", "-c", "python build.py ${HARDWARE} -b debug"]

```
