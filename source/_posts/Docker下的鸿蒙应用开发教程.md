---
title: Docker下的鸿蒙应用开发教程
date: 2020-07-21 10:46:26
updated: 2020-08-6 15:08:26
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

> 编译后的代码在out目录

－ 如果项目大的话，建议直接替换掉 整个`/OpenHarmony/applications/sample/wifi-iot/app/` 目录, 下面的都是示例代码

### 其它问题

- 如果要修改启动编译的命令的话，可以写好shell 脚本， run时指定cmd命令
  - 构建命令为: `python build.py ${HARDWARE} -b debug`
  - `docker run --rm -v ${PWD}/mybuild.sh:/OpenHarmony/mybuild.sh ystyle/open-harmony /OpenHarmony/mybuild.sh`
- 更新鸿蒙代码: 用修改镜像启动命令的方法，在`/OpenHarmony`目录执行`repo sync -c` 命令
- 其它驱动开发或系统组件开发也可以用挂载的方式把工程目录映射到容器，开发并编译

