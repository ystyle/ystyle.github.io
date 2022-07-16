---
title: Dokcer编译方舟引擎（MapleEngine）
date: 2020-07-21 10:46:26
updated: 2020-08-6 15:08:26
tags:
- 编译器
- 方舟
- 方舟多语言调试器
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
FROM ubuntu:16.04
MAINTAINER https://www.openarkcompiler.cn

# Setting up the build environment
RUN sed -i 's/archive.ubuntu.com/mirrors.163.com/g' /etc/apt/sources.list && \
    apt-get -y update && \
    apt install --no-install-recommends -y build-essential git wget clang cmake libffi-dev libelf-dev libunwind-dev \
        libssl-dev openjdk-8-jdk-headless unzip python-minimal python3 curl && \
    rm -rf /var/lib/apt/lists/*

# 在国内请反注释下行, 因为容器也是个单独的系统，所以别用127.0.0.1
#ENV http_proxy=http://192.168.3.81:1081 \ 
#    https_proxy=http://192.168.3.81:1081

# copy source
COPY . /maple_engine
WORKDIR /maple_engine

# custom java/lang/Object.java
RUN cd /maple_engine/maple_build/jar/ && \
    bash -c "cp /usr/lib/jvm/java-8-openjdk-amd64/jre/lib/{rt.jar,jce.jar,jsse.jar,charsets.jar} . " && \
    mkdir -p java/lang/ && \
    curl -L http://hg.openjdk.java.net/jdk8u/jdk8u/jdk/raw-file/jdk8u265-b01/src/share/classes/java/lang/Object.java > java/lang/Object.java && \
    sed -i '/public class Object {/a\long reserved_1; int reserved_2;' java/lang/Object.java && \
    javac -target 1.8 -g java/lang/Object.java && \
    jar uf rt.jar java/lang/Object.class && \
    rm -rf java

# compile
RUN bash -c "source ./envsetup.sh && ./maple_build/tools/build-maple.sh && ./maple_build/tools/build-libcore.sh && rm -rf /maple_engine/maple_build/out/*"
```

### 编译方舟引擎
>方舟编译器，也会一起编译，注意： 编译libjava时会占用25G左右的内存，不足25G建议添加swap分区

>本人机器是16G内存，20G的SSD swap分区

```shell
docker build -t ystyle/maple-engine .
```
![编译占用](https://dll.ystyle.top/images/2020-07/44F09FD9B6FF040264D4D5D02EBD079E.jpg)

### 测试
>[镜像](https://hub.docker.com/r/ystyle/maple-engine)已经推送到[docker hub](https://hub.docker.com/r/ystyle/maple-engine), 可以直接使用下面的镜像编译hello world或其它软件

```
docker run --rm -ti ystyle/maple-engine bash
# 设置基础环境
source ./envsetup.sh
# 编译java hello world
cd ./maple_build/examples/HelloWorld
$MAPLE_BUILD_TOOLS/java2asm.sh HelloWorld.java
# 生成把.s文件编译为.so
$MAPLE_BUILD_TOOLS/asm2so.sh HelloWorld.s
# 运行软件
$MAPLE_BUILD_TOOLS/run-app.sh -classpath ./HelloWorld.so HelloWorld
```

![编译执行结果](https://dll.ystyle.top/images/2020-07/2020-07-22_10-35.png)


### 调试应用程序
- [方舟多语言调试器介绍](https://gitee.com/openarkcompiler-incubator/maple_engine/wikis/%E6%96%B9%E8%88%9F%E5%A4%9A%E8%AF%AD%E8%A8%80%E8%B0%83%E8%AF%95%E5%99%A8?sort_id=2711073)
- [方舟多语言调试器项目说明](https://gitee.com/openarkcompiler-incubator/maple_engine/tree/master/maple_debugger)
- [方舟多语言调试器用户手册](https://gitee.com/openarkcompiler-incubator/maple_engine/blob/master/maple_debugger/UserReference.md)


```
docker run --rm -ti ystyle/maple-engine:gdb bash
# 设置jdk源码路径 $JDK_SRC 为本地的openjdk源码
# docker run --rm -ti -v ${JDK_SRC}:/root/my_openjdk8/jdk/src/ ystyle/maple-engine:gdb bash
# 设置基础环境
source ./envsetup.sh
# 编译java hello world
cd ./maple_build/examples/HelloWorld
$MAPLE_BUILD_TOOLS/java2asm.sh HelloWorld.java
# 生成把.s文件编译为.so
$MAPLE_BUILD_TOOLS/asm2so.sh HelloWorld.s
# 调试应用程序
"$MAPLE_BUILD_TOOLS"/run-app.sh -gdb -classpath ./HelloWorld.so HelloWorld
```
