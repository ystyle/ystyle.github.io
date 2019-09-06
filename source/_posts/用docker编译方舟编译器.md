---
title: 用docker编译方舟编译器
date: 2019-09-06 20:22:21
tags:
  - android
  - ark
  - linux
  - docker
categories: 编程
permalink: compile-ark
---

# 用docker编译方舟编译器
### 准备工作
1. 下载方舟源码: `git clone https://code.opensource.huaweicloud.com/HarmonyOS/OpenArkCompiler.git`
2. 需要安装docker
>生成出来的镜像以后可作为CI里编译方舟应用时的编译环境。  
>现在可用来做getting start的环境，简单编译环境的搭建



### dockerfile
> 把下面的dockerfile放到方舟源码根目录下

```dockerfile
FROM ubuntu:16.04 AS build-env
MAINTAINER https://www.openarkcompiler.cn

# Setting up the build environment
RUN sed -i 's/archive.ubuntu.com/mirrors.163.com/g' /etc/apt/sources.list && \
    dpkg --add-architecture i386 && \
    apt-get -y update && \
    apt-get -y dist-upgrade && \
    apt-get -y install curl git-core tar xz-utils unzip gnupg flex bison gperf build-essential ccache openjdk-8-jdk && \
    apt-get -y install zlib1g-dev libc6-dev-i386 lib32ncurses5-dev x11proto-core-dev libx11-dev lib32z-dev libgl1-mesa-dev libxml2-utils xsltproc lib32z1-dev qemu g++-multilib gcc-multilib libglib2.0-dev libpixman-1-dev linux-libc-dev:i386 && \
    apt-get -y install python3-paramiko python-paramiko python-jenkins python-requests python-xlwt && \
    apt-get -y install gcc-5-aarch64-linux-gnu g++-5-aarch64-linux-gnu aria2 && \
    mkdir -p /tools/ninja /tools/gn && \
    cd /tools && \
    curl -C - -LO http://releases.llvm.org/8.0.0/clang+llvm-8.0.0-x86_64-linux-gnu-ubuntu-16.04.tar.xz && \
    curl -LO https://github.com/ninja-build/ninja/releases/download/v1.9.0/ninja-linux.zip && \
    curl -L -o /tools/gn/gn https://archive.softwareheritage.org/browse/content/sha1_git:2dc0d5b26caef44f467de8120b26f8aad8b878be/raw/?filename=gn && \
    tar Jvxf /tools/clang+llvm-8.0.0-x86_64-linux-gnu-ubuntu-16.04.tar.xz -C /tools/ && \
    unzip /tools/ninja-linux.zip -d /tools/ninja/ && \
    chmod a+x /tools/gn/gn && \
    rm /tools/clang+llvm-8.0.0-x86_64-linux-gnu-ubuntu-16.04.tar.xz /tools/ninja-linux.zip && \
    rm -rf /var/cache/apt/archives

# copy source
COPY . /OpenArkCompiler
WORKDIR /OpenArkCompiler

# create symbolic link and
RUN mkdir -p /OpenArkCompiler/tools /OpenArkCompiler/tools/gn && \
    ln -s /tools/ninja /OpenArkCompiler/tools/ninja_1.9.0 && \
    ln -s /tools/gn/gn /OpenArkCompiler/tools/gn/gn && \
    ln -s /tools/clang+llvm-8.0.0-x86_64-linux-gnu-ubuntu-16.04 /OpenArkCompiler/tools/clang_llvm-8.0.0-x86_64-linux-gnu-ubuntu-16.04
# compile
RUN ["/bin/bash", "-c", "source build/envsetup.sh && make"]

# build final docker image
FROM ubuntu:16.04
RUN sed -i 's/archive.ubuntu.com/mirrors.163.com/g' /etc/apt/sources.list && \
    apt-get -y update && \
    apt-get install -y openjdk-8-jdk curl vim && \
    rm -rf /var/cache/apt/archives
COPY --from=build-env /OpenArkCompiler/out /OpenArkCompiler
VOLUME /OpenArkCompiler
ENV PATH=/OpenArkCompiler/bin:$PATH
CMD maple -h
```


### 编译
```shell
docker build -t ark:latest . 
```

### 测试
```shell
docker run --rm ark:latest
```

### 交互模式
```shell
docker run --rm -ti ark:latest bash
maple -h
```

>[方舟编译java代码教程](https://ystyle.top/2019/09/06/ark-test-axample/)
