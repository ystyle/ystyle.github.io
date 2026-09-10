---
title: 仓颉服务 - 忆时塔 OOM 追凶记
subtitle: 一次横跨六个仓颉自研库的排查
date: 2026-09-09 23:30:00
updated: 2026-09-09 23:30:00
permalink: chronomem-oom-hunt
categories:
  - 软件
tags:
  - Cangjie
  - MCP
  - badger-cj
  - json-rpc
  - 排查实录
hero:
  name: 仓颉服务-忆时塔 OOM 追凶记
  text: 一次横跨六个仓颉自研库的排查
  tagline: 从一条空 message 的异常，到 662 个 CLOSE_WAIT —— 长连接泄漏如何伪装成存储 OOM
  actions:
    - theme: brand
      text: 开始阅读
      link: '#一条空消息'
---

<h1 align="center">仓颉服务: 忆时塔 OOM 追凶记</h1>

<p align="center"><strong>一次横跨六个仓颉自研库的排查</strong></p>

<p align="center"><em>从一条空 message 的异常，到 662 个 CLOSE_WAIT —— 长连接泄漏如何伪装成存储 OOM</em></p>

<p align="center"><code>2026-08-19 → 2026-09-09</code> · <code>Cangjie</code> · <code>badger-cj</code> · <code>mcp-cj</code> · <code>json-rpc</code></p>

---

## 一条空消息

事情的开始，是一条几乎不包含任何信息的报错。

我在本地跑着一个常驻的 MCP 服务——一个**基于时序数据库、用于会话记录存储的记忆系统**（下面就叫它「线上这个服务」）。它会在后台定期执行维护任务。

某个下午开始，这个后台任务**每 60 秒失败一次**，而且失败信息只有一个：

```text
Exception:
```

`toString()` 出来就是 `Exception` —— 类型名是 `Exception`，message 为空。所有写入路径全军覆没，读取路径却完好无损。更诡异的是：**把线上数据复制一份到本地重跑，全部记录都正常。**

这排除了数据损坏，指向一个纯粹的**运行态**问题。

## 第一现场：写路径为什么会静悄悄地断

顺着空消息往上翻代码，答案的第一个碎片浮出水面：

```cangjie
// badger-cj WritePipeline.runBatch
try {
    // ... 批处理写
} catch (e: Error) {
    markFailed(e.message)   // ← Error 的 message 可能是空的
}
```

而 `commitOrThrow` 拿到失败的批次后：

```cangjie
throw Exception("")   // ← 空消息异常的来源
```

所以「空 message 的 Exception」= **OOM 的特征签名**。`OutOfMemoryError` 属于 `Error` 层级，它的 `message` 往往是空字符串，被 `markFailed` 原样透传，最后变成一条没有任何线索的 `Exception("")`。

> **教训 1**：排查框架报错时看到**空 message 的异常**，第一个要怀疑的不是业务逻辑，而是 **OOM**。这是一个可以写进排查手册的「特征签名」。

问题是：内存去哪了？

## 第二现场：256MB 的 GC 堆与 4MB 的 memtable

摸到运行时现场，两个数字非常刺眼：

- 容器 `VmRSS` 顶在 **250MB**，而 GC 堆上限是 **256MB** —— 几乎贴脸；
- 一个 `.mem` 文件停在 **4.6MB** 不再增长（超过 4MB 的 `memTableSize`），没有新的 `.sst` 落盘。

`badger-cj` 的写路径里，memtable 写满要 rotate：构造一张新表的 arena，默认 **8MB**。当堆已经被占满，这 8MB 的构造就是压死骆驼的最后一根稻草：

```text
memtable rotate → 新表 arena 分配 8MB → OOM
  → WritePipeline.runBatch catch(Error) → markFailed(空 message)
    → commitOrThrow → throw Exception("")
      → 后台维护任务每轮失败
```

这条链在 9 月 5 日爆发了两次。第一次是 **08:57 起写路径全断 3 小时以上**，本地用 16MB 的 `memTableSize` 复现出「第 18 条必 OOM」，同一款空消息异常。

修复分两步落地：

1. **`memTableSize` 默认 16MB → 4MB**（arena 32MB → 8MB）。根因不是「内存给小了」，而是 **同步 flush 的峰值与 memtable 规模不匹配**——当时拍板的思路是：*数据量这么小，不该去调大内存*。
2. **入口限长**。另一路排查发现，一个 **950KB 的病态 body** 在处理链上瞬时分配了约 **200MB**，直接把 256MB 的堆顶爆（GC 日志里 `GCReason: oom` 在 261MB 处是铁证）。于是在 HTTP 层加了 **Content-Length 预检**（>512KB 直接 413，零解析零读入），业务层再加 **payload 限长 256KB**。

限长上线后的端到端验证很直观：**50 个 950KB 病态请求连发，全部 413 秒回，零 OOM**；而修复前大约 15 条就会把服务卡死。

## 顺着依赖往上挖：badger-cj、json-rpc、mcp-cj

线上服务本体只是一个薄薄的 MCP 服务层，真正的故事发生在它脚下的**自研库依赖链**里。这一轮排查像剥洋葱，每剥一层都发现一个独立的缺陷。

### badger-cj：存储引擎的三笔旧账

**第一笔：运行期 flush 不落盘（数据丢失的元凶）。**

8 月 30 日晚上容器重建时，线上丢了数据。定位到的缺陷链相当经典：

- `flushToLevel` 在运行期**只建内存 L0 表**，不写 SSTable、不更新 MANIFEST；
- `imm`（不可变 memtable）**只增不减**，永远不出队；
- 落盘依赖 `close()`，而容器 `SIGKILL`/无优雅退出时 `close` 根本来不及跑，WAL 又在 flush 后被删除。

三重叠加的结果是：**进程一重启，内存里的东西就人间蒸发**。修复（`fix/flush-persist`）把 flush 做成真正的落盘原语（写 SSTable + 先记录 MANIFEST + imm 出队 + `decrRef`），并配套修掉三个连带缺陷：reopen 时表被重复加载两次、磁盘表 `findBlock` 对同 user key 组定位错位导致重启丢读（实测 45/160）、以及 `seedFileIDAfter` 与 memtable fid 冲突导致 WAL 误删。

同时补上了**优雅退出**：`registerShutdownHook(cb)` 让宿主清理逻辑在信号处理的后台线程里、在 `close()` 之前按序执行。这里有个反直觉的坑——仓颉 `std.runtime` 的信号 handler **必须返回 `true`**，返回 `false` 会触发默认终止，进程被 `SIGTERM` 直接杀掉，`close` 依旧来不及执行。

**第二笔：64KB 的价值上限其实是自己加的。**

线上服务写入 80KB 的大值时报错，我一度以为是 badger 的固有限制。对照 `badger-go` 才发现：**64KB 限制是仓颉版自己加的**（memtable 的 value 槽用了 `UInt16`），而 go 版实际只限制 `key ≤ 65000`（表与 vlog 格式），**value 并无 64KB 上限**。修复把 value 槽扩到 `UInt32`、`key > 65000` 写前拒绝，语义正式对齐 go。

**第三笔：掩码漏改与静默丢写。**

`UInt16 → UInt32` 的槽位扩容引入了两处回归，而且都很隐蔽：

- `memtable_iterator.cj` 漏改了 value 槽的 16 位掩码 —— **大于 64KB 的值迭代读回被截断**（实测 `80141 → 14605`），下游表现为数组越界；
- `WritePipeline.loop` **没有 Error 边界** —— OOM 会杀掉管道协程，写请求永久挂起（对调用方表现为「卡住」，不是「失败」）。

这两处修复后，badger-cj 又追加了一轮架构级投入：**flush 移出写锁异步化**（flusher 协程 + 队列背压，对齐 go 的 `flushChan`，吞吐 46→94K keys/s，`close` 从 720ms 降到 16ms）、`TableBuilder` 单拷贝、以及 **rotate 原子化 + 阶段化**。

阶段化这条值得单独说：并发压测下曾出现**整批数据丢失**（初版丢 300/1800、33/1305、28/200）。现场铁证是 `flushMemTable` 返回后 `immNow = 2` —— rotate 与入队分成两段，中间一旦被 OOM/Error 打断，表就滞留在 `imm` 永远不入队。修复把「rotate + 入队」收进同一写锁段，并把**可抛异常的操作前置到不可抛的状态序列之前**，消除中断窗口。

**旁支：一个编译器 bug。**

压测中还有一类偶发失败，最后追到了仓颉编译器上：`Array(n, { j => ... })` 这种**闭包构造数组**，在 `-O2` 下会出现**末元素取反**。我们归档了单文件最小复现（`class` + `static` 构造 + 切片陪衬的形状），提交到上游 issue #3454。

官方后来裁定为**误报**（切片共享存储 + 复现程序断言写反）。我们本地复测确认了官方结论，但**保留了规避代码**——把 `{ j => ... }` 构造换成「占位 + 循环赋值」，这是一次防御性加固，代价为零。顺带说，真凶另有其人：并发 `close` 丢数据是独立的真 bug，已在前面那轮的原子化修复里解决。

### json-rpc：被 OOM 杀死的接收循环

`mcp-cj` 建立在 `json-rpc` 之上，而接收循环是整条链路的入口。它踩了两个坑：

1. **单条消息异常关掉整个服务器**（8-26 修复）。一条畸形消息就能让服务下线，这是可用性上的大忌。
2. **接收循环没有 Error 边界**（9-2 修复）。`catch (e: Error)` 只能捕获 `Error` 子类；普通 `Exception` 会穿透，而 OOM 直接**杀掉接收协程**——表现就是「服务还活着，但再也收不到任何请求」。

修复后 `receiveLoop` 在边界捕获系统级 `Error`，只记录、不逃逸。这条经验后来被推广到所有「主循环」型代码。

### mcp-cj：SSE 长连接里的幽灵

`mcp-cj` 是 MCP 服务端框架。早在 8 月 26 日，它就因为「断连写异常杀死服务器 + SSE 不刷响应头」做过一轮健壮性加固（v2.3.5）。但那只是**症状层**的包扎。真正的根因要到 9 月 9 日才现形。

## 转折点：一句朴素的直觉

> 「我怎么感觉我每次进去界面后都出了问题（虽然可能不相关）。」

这是一句来自实际使用者的观察。事后看，**它是整场追凶的转折点**。

沿着这个直觉去问容器要数据，画面触目惊心：

```text
CLOSE_WAIT 状态连接：662
socket fd 数量：1009        （正常水位 < 100）
```

一个只有零星访问的服务，攒下了 **662 个半关闭连接**和 **1009 个 socket 文件描述符**。

`CLOSE_WAIT` 的含义非常明确：**对端已经关闭了连接，本端却还没有调用 `close()`**。也就是说——有人把连接忘在那了。

### SSE：`wait()` 永远等不到的那个通知

`mcp-cj` 的 `StreamableHttpServer.handleSSE` 长这样：

```cangjie
// 简化示意
this.sseWriter = Some(writer)
while (true) {
    this.sseCond.wait()     // ← 无限阻塞，没有超时
}
```

客户端建立 SSE 通道后，服务端在这里挂起等待推送。问题在于：**当客户端断开（关页面、断网、Agent 退出）时，没有任何人去唤醒它**。连接对应的 `HttpResponseWriter` 一直留在 `sseWriter` 里，TCP 连接停在 `CLOSE_WAIT`，fd 永远不释放。

每一次 MCP 会话的断开，都在这里留下一具「尸体」。所以那句直觉完全正确：**每次进界面、刷新、关页面，都会泄漏一条连接**。

修复方式是把「无限等待」换成「**带超时的心跳探测**」：

```cangjie
// v2.3.8
while (true) {
    if (this.sseCond.wait(timeout: this.heartbeatInterval)) {
        // 被正常唤醒（有新数据要推）
    } else {
        // 超时 = 心跳周期到了：写一行 SSE 注释探测对端
        try {
            writer.write(": ping\n\n".toArray())
        } catch (e: Exception) {
            // 写失败 = 对端已经走了 → 清理 writer 并退出循环
            this.sseWriter = None
            break
        }
    }
}
```

核心洞察是：**HTTP 不会主动告诉你对端消失了，但「写」会**。写失败就是断连信号；写成功则证明连接还活着。心跳间隔默认 30 秒，既完成了对端探测，又给连接回收设定了上界。

### cjxt：同一款病，换了个协议

那句直觉指向的是「界面」，而界面是 `cjxt`（服务端驱动 UI 框架）渲染的，它用 **WebSocket** 通信——SSE 的孪生兄弟。

一模一样的病：

```cangjie
// cjxt app.cj listenLoop（修复前）
while (true) {
    let frame = ws.read()      // ← 无限阻塞
    match (frame) {
        case Close => break    // ← break 之后没有 closeConn()
        ...
    }
}
```

- 只有收到 **Close 帧**才会 `break`，而 `break` 之后**根本没关连接**；
- 如果对端是**直接断开 TCP**（关页面、断网，很常见），`ws.read()` 抛出 `ConnectionException`，被上层的 `upgradeWS` 捕获后**只打了一行日志**，同样没有 `closeConn()`。

用 `/proc/self/fd` 计数做了对照实验（5 次连接 + 断开）：

| | 修复前 | 修复后 |
|---|---|---|
| fd 变化 | 10 → 15（单调累积） | 10 → 10（稳定） |
| CLOSE_WAIT | 0 → 5 | 0 |

修复是把整个 `listenLoop` 包进 `try/finally`，**所有退出路径**（Close 帧、异常逃逸、handler 异常）都兜底执行 `ws.closeConn()`。

### cron-cj：差点被漏掉的第三个循环

排查到这里顺手做了一次「**全仓库主循环体检**」，果然又抓到一个：`cron-cj` 的调度器 `runLoop`、任务执行、以及 `Recover/Delay/Skip` 三个链式装饰器，**全都没有 `catch (e: Error)`**。

后果很直接：一次 OOM 就能**杀死整个调度器**——而后台的维护任务正是挂在这个调度器上的。这解释了为什么「写路径断了」的同时，后台任务也一起没了动静。

修复是三层补齐 `catch (e: Error)`，只记录、不退出。回归测试用**无限递归**制造 `StackOverflowError`，断言计数器仍在增长——即调度器存活。

## 完整因果链

把四幕拼起来，整条因果链终于闭合：

```text
MCP 会话 / 界面访问频繁断开
   │
   ├─ mcp-cj handleSSE 无限 wait()     → CLOSE_WAIT + fd 泄漏
   └─ cjxt listenLoop 不 closeConn     → CLOSE_WAIT + fd 泄漏
                                          │
                                          ▼
                              连接与内存持续累积
                                          │
                                          ▼
                          GC 堆 256MB 被顶满（VmRSS 250MB）
                                          │
                                          ▼
                        memtable rotate 构造新表 arena 8MB → OOM
                                          │
                                          ▼
                 OOM 是 Error 层级 → runBatch markFailed(空 message)
                                          │
                                          ▼
                     commitOrThrow → throw Exception("")
                                          │
                                          ▼
                       写路径全断（读路径不分配大对象，故幸存）
```

**所以「存储 OOM」只是表象。真正的第一因，是长连接泄漏。** 存储层的一系列加固（memTableSize、限长、异步 flush、rotate 原子化）都是必要的纵深防御，但它们治的是并发症——如果不修连接泄漏，堆迟早还会被填满。

修复上线后的对照数据：

| 指标 | 修复前 | 修复后 |
|---|---|---|
| CLOSE_WAIT | 662 | **0** |
| socket fd | 1009 | **10** |
| 后台维护任务 | 每轮失败 | 正常，0 失败 |
| 模拟 10 次 SSE 断连 | fd 持续涨 | fd 20 → 11 → **10**（回落归零） |
| 模拟 5 次 WS 连接/断开 | fd 10 → 15 | fd **10**（纹丝不动） |

数据零丢失：旧的 `.mem` 正常 flush 成 SSTable，全部记录一条不少。

## 沉淀：七条可以复用的经验

多库联合排查的收获，大多不是「某个 bug 怎么修」，而是「**以后怎么更快地找到它**」：

**1. 空 message 异常 ≈ OOM。**
框架层的 `catch (e: Error) → markFailed(e.message)` 会把 `OutOfMemoryError` 的空 message 原样透传，最终变成没有任何线索的 `Exception("")`。看到它，先查内存，别查业务。

**2. `catch (e: Error)` 捕不到 `Exception`（反之亦然）。**
仓颉里 `Error` 与 `Exception` 是两条不同的继承链。服务边界要用 `catch (e: Error)` 兜住系统级错误（OOM、栈溢出），但**不能指望它接住普通异常**（`Int64.parse` 抛的是 `IllegalArgumentException`）。所有「主循环」——接收循环、调度循环、监听循环、连接循环——都必须有 `catch (e: Error)`，**只记录、不退出**。

**3. 长连接必须有心跳超时。**
任何「阻塞等待对端消息」的循环，都必须带超时。HTTP/WebSocket 不会主动通知你对端消失了，但**写操作会**——「写失败 = 断连」是最可靠的探测手段。

**4. 连接泄漏看 CLOSE_WAIT 和 fd 计数。**
`CLOSE_WAIT` 堆积 = 本端忘了 `close()`。`/proc/self/fd` 的条目数可以做进程内断言，非常适合写成回归测试。这两个指标应该进监控告警——本次排查的入口数据就是它们。

**5. 分层防御，而不是单点补丁。**
入口限长（Content-Length 预检 413 + payload 限长）、存储参数（memTableSize）、资源水位（GC 堆）、生命周期（优雅退出落盘）——每一层都只降低概率，但叠起来才能让「一个 bug」不至于击穿整个服务。

**6. 排查手段也要讲究。**
- `docker logs` 直接管道 `grep` 会因为 broken pipe 给出**假的 0 计数**，一定要**先落盘再 grep**；
- 生产事故第一反应不是改生产，而是**复制数据副本到本地复现**（本次正是靠它排除了数据损坏）；
- 修复必须做 **A/B 对照**：旧代码跑测试 FAILED、新代码 PASSED，这个断言本身就是回归测试。

**7. 上游库缺陷要有「作战流程」。**
最小复现 → 归档 → 报 issue → 本地对照验证。`badger-cj` 那轮连编译器 bug 都追到了最小复现文件（最后被官方裁定误报，但对照实验的过程本身就是资产）。

## 后记

这场排查从 8 月下半持续到 9 月 9 日，横跨**六个自研库**：

| 库 | 定位 | 关键修复 |
|---|---|---|
| [**badger-cj**](https://atomgit.com/ystyle/badger-cj) | 存储引擎 | flush 落盘、优雅退出、掩码/Error 边界、异步 flush、rotate 原子化、编译器 bug 规避 |
| [**tsdb-cj**](https://atomgit.com/ystyle/tsdb-cj) | 时序数据库 | key 编码 v2 + 迁移、游标/offset 分页、reverse seek 修复 |
| [**mcp-cj**](https://atomgit.com/ystyle/mcp-cj) | MCP 服务端框架 | SSE 刷头、断连不杀服务、**SSE 心跳回收（v2.3.8）** |
| [**json-rpc**](https://atomgit.com/ystyle/json-rpc) | RPC 层 | 单消息异常不关服、接收循环 Error 边界 |
| [**cjxt**](https://atomgit.com/ystyle/cjxt) | 服务端驱动 UI 框架 | **WS 连接回收**、@defineCSS 内联泄漏、@Page 多行字符串 |
| [**cron-cj**](https://atomgit.com/ystyle/cron-cj) | 调度器 | **三层 `catch (e: Error)` 存活性边界（v1.0.1）** |

最有意思的一点是：**最后那把钥匙，来自一句朴素的使用直觉**——「我怎么感觉我每次进去界面后都出了问题」。当时所有技术线索都指向存储层，是这句话把我们重新拉回到「界面 → 连接」这条线上。

排查最难的从来不是修 bug，而是**在一堆合理的怀疑里，找到那个真正的主因**。而这一次，主因藏在一句朴素的观察里。

