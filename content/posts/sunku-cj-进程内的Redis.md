---
title: "sunku-cj：当 Redis 的 API 装进进程内"
subtitle: 120 个方法同名同义，但架构位置完全不同——能替代什么、不能替代什么
date: 2026-10-22 10:00:00
lastmod: 2026-10-22 10:00:00
slug: sunku-cj-embedded-redis
categories:
  - 软件
tags:
  - Cangjie
  - sunku
  - Redis
  - 缓存
  - 数据库
---

<p align="center"><strong>sunku-cj 介绍</strong></p>

<p align="center"><em>API 可以一模一样，架构位置不能</em></p>

> sunku-cj 是仓颉生态里的「Redis 兼容本地 KV 数据库」，架在 [badger-cj](/2026/10/10/badger-cj-porting-notes/) 之上。
> 本文不吹它「兼容 Redis」，而是把「同构到什么程度、在哪一层不能同构」讲清楚。

## 一、它是什么

一句话：**用 Redis 的命令写进程内 KV**。

```cangjie
import sunku.*

// 纯内存
let cache = Sunku.memory()
// 持久化到磁盘
// let cache = Sunku.open("/data/db")

cache.set("user:1", "张三")
cache.setex("session:abc", "token",
    Duration.hour)
cache.incr("counter", by: 1)

cache.zadd("rank", 100.0, "alice")
cache.lpush("queue", "task-1")
cache.sadd("tags", "cangjie")
```

方法名就是 Redis 命令名。五种数据结构都覆盖，合计约 120 个公开方法：

| 结构 | 方法数 | 覆盖的命令（部分） |
| --- | --- | --- |
| String | 29 | `set` `setex` `psetex` `get` `del` `incr` `incrby` `incrbyfloat` `append` `strlen` `getrange` `setrange` `getbit` `setbit` `bitcount` |
| Hash | 17 | `hset` `hget` `hgetall` `hdel` `hexists` `hincrby` `hkeys` `hvals` `hlen` `hmset` `hmget` `hsetnx` |
| List | 23 | `lpush` `rpush` `lpop` `rpop` `lrange` `lindex` `lset` `ltrim` `lrem` `linsert` `blpop` `brpop` `brpoplpush` `lpos` |
| Set | 23 | `sadd` `srem` `smembers` `sismember` `scard` `sinter` `sunion` `sdiff` `smove` `spop` `srandmember` `sscan` |
| ZSet | 28 | `zadd` `zrem` `zscore` `zrank` `zrange` `zrangebyscore` `zincrby` `zcount` `zremrangeby*` `zunionstore` `zinterstore` `zpopmin` `bzpopmin` |
| Key | 13 | `exists` `expire` `expireat` `pexpire` `ttl` `persist` `key` |

**这不是「像 Redis」，是「照着 Redis 的签名抄的」**——连 `setex` / `psetex`（秒和毫秒的区别）、`incrbyfloat`、`zrangebyscore` 这些细节都对上了。

## 二、为什么会有这个东西

在仓颉里用 Redis，通常要起一个服务、走网络、序列化。如果你的程序本身就是**单进程**的，这套开销是白付的：

```
用 Redis：
  你的程序 ──TCP──> Redis 进程 ──> 内存
              ↑
        序列化、上下文切换、
        连接池管理

用 sunku：
  你的程序 ──函数调用──> 本地 LSM / 内存
```

差别不只是「快一点」：

| | Redis | sunku |
| --- | --- | --- |
| 部署 | 起一个服务（Docker / systemd） | 一个依赖，零额外进程 |
| 运维 | 要监控、要备份、要考虑认证 | 库怎么部署它就怎么部署 |
| 故障面 | 网络断了就没了 | 没有网络这一层 |
| 数据边界 | 多个客户端共享 | **只有本进程能访问** |

所以它的合适位置是：**你的程序自己就是那个「唯一使用者」的时候**。

## 三、能做什么（核对过源码）

### 3.1 五种数据结构，覆盖完整

我逐个文件核对过实现行数，没有「声明了但没实现」的占位：

| 结构 | 实现 | 测试 |
| --- | --- | --- |
| String | 513 行 | 323 行 |
| ZSet | 686 行 | 481 行 |
| Set | 363 行 | 275 行 |
| List | 494 行 | 387 行 |
| Hash | 233 行 | 171 行 |

**测试 2159 行 vs 实现 2853 行**——测试比想象中厚，这对一个存储库是好事。

### 3.2 两种存储模式

```cangjie
// 纯内存，进程退出即丢
Sunku.memory()
// 指定 memtable 大小
Sunku.memory(memTableSize: ...)
// 持久化（LSM 落盘）
Sunku.open("/data/db")
```

持久化模式直接复用 badger-cj，所以继承了它的能力：WAL、SSTable、compaction、优雅退出落盘。

```cangjie
// SIGTERM → flush 落盘 → 退出
cache.registerSignalShutdown()
```

对一个要跑在容器里的程序，这条很实用：`docker stop` 时数据不会丢。

### 3.3 TTL

```cangjie
cache.setex("k", "v", Duration.hour)
cache.pexpire("k", 5000)   // 毫秒
cache.ttl("k")             // 剩余时间
cache.persist("k")         // 去掉过期
```

实现方式是**写时把 `expiresAt` 存进 LSM**（`Entry.withExpiresAt`），读到过期就视作不存在。

## 四、不能做什么（这几条比上面更重要）

### 4.1 它不是「Redis 的替代品」，是「Redis 的一个位置」

这是最容易误解的一点。**sunku 是进程内库，不是网络服务。**

```
Redis 在架构里的位置：

  ┌────────┐ ┌────────┐ ┌────────┐
  │ 进程 A │ │ 进程 B │ │ 进程 C │
  └───┬────┘ └───┬────┘ └───┬────┘
      └──────────┼──────────┘
                 ▼
            ┌─────────┐
            │  Redis  │
            └─────────┘
        唯一真相，所有进程共享


sunku 在架构里的位置：

  ┌─────────────────┐ ┌─────────────────┐
  │ 进程 A          │ │ 进程 B          │
  │ ┌─────────────┐ │ │ ┌─────────────┐ │
  │ │   sunku     │ │ │ │   sunku     │ │
  │ └─────────────┘ │ │ └─────────────┘ │
  └─────────────────┘ └─────────────────┘

     各自一份，互不可见
```

所以「Redis 当主缓存、sunku 当二级缓存」这个想法**方向是反的**。

真正的两级缓存通常长这样：

| 层 | 位置 | 延迟量级 | 用什么 |
| --- | --- | --- | --- |
| L1 | 进程内 | 纳秒 | **sunku 在这个位置** |
| L2 | 进程间共享 | 毫秒 | Redis |
| L3 | 持久化 | 毫秒~秒 | 数据库 |

**sunku 天生就是 L1 的材料**：零网络、零序列化（对仓颉对象）、单进程独占。

### 4.2 `blpop` 是轮询，不是条件变量唤醒

Redis 的 `BLPOP` 是阻塞的：没有元素就挂在条件变量上，`LPUSH` 一到立刻唤醒。

sunku 的实现在做这个：

```cangjie
public func blpop(keys: Array<String>,
        timeout: Duration)
        : ?(String, String) {
    let deadline =
        DateTime.now() + timeout
    let checkInterval =
        Duration.millisecond * 100

    while (DateTime.now() < deadline) {
        for (key in keys) {
            match (lpop(key)) {
                case Some(v) =>
                    return Some((key, v))
                case None => continue
            }
        }
        // ← 每 100ms 轮询一次
        sleep(checkInterval)
    }
    ...
}
```

**语义对上，延迟多最多 100ms。** 做任务队列时这个差别是能感觉到的；做普通缓存则无所谓。

### 4.3 TTL 只有惰性过期

Redis 有两套机制：**惰性删除**（读到才判）+ **定期删除**（后台扫一批）。sunku 只有前者。

后果：**已过期的 key 会一直占着磁盘，直到有人读到它。**

对一个长期运行的缓存进程，这意味两件事：

- 内存/磁盘曲线只涨不落，除非访问模式恰好覆盖到那些 key
- 想主动清理，只能自己扫 `key` 列表逐个 `ttl` 判断

### 4.4 并发：这里的语义和 Redis 不一样

这条我核对源码后确认，值得单独说。

Redis 是**单线程执行命令**的，所以 `INCR` 天然原子。sunku 跑在你的多线程程序里，而它的事务使用方式是：

```cangjie
// src/sunku_string.cj 的 incr（节选）
let txn = db.newTransaction(update: true)
// ↓ 事务外读
let currentValue =
    match (db.get(keyBytes)) {
    case Some(vs) => ...
}
let newValue = currentValue + by
txn.setEntry(entry)
txn.commit()
```

**读用的是 `db.get`（事务外），写用的是 `txn.setEntry`（事务内）。**

底层 badger-cj 有 SSI 冲突检测，但它依赖事务**记录读集**（`txn.get` 时把 key 记进 `reads`）。事务外读不入账，冲突检测就看不见这次竞争。

实测统计：整个库 **65 处 `db.get`，0 处 `txn.get`**。

所以：

| 场景 | 是否安全 |
| --- | --- |
| 单线程 | ✅ 没问题 |
| 多线程各自操作**不同 key** | ✅ 没问题（写入本身是事务的） |
| 多线程对**同一个 key** 做 `incr`/`zadd` 这类「读-改-写」 | ⚠️ **可能丢更新** |
| 多线程各自 `set` 同一个 key | ✅ 后写覆盖，语义明确 |

**如果你要并发用，避开「多线程对同一 key 做读-改-写」这个模式**，或者在应用层自己加锁。

### 4.5 其他「Redis 有、它没有」的

| Redis 有 | sunku |
| --- | --- |
| 网络协议（RESP）、多客户端 | 无 |
| pub/sub | 无 |
| 事务 `MULTI/EXEC`、Lua 脚本 | 无（但底层是 LSM 事务） |
| RDB / AOF 持久化 | 直接架在 LSM 上，没有独立的持久化格式 |
| 主从复制、哨兵、集群 | 无 |
| `SCAN` 游标（完整实现） | 只有 `zscan` / `sscan` 等局部扫描 |

## 五、什么场景该用它

按上面的边界，能用的场景其实很清楚：

**✅ 合适**

- **单进程程序的本地缓存**：要 TTL、要五种结构、不想起 Redis
- **CLI 工具 / 脚本的状态存储**：跑完就走，不需要服务
- **测试替身**：写测试时用 `Sunku.memory()` 替代 Redis，不用起容器
- **离线数据处理的临时工作区**：五种结构在手，比裸 KV 好用
- **单机的边缘/嵌入式程序**：本来就没有「多进程共享」的需求

**⚠️ 不合适**

- **多进程共享状态**——这是最核心的一条
- **需要和别的语言/服务共享缓存**（Redis 的价值就在协议标准化）
- **多线程高频更新同一个计数器**（见 4.4）
- **需要 pub/sub 或 Lua 做原子复合操作**
- **需要主从/集群做高可用**

## 六、怎么用：一个实际例子

假设你在写一个本地 CLI，要缓存远程 API 的响应，避免重复请求：

```cangjie
import sunku.*

class ApiCache {
    let store: Sunku

    init(dir: String) {
        store = Sunku.open(dir)
        // 退出时落盘
        store.registerSignalShutdown()
    }

    func getOrFetch(url: String,
            fetch: () -> String): String {
        // 先查缓存（1 小时有效）
        match (store.get(url)) {
            case Some(v) => return v
            case None => ()
        }
        // 未命中就请求并写入
        let body = fetch()
        store.setex(url, body,
            Duration.hour)
        body
    }

    // 记每个域名的调用次数（ZSet 排名）
    func recordHost(host: String): Unit {
        store.zincrby("hosts", 1.0, host)
    }

    // 看调用最多的域名
    func topHosts(n: Int64):
            ArrayList<(String, Float64)> {
        store.zrevrange("hosts", 0, n - 1,
            withScores: true)
    }
}
```

这段代码在 Redis 下几乎一模一样——除了 `Sunku.open()` 换成了连接池，这正说明**API 同构是有价值**的：迁移成本主要在初始化和生命周期，不在业务逻辑。

## 七、小结

- **API 同构是真的**：120 个方法，命令名、参数顺序、语义都对着 Redis 抄
- **架构位置不能同构**：它是进程内库，只能当 **L1**，不能当 Redis 那种进程间共享的 **L2**
- 三条已知边界：`blpop` 轮询（+100ms）、TTL 只有惰性过期、并发读-改-写需要自己注意
- 合适的场景：单进程、单机、测试替身、CLI 工具——**只要你不需要「多进程共享」，它就是 Redis 的轻量替代**

> 下一篇：另一个仓颉数据库 [holt-cj](/2026/10/22/holt-cj-graph-db/)——图数据库，
> 关注的是「顶点和边怎么存、怎么遍历」。
