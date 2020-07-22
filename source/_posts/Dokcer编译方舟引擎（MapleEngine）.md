---
title: Dokcer编译方舟引擎（MapleEngine）
date: 2020-07-21 10:46:26
updated: 2020-07-21 22:50:26
tags:
- 编译器
- 方舟
categories: 软件
permalink: dokcer-compile-maple-engine
---

### 文档
- [方舟引擎发布公告](https://gitee.com/harmonyos/OpenArkCompiler/issues/I1OHE5)
- [官方文档 - 方舟引擎编译说明](https://gitee.com/openarkcompiler-incubator/maple_engine)
- [官方文档 - 构建Java 核心库](https://gitee.com/openarkcompiler-incubator/maple_engine/blob/master/maple_build/doc/build_OpenJDK8.md)

### Docker 文件
>复制到方舟引擎代码根目录, 文件名为Dockerfile

```dockerfile
FROM ubuntu:16.04 AS build-jdk-env
MAINTAINER https://www.openarkcompiler.cn
RUN sed -i 's/archive.ubuntu.com/mirrors.163.com/g' /etc/apt/sources.list && \
    apt-get -y update && \
    apt-get -y install curl mercurial build-essential cpio unzip zip libx11-dev libxext-dev libxrender-dev libxtst-dev libxt-dev && \
    apt-get -y install libcups2-dev && \
    apt-get -y install libfreetype6-dev libfreetype6 && \
    apt-get -y install libasound2-dev

# 在国内请反注释下行, 因为容器也是个单独的系统，所以别用127.0.0.1
ENV http_proxy=http://192.168.3.81:1081 \ 
    https_proxy=http://192.168.3.81:1081

ENV PATH=/java-se-7u75-ri/bin:${PATH}

RUN curl -OL https://download.java.net/openjdk/jdk7u75/ri/openjdk-7u75-b13-linux-x64-18_dec_2014.tar.gz && \
    tar zxf openjdk-7u75-b13-linux-x64-18_dec_2014.tar.gz && \
    hg clone http://hg.openjdk.java.net/jdk8/jdk8 ~/my_opejdk8 && \
    cd ~/my_opejdk8 && bash ./get_source.sh && \
    ln -s /usr/include/freetype2/ft2build.h /usr/include/ && \
    sed -i '/public class Object {/a\long reserved_1; int reserved_2;' ~/my_opejdk8/jdk/src/share/classes/java/lang/Object.java && \
    sed -i '67cs/ -\([^ I][^ ]*\)j/ -\1 -j/' hotspot/make/linux/makefiles/adjust-mflags.sh

RUN cd ~/my_opejdk8 && bash ./configure && export DISABLE_HOTSPOT_OS_VERSION_CHECK=ok; make all

FROM ubuntu:16.04 AS build-env
MAINTAINER https://www.openarkcompiler.cn

# Setting up the build environment
RUN sed -i 's/archive.ubuntu.com/mirrors.163.com/g' /etc/apt/sources.list && \
    apt-get -y update && \
    apt install --no-cache -y build-essential git wget clang cmake libffi-dev libelf-dev libunwind-dev \
        libssl-dev openjdk-8-jdk-headless unzip python-minimal python3 && \
    rm -rf /var/lib/apt/lists/*

# 在国内请反注释下行, 因为容器也是个单独的系统，所以别用127.0.0.1
ENV http_proxy=http://192.168.3.81:1081 \ 
    https_proxy=http://192.168.3.81:1081

# copy source
COPY . /maple_engine
WORKDIR /maple_engine

COPY --from=build-jdk-env /root/my_opejdk8/build/linux-x86_64-normal-server-release/images/lib/rt.jar /maple_engine/maple_build/jar/
COPY --from=build-jdk-env /root/my_opejdk8/build/linux-x86_64-normal-server-release/images/lib/jce.jar /maple_engine/maple_build/jar/
COPY --from=build-jdk-env /root/my_opejdk8/build/linux-x86_64-normal-server-release/images/lib/jsse.jar /maple_engine/maple_build/jar/
COPY --from=build-jdk-env /root/my_opejdk8/build/linux-x86_64-normal-server-release/images/lib/charsets.jar /maple_engine/maple_build/jar/

# compile
RUN ["/bin/bash", "-c", "source ./envsetup.sh && ./maple_build/tools/build-maple.sh && ./maple_build/tools/build-libcore.sh && cd /maple_engine/maple_build/out/x86_64/ && rm *.s && rm libcore.VtableImpl.mpl libcore.mpl.mir.mpl"]
```

### 编译方舟引擎
>方舟编译器，也会一起编译，注意： 编译libjava时会占用25G左右的内存，不足25G建议添加swap分区

>本人机器是16G内存，20G的SSD swap分区

```shell
docker build -t ystyle:maple_engine .
```
![编译占用](https://dl.ystyle.top/images/2020-07/44F09FD9B6FF040264D4D5D02EBD079E.jpg)

### 测试
>目前因为不知道要提取哪些文件， 所以里边打包了整个编译环境， 现在镜像非常大。 以后熟悉了再做个精简镜像。

```
# 镜像已经推送到docker hub, 可以直接使用下面的镜像编译hello world或其它软件
docker run --rm -ti ystyle:maple_engine bash
# 设备基础环境
source ./envsetup.sh
# 编译java hello world
cd ./maple_build/examples/HelloWorld
$MAPLE_BUILD_TOOLS/java2asm.sh HelloWorld.java
# 生成把.s文件编译为.so
$MAPLE_BUILD_TOOLS/asm2so.sh HelloWorld.s
# 运行软件
$MAPLE_BUILD_TOOLS/run-app.sh -classpath ./HelloWorld.so HelloWorld
```

![编译执行结果](https://dl.ystyle.top/images/2020-07/2020-07-22_10-35.png)
