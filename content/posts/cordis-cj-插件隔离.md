---
title: "cordis-cj：静态语言怎么做出能卸载的插件"
subtitle: 进程隔离、可逆效果，和一套把 IPC 藏起来的宏
date: 2026-11-12 10:00:00
lastmod: 2026-11-12 10:00:00
slug: cordis-cj-plugin-isolation
categories:
  - 软件
tags:
  - Cangjie
  - cordis
  - 插件系统
  - 进程隔离
  - 架构
---

<p align="center"><strong>cordis-cj 源码拆解</strong></p>

<p align="center"><em>卸载这件事，静态语言从根上就做不了</em></p>

> 动态语言的插件系统可以「加载 → 卸载 → 再加载」，
> 静态语言不行——不是实现得不够好，是运行时结构不允许。
> 这篇讲 [cordis-cj](https://atomgit.com/ystyle/cordis-cj) 绕开这个限制的办法，以及绕开之后要付的账。

## 一、卸载不掉的东西

JavaScript 里卸载一个模块，做法是删掉缓存里的引用，让 GC 回收。Node 的 `require.cache` 就是干这个的。

仓颉不行。它编译成**静态机器码**，模块加载后，里面的**全局变量、静态初始化、注册表都落在进程内存里**。你就算把代码段「卸掉」，那些数据还在——而且没有任何机制能安全地把它们重置回初始状态。

这不是仓颉独有的问题。C 的 `dlopen`/`dlclose` 在理论和实践之间差着一大截：POSIX 标准里 `dlclose` 甚至**允许什么都不做**；GNU ld 的文档明说，带 `UNIQUE` 符号或 `dlopen` 了带 TLS 的库时，`dlclose` 之后那个 handle 依然有效。

> 换句话说：**「卸载」在原生程序里本来就只是个建议，不是承诺。**

所以静态语言写插件系统，最后都撞同一面墙。撞法有两种：

| 做法 | 代价 |
| --- | --- |
| 假装能卸载（重置状态） | 要穷举所有全局状态，漏一个就是幽灵 bug |
| 干脆不能卸载（只重启进程） | 每次改插件都要重启宿主，热更新没了 |

cordis-cj 选了第三条：**插件不跑在宿主进程里**。

## 二、卸载 = 杀进程

思路很直接：如果「卸载」的定义是「让这些代码和数据彻底消失」，那唯一可靠的方式是让**承载它们的东西**消失。

进程。`kill` 之后操作系统回收它的全部内存、文件描述符、线程——不需要插件配合，不会漏。

于是架构变成两层：

```
宿主进程（微内核，永不卸载）
  ├─ 调和器：读配置、算 diff
  └─ 进程管理：拉起 / 杀掉 / 探活
        │  stdio 管道 / Unix socket
        ▼
插件 A          插件 B          插件 C
（各自独立，崩溃不影响别人）
```

这个方案解决了三件事，而且都不需要插件作者操心：

- **资源回收**：`kill` 就是全部回收，不依赖插件写 `dispose`
- **故障隔离**：一个插件崩了，宿主和别的插件都不知道
- **崩溃自愈**：宿主探活失败就重启，状态从配置文件重建

但天下没有白拿的好处。**跨进程之后，一次函数调用变成了消息往返。**

## 三、代价在三处

拆进程的账，主要记在三个地方。

### 握手

插件不能一启动就开始干活——它得先告诉宿主「我是谁、我提供哪些服务」，宿主才能把它接入路由表。

所以每个插件启动后第一件事是**握手**：

```
插件 → 宿主：
initialize(name, provides)
宿主 → 插件：ok，登记到 serviceIndex
插件 → 宿主：provide("echo", undo_id=uuid)
宿主：登记服务，记住 undo_id
```

这个 `undo_id` 不是随便加的。它对应**可逆效果**（revertible effects）：注册一个服务时，同时给出「怎么撤销这次注册」。宿主执行 `dispose(undo_id)` 时，插件按记录撤销——而不是插件自己猜要清理什么。

> 这个设计来自北大和 DeepSeek-AI 的一篇论文，cordis-cj 按它的语义实现。
> 要点是：**副作用在发生时就把「撤销方式」记下来**，而不是事后靠人回忆。

### 序列化

跨进程只能传字节。所以每个调用都要走 `JsonValue`。

这件事如果让插件作者手写，插件系统就没法用了：

```cangjie
// 每天写一百遍这种东西，谁都不想用
let args = ArrayList<JsonValue>()
args.add(JsonValue.Number(2.0))
args.add(JsonValue.Number(3.0))
let result = ctx.invoke(
    "calc", "add", args)
let n = match (result) {
    case JsonValue.Number(v) => v
    case _ => 0.0
}
```

所以 cordis-cj 提供了泛型版本，把序列化藏在类型后面：

```cangjie
// 业务代码只认仓颉类型，序列化是框架的事
let sum = ctx.invoke<AddRequest, Int64>(
    "calc", "add", [AddRequest(2, 3)])
```

`AddRequest` 实现 `JsonSerializable`，`Int64` 实现反序列化——框架在中间做转换，业务代码里看不到 `JsonValue`。

### 启动顺序

服务有依赖。插件 B 要用插件 A 提供的 `db` 服务，就必须后启动。

这件事不能靠配置里的书写顺序——那太脆弱了。所以调和器按 **`inject` / `provide` 声明做拓扑排序**：

```toml
[[plugins]]
id = "db"
provide = ["db"]

[[plugins]]
id = "cache"
provide = ["cache"]
inject = ["db"]      # 得等 db 起来
```

声明了 `inject`，宿主自然会把它排在提供者后面。**配置里不用写顺序，写依赖。**

## 四、把 IPC 藏起来

到这里，插件作者要面对的东西还是很多：写 `main`、处理握手、注册服务、解析参数……

cordis-cj 用宏把这层削掉了。一个完整的插件长这样：

```cangjie
@Plugin[]
public class MyPlugin {
    @Provide["echo"]
    public func echo(
        args: Array<JsonValue>)
        : JsonValue {
        if (args.size > 0) { args[0] }
        else { JsonValue.Null }
    }
}
```

`@Plugin[]` 自动生成 `main` 函数、握手流程、服务注册、`invoke` 路由分发。`@Provide["echo"]` 声明这个方法对外是 `echo` 服务。

**插件作者看到的是一个普通类，不是一套 RPC 脚手架。**

不过宏不是唯一的路。README 里给了两种写法：

| 写法 | 适合谁 | 代价 |
| --- | --- | --- |
| 宏（`@Plugin`） | 框架内置插件 | 宏包必须与调用方**同模块**（见后文） |
| 显式 API（`PluginRuntime.run`） | 外部插件作者 | 手写 `main`，但不受宏的跨模块限制 |

**两种写法是给工具链缺陷留的退路**，后面会讲。

### 双传输，插件无感

进程间通信有两种方式，cordis-cj 都支持：

| 传输 | 帧格式 | 适用 |
| --- | --- | --- |
| `stdio`（默认） | 换行分帧 | 简单，管道天然有序 |
| `uds` | Content-Length 分帧 | Unix socket，能传更复杂的东西 |

切换靠配置里的一个字段。插件侧**完全不用改**：

```cangjie
main(): Int64 {
    PluginRuntime.run("my-plugin", [],
        ["echo"], handler)
    return 0
}
```

`run()` 内部会自己看命令行有没有 `--uds <path>`，有就走 UDS，没有就 stdio。所以同一份插件代码两种模式都能跑。

> **传输模式是部署决定，不该污染插件代码**。
> 如果插件得知道自己跑在哪种传输上，那换传输就等于改所有插件。

## 五、调和器：配置说了算

剩下最后一件事：怎么让「期望状态」和「实际状态」对上。

cordis-cj 用的是声明式调和——你只写「该有哪些插件」，不写「怎么启动」：

```toml
interval = 5
transport = "stdio"

[[plugins]]
id = "my-plugin"
source = "./target/release/bin/my_plugin"
provide = ["echo"]
enabled = true
```

宿主每 5 秒跑一轮，做四件事：

```
读配置 → 算 diff → 拓扑排序
→ 启动新的 → 先加后删 → 崩溃自愈
```

几个设计细节：

**「先加后删」有代价。** 如果要换一个插件的版本，先杀旧的再起新的，中间会有一段服务不可用；先起新的再杀旧的，切换是平滑的。代价是短时间内两套并存，所以只在**服务不冲突**时成立。

**探活是独立的。** 每 30 秒 ping 一次，超时就重启。这跟调和周期分开——配置 5 秒一轮是为了响应变化，探活 30 秒一轮是为了发现假死。

**崩溃自愈不消耗人。** 插件崩了不需要运维介入，下一轮调和就会把它拉起来。

> 这套东西的哲学是：**人只维护「想要什么」，机器负责「怎么达到」。**
> 配置写错时宿主会报错，但配置漂移（有人手动杀了进程）会被自动纠正。

## 六、一个工具链层面的坑

写宏的时候撞了一个 cjpm 的问题，值得单独记：**带 `organization` 的宏包，跨模块依赖时宏不会链接到调用方**。

```cangjie
// cordis_plugin 模块里的宏包
macro package ystyle::cordis_plugin.macros

public macro Plugin(
    attr: Tokens, input: Tokens): Tokens {
    ...
}
```

独立模块的调用方 `import ystyle::cordis_plugin.macros.Plugin` 之后：

```cangjie
// 报错：undeclared identifier 'plugin'
@Plugin[]
public class SimplePlugin {}
```

编译不通过。**把 cjpm.toml 里的 `organization` 去掉，立刻就好了。**

这个坑的麻烦之处在于：报错信息（`undeclared identifier`）**完全不指向真实原因**。你会以为是宏写得不对、导入写错了、语法有问题——实际上是包管理器没把宏的 `.so` 传下去。

排查了很久才定位到，**结论写进了 README**：`cordis_plugin.macros` 和调用方必须同模块。于是才有了前面那个「两种写法」的设计——宏给内置插件用，外部插件走显式 API。

> 一个工具链的缺陷，最终变成了一个 API 的形状。

## 七、还有一条路：用脚本写插件

进程隔离的另一个好处是：**插件进程里跑什么，宿主管不着。**

所以 cordis-cj 支持 xisp 脚本插件——插件不是编译好的二进制，而是一个 Lisp 脚本：

```lisp
(define (echo args)
  (if (> (length args) 0)
      (car args)
      'null))
```

`cordis_xisp` 运行时把宿主能力注入脚本环境（`cordis::*` 命名空间），脚本直接调用 `provide` / `invoke` / `log`。

这条路的代价是性能（解释执行），好处是**改插件不用重新编译**。对一个热更新场景，这个交换很划算。

## 八、边界

这套东西做不到这些：

| 限制 | 说明 |
| --- | --- |
| 不做跨机 | 进程隔离只在一个机器上；跨机得自己加网络层 |
| 插件只增不热改 | 改插件代码要换二进制 + 重启该插件（调和器能做，但不是热补丁） |
| 序列化有成本 | 大对象跨进程传会慢，设计服务接口时要考虑粒度 |
| 微内核不卸载 | 宿主进程本身是单体，它崩了整个都崩 |
| 宏有跨模块限制 | 见上节；外部插件只能走显式 API |

最后一条值得展开：**架构上的「可卸载」不等于「随时能改」**。

进程隔离让你能安全地**停止**一个插件，但要让新版本生效，还是得换文件、重启进程。这跟某些动态语言那种「运行时热替换类定义」完全是两回事。

## 九、小结

- **静态语言不能卸载模块**，这是运行时结构决定的，不是实现问题。`dlclose` 在原生程序里本来就只是个建议。
- **绕开的办法是换承载物**：插件跑在独立进程里，卸载就是杀进程，资源回收交给操作系统。
- **代价在握手、序列化、依赖顺序**三处。前两个用宏和泛型 API 藏起来，第三个用声明式依赖（`inject`/`provide`）自动解决。
- **可逆效果**：服务注册时就把撤销方式记下来（`undo_id`），而不是事后猜。
- **调和器让运维只写期望**：5 秒一轮 diff，探活 30 秒一轮，崩溃自愈不惊动人。
- **工具链缺陷会改变 API 形状**。宏的跨模块问题没有「修好」，而是变成了两套写法并存。

如果只能记一句：**当语言不给你某件事时，先想清楚「不给你」是在哪一层——如果在运行时，就换个承载它的东西。**

> 这个项目的插件语义对标 [Cordis](https://github.com/shigma/cordis)（DeepSeek Harness 的插件框架），
> 理论依据来自《Revertible Effects and Reactive Coeffects》。
> 它的下游用途之一，是把 agent 适配器从宿主进程里拆出去——
> 也就是 [uhp-cj](/2026/11/11/uhp-cj-protocol-implementation/) 那个服务端将来要做的事。
