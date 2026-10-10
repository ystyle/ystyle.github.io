---
title: "把 BadgerDB 移植到仓颉（一）：没有裸指针怎么做无锁跳表"
subtitle: 仓颉没有 unsafe.Pointer，于是我把节点指针换成了数组下标
date: 2026-10-10 10:00:00
lastmod: 2026-10-10 10:00:00
slug: badger-cj-porting-notes
categories:
  - 软件
tags:
  - Cangjie
  - badger-cj
  - 数据库
  - LSM-Tree
  - 移植
---

<p align="center"><strong>从 Go 移植 BadgerDB 到仓颉（一）</strong></p>

<p align="center"><em>仓颉没有裸指针，于是我把节点指针换成了数组下标</em></p>

<p align="center"><code>Cangjie</code> · <code>LSM-Tree</code> · <code>badger-cj</code> · <code>移植</code></p>

> 这是系列第一篇，讲**怎么把它写出来**：语言差异怎么绕、以及怎么用。
> 后续三篇分别讲优化与误判、基准复核、以及怎样测才算数。

---

## 一、为什么要自己写一个 {#一为什么要自己写一个}

仓颉生态里，能直接嵌进进程、持久化、又足够快的 KV 存储，基本是空白。

选型时摆在面前的路有三条：包装一个 C/C++ 引擎、用 Go 写个 sidecar 通过 RPC 通信、或者干脆用纯仓颉重写一个。前两条都绕不开 FFI 或跨进程成本——而这恰恰是嵌入式数据库最不该有的负担。

所以 `badger-cj` 选择了第三条：**移植 Go 的 [BadgerDB v4](https://github.com/dgraph-io/badger)**。它是 LSM-Tree 架构，模块边界清晰，且已经被大量生产验证过。

> 移植不等同于翻译。Go 与仓颉在内存模型、并发原语、乃至类型系统上都有关键差异，下面会看到，最大的那块骨头出现在最核心的地方。

### 先说清楚：它兼容什么、不兼容什么

这一点我写在 README 最前面，因为含糊的兼容性声明比没有声明更危险：

| | 状态 |
| --- | --- |
| **API 语义** | ✅ 兼容 —— 接口设计遵循 Go 版本 |
| **数据格式** | ⚠️ 理论上兼容（按 Go 的 SSTable/VLog/MANIFEST 格式实现），但未经跨语言测试验证 |
| **直接迁移** | ❌ 不支持 —— **不能**直接读取 Go BadgerDB 的数据目录 |

原因在于元数据的编码方式是手动实现的（Protobuf / FlatBuffers），没有经过充分的跨语言对拍。**如果你打算用它，请从零开始建库，不要指望接管一个已有的 Badger 数据目录。**

---


---

## 二、第一块硬骨头：没有 `unsafe.Pointer`，怎么做无锁跳表 {#二第一块硬骨头没有unsafe.Pointer怎么做无锁跳表}

LSM-Tree 的写入路径最前端是 MemTable，而 MemTable 的心脏是一张**并发跳表**。Go 版 Badger 在这里用了大量裸指针 + CAS：

```go
// 节点间用裸指针相连，CAS 直接换指针
atomic.CompareAndSwapPointer(
    &node.next[i], oldPtr, newPtr)
```

问题来了：**仓颉没有 `unsafe.Pointer`**，也没有可以直接做原子比较交换的裸指针。这条路直接堵死。

### 解法：把指针换成「偏移量」

思路是**放弃指针，改用数组下标**——把所有节点的存储集中管理，节点之间不再互相持有引用，而是记录对方在存储块中的偏移：

```cangjie
// src/skiplist/atomic_storage.cj
class Segment {
    public let values: Array<AtomicUInt64>
    public let towers: Array<AtomicUInt32>

    public init() {
        var vs = Array<AtomicUInt64>(SEGMENT_SIZE,
            repeat: AtomicUInt64(0))
        var i: Int64 = 0
        while (i < SEGMENT_SIZE) {
            // 逐个覆盖为独立对象
            vs[i] = AtomicUInt64(0)
            i++
        }
        this.values = vs
        // ... towers 同理
    }
}
```

于是 CAS 就变成了对偏移量的比较交换：

```cangjie
// src/skiplist/atomic_storage.cj:117
public func casNextOffset(
    nodeIdx: Int64, level: Int64,
    old: UInt32, new: UInt32
): Bool {
    towers[nodeIdx][level]
        .compareAndSwap(old, new)
}
```

插入时用标准的 CAS 循环重试——换失败就重新查找插入位置，再来一次：

```cangjie
while (true) {
    let ok = prevNode.casNextOffset(
        i, nextOffsets[i], nodeOffset)
    if (ok) {
        break                    // 成功
    }
    // 失败：重新定位插入点
    let (p, n) = findSpliceForLevel(
        key, prevOff, i)
    prevOffsets[i] = p
    nextOffsets[i] = n
}
```

存储按**分段**扩展，避免一开始就预分配整块大数组。

### 一个坑：`repeat` 会让所有元素共享同一个原子对象

上面代码里那句「逐个覆盖为独立对象」不是啰嗦，是**必须**的。仓颉的 `Array(n, repeat: obj)` 对**引用类型**是值拷贝——如果 `AtomicUInt64` 是引用类型，`repeat` 出来的所有元素会**指向同一个对象**：

```cangjie
// ❌ 错：10 个元素共享同一个原子对象
//    并发下必然出错
let arr = Array<AtomicUInt64>(
    10, repeat: AtomicUInt64(0))

// ✅ 对：每个元素独立
var arr = Array<AtomicUInt64>(
    10, repeat: AtomicUInt64(0))
for (i in 0..10) {
    arr[i] = AtomicUInt64(0)
}
```

这类 bug 很阴险——单线程测试全绿，一上并发就数据错乱。

### 代价要认：读性能退化换来了正确性

无锁化不是没有成本的：

| 指标 | 改造前（伪 CAS） | 改造后（真 CAS） |
| --- | --- | --- |
| 并发安全 | ❌ 有数据损坏风险 | ✅ 无锁并发安全 |
| 写性能 | 数字好看（假象） | 变慢——真 CAS 要付内存序代价 |
| **读性能** | 数字好看（假象） | **明显变慢，约 3 倍** |

改造前那条路径"快"，是因为它**根本没在做真正的同步**。换用真正的原子操作后，每次读都要付出内存序的代价。

> 这组数字属于"改造前 vs 改造后"的对照，而旧实现早已不在代码里、无法重跑，
> 所以这里只保留量级关系（读变慢约 3 倍），不给纳秒值。

那为什么还要换？因为**数据安全是 0 或 1 的问题**，不是快慢问题。一个会损坏数据的存储引擎，性能再好也没有意义。

---


---

## 三、怎么用 {#三怎么用}

### 引入

```toml
[dependencies]
  "badgercj" = "1.6.21"
```

### 最小示例

```cangjie
import badgercj.db.*

main() {
    let opt = Config(dir: "/tmp/mydb")
    let db = Badger.open(opt)

    db.update({ txn =>
        txn.set("name".toArray(),
                "badger-cj".toArray())
    })

    let got = db.get("name".toArray())
    if (let Some(vs) <- got) {
        let s = String.fromUtf8(vs.value)
        println("value: ${s}")
    }

    db.close()
}
```

### 几个常用能力

```cangjie
// 链式配置
let opt = Config()
    .withDir("/tmp/mydb")
    // 注意：过大会加剧 flush 峰值
    .withMemTableSize(64 * 1024 * 1024u64)
    .withDisableWAL(false)

// 纯内存模式（测试、临时缓存）
let cfg = Config(inMemory: true)
let mem = Badger.open(cfg)

// TTL 过期
let key = "session".toArray()
let val = "data".toArray()
let entry = Entry.new(key, val)
    .withTTL(Duration.hour * 24)
db.batchSet(ArrayList<Entry>([entry]))

// 服务器场景：没有合适的地方调 close()
let opt2 = Config(dir: "./data")
    .withAutoCloseOnExit(true)
```

已实现的能力包括：事务（含 **SSI 可串行化快照隔离 + 冲突检测**）、前向/反向迭代器与前缀过滤、快照、MVCC、WAL 崩溃恢复、SSTable 前缀压缩 + Block 级 CRC、Value Log 分离存储与 GC、MANIFEST、完整 L0→L6 Compaction、BloomFilter（默认 1% 误判率）、Snappy 压缩、Stream API、全量/增量 Backup/Restore。

> **一个实用提示**：批量写的事务粒度对性能影响很大。同一写路径下，把单键事务改成
> 8 个 key 一个事务，每 key 成本降到约 1/3；64 个 key 一个事务可降到约 1/4。
> 原因是写路径的同步成本**没法靠框架内部批量提交摊薄**（唤醒次数 = 请求数，
> 每个 commit 必须被单独唤醒），真正的杠杆在用户侧的事务粒度。

---


---

## 四、它撑起了什么 {#四它撑起了什么}

`badger-cj` 不是一个孤立的库——它是这一系列底层存储的**地基**：

| 项目 | 定位 |
| --- | --- |
| [**badger-cj**](https://atomgit.com/ystyle/badger-cj) | LSM-Tree 可嵌入 KV 引擎（本文） |
| [**storm-cj**](https://atomgit.com/ystyle/badger-storm) | 嵌入式 JSON 文档数据库，纯仓颉零 FFI |
| [**sunku-cj**](https://atomgit.com/ystyle/sunku-cj) | Redis 兼容的本地 KV 数据库 |
| [**tsdb-cj**](https://atomgit.com/ystyle/tsdb-cj) | 嵌入式时序数据库 |
| [**holt-cj**](https://atomgit.com/ystyle/holt-cj) | 嵌入式图数据库 |

它们各自在同一套存储原语之上叠加不同的数据模型。后续文章会逐个展开。

---

---

## 结语 {#结语}

回头看这次移植，最花时间的不是"把 Go 代码翻译成仓颉"，而是**绕开语言差异**：没有 `unsafe.Pointer`，就用偏移量 + 原子数组重建无锁跳表。

一个存储引擎的价值，最终不在于它快了多少纳秒，而在于**你敢不敢把数据交给它**。这也是为什么在"读变慢 3 倍"和"数据不会损坏"之间，答案从来没有悬念。

> **下一篇**讲性能：十次优化把写吞吐翻倍，以及一次「我以为是编译器 bug」的乌龙。

---

## 相关链接 {#相关链接}

- 项目地址：[atomgit.com/ystyle/badger-cj](https://atomgit.com/ystyle/badger-cj)
- 中心仓包：[pkg.cangjie-lang.cn/packages/badgercj](https://pkg.cangjie-lang.cn/packages/badgercj)
- 参考实现：[Go BadgerDB v4](https://github.com/dgraph-io/badger)
- 本系列：
  - 第一篇：[没有裸指针怎么做无锁跳表](https://ystyle.top/2026/10/10/badger-cj-porting-notes/)
  - 第二篇：[十次优化与一次误判](https://ystyle.top/2026/10/11/badger-cj-perf-and-false-alarm/)
  - 第三篇：[重跑基准，三个结论翻了](https://ystyle.top/2026/10/12/badger-cj-benchmark-audit/)
  - 第四篇：[怎样测才算数](https://ystyle.top/2026/10/13/badger-cj-benchmark-method/)
