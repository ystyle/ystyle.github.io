---
title: Dokcer编译方舟引擎（MapleEngine）
date: 2020-07-21 10:46:26
updated: 2020-08-6 15:08:26
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
    apt-get -y install openjdk-8-jdk-headless mercurial curl

# 在国内请反注释下行, 因为容器也是个单独的系统，所以别用127.0.0.1
#ENV http_proxy=http://192.168.3.81:1081 \ 
#    https_proxy=http://192.168.3.81:1081

RUN hg clone http://hg.openjdk.java.net/jdk8u/jdk8u -r jdk8u252-b09 ~/my_opejdk8 && \
    cd ~/my_opejdk8 && bash ./get_source.sh && \
    sed -i '/public class Object {/a\long reserved_1; int reserved_2;' ~/my_opejdk8/jdk/src/share/classes/java/lang/Object.java

RUN mkdir out && cd out && \
    bash -c "cp /usr/lib/jvm/java-8-openjdk-amd64/jre/lib/{rt.jar,jce.jar,jsse.jar,charsets.jar} . " && \
    mkdir -p java/lang/ && \
    cp ~/my_opejdk8/jdk/src/share/classes/java/lang/Object.java java/lang/ && \
    javac -target 1.8 -g java/lang/Object.java && \
    jar uf rt.jar java/lang/Object.class

FROM ubuntu:16.04 AS build-env
MAINTAINER https://www.openarkcompiler.cn

# Setting up the build environment
RUN sed -i 's/archive.ubuntu.com/mirrors.163.com/g' /etc/apt/sources.list && \
    apt-get -y update && \
    apt install --no-install-recommends -y build-essential git wget clang cmake libffi-dev libelf-dev libunwind-dev \
        libssl-dev openjdk-8-jdk-headless unzip python-minimal python3 && \
    rm -rf /var/lib/apt/lists/*

# 在国内请反注释下行, 因为容器也是个单独的系统，所以别用127.0.0.1
#ENV http_proxy=http://192.168.3.81:1081 \ 
#    https_proxy=http://192.168.3.81:1081

# copy source
COPY . /maple_engine
WORKDIR /maple_engine

COPY --from=build-jdk-env /out/*.jar /maple_engine/maple_build/jar/


# compile
RUN ["/bin/bash", "-c", "source ./envsetup.sh && ./maple_build/tools/build-maple.sh && ./maple_build/tools/build-libcore.sh && cd /maple_engine/maple_build/out/x86_64/ && rm `ls * |egrep -v '(libcore.mpl|libcore.mplt|mrt_module_init.o|orig-libcore.mplt)'` && rm libcore.mpl.mir.mpl"]
```

### 编译方舟引擎
>方舟编译器，也会一起编译，注意： 编译libjava时会占用25G左右的内存，不足25G建议添加swap分区

>本人机器是16G内存，20G的SSD swap分区

```shell
docker build -t ystyle/maple-engine .
```
![编译占用](https://dl.ystyle.top/images/2020-07/44F09FD9B6FF040264D4D5D02EBD079E.jpg)

### 测试

```
# 镜像已经推送到docker hub, 可以直接使用下面的镜像编译hello world或其它软件
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

![编译执行结果](https://dl.ystyle.top/images/2020-07/2020-07-22_10-35.png)
