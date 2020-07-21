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
#ENV http_proxy=http://192.168.3.81:1081 \ 
#    https_proxy=http://192.168.3.81:1081

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
    apt install -y build-essential git wget clang cmake libffi-dev libelf-dev libunwind-dev \
        libssl-dev openjdk-8-jdk-headless unzip python-minimal python3

# 在国内请反注释下行, 因为容器也是个单独的系统，所以别用127.0.0.1
#ENV http_proxy=http://192.168.3.81:1081 \ 
#    https_proxy=http://192.168.3.81:1081

# copy source
COPY . /maple_engine
WORKDIR /maple_engine

COPY --from=build-jdk-env /root/my_opejdk8/build/linux-x86_64-normal-server-release/images/lib/rt.jar /maple_engine/maple_build/jar/
COPY --from=build-jdk-env /root/my_opejdk8/build/linux-x86_64-normal-server-release/images/lib/jce.jar /maple_engine/maple_build/jar/
COPY --from=build-jdk-env /root/my_opejdk8/build/linux-x86_64-normal-server-release/images/lib/jsse.jar /maple_engine/maple_build/jar/
COPY --from=build-jdk-env /root/my_opejdk8/build/linux-x86_64-normal-server-release/images/lib/charsets.jar /maple_engine/maple_build/jar/
COPY --from=build-jdk-env /root/my_opejdk8/build/linux-x86_64-normal-server-release/jdk/lib/amd64/libjava.so /maple_engine/maple_runtime/lib/x86_64/
COPY --from=build-jdk-env /root/my_opejdk8/build/linux-x86_64-normal-server-release/jdk/lib/amd64/server/libjvm.so /maple_engine/maple_runtime/lib/x86_64/
COPY --from=build-jdk-env /root/my_opejdk8/build/linux-x86_64-normal-server-release/jdk/lib/amd64/libverify.so /maple_engine/maple_runtime/lib/x86_64/

# compile
RUN ["/bin/bash", "-c", "source ./envsetup.sh && ./maple_build/tools/build-maple.sh && ./maple_build/tools/build-libcore.sh"]

```

### 编译方舟引擎
```shell
docker build -t ystyle:maple_engine .
```

### 测试
```
# 镜像已经推送到docker hub, 如果出现core-dump的话，等方舟更新并重新编译
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
