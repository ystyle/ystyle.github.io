---
title: "holt-cj：720 行的图数据库，能干什么、干不了什么"
subtitle: 顶点、边、Gremlin 风格遍历——以及一个还没实现的索引
date: 2026-10-22 10:00:00
lastmod: 2026-10-22 10:00:00
slug: holt-cj-graph-db
categories:
  - 软件
tags:
  - Cangjie
  - holt
  - 图数据库
  - 数据库
---

<p align="center"><strong>holt-cj 介绍</strong></p>

<p align="center"><em>一个小图库的边界清单</em></p>

> holt-cj 是基于 [badger-cj](/2026/10/10/badger-cj-porting-notes/) 的嵌入式图数据库。
> 它只有 720 行实现代码，所以本文不打算把它讲成一个大项目——
> 而是**把它的能力和边界一条条列清楚**，方便你判断能不能用。

## 一、它是什么

一句话：**嵌入式图数据库，顶点 + 边 + 属性 + 遍历。**

```cangjie
import holt.*
import jsonvalue.*

let g = Holt.openInMemory()
// let g = Holt.open("/data/graph")

// 建两个顶点（多标签 + JsonValue 属性）
let alice = g.createVertex(
    ArrayList<String>(["Person"]),
    HashMap<String, JsonValue>([
        ("name",
         JsonValue.String("Alice")),
        ("age", JsonValue.Number(30))
    ])
)
let bob = g.createVertex(
    ArrayList<String>(["Person"]), ...
)

// 建一条边
g.createEdge("knows", alice.id, bob.id,
    HashMap<String, JsonValue>([
        ("since", JsonValue.Number(2020))
    ]))
```

数据模型很直接：

- **顶点**：ULID 标识 + 多标签（`Array<String>`）+ 属性（`HashMap<String, JsonValue>`）
- **边**：ULID 标识 + 谓词（label）+ 起点 + 终点 + 属性
- **属性值**：`JsonValue`，可以是字符串/数字/布尔/数组/对象

## 二、核心 API

### 2.1 顶点与边

| 操作 | 方法 |
| --- | --- |
| 建/读写顶点 | `createVertex` `getVertex` `updateVertex` `deleteVertex(cascade)` |
| 建/读写边 | `createEdge` `getEdge` `updateEdge` `deleteEdge` |
| 按标签查 | `has(label)` |
| 邻接 | `getOutgoingEdges` `getIncomingEdges` `getNeighbors(dir)` |

`deleteVertex(id, cascade: true)` 会级联删掉关联的边——这个设计是必要的，否则会留下悬空的边。

### 2.2 遍历：Gremlin 风格

这是它最有意思的部分。遍历是**惰性构建**的：每一步只是往列表里追加动作，`toList()` 才真正执行。

```cangjie
let result = g.V()
    // 按标签过滤
    .has("Person")
    // 按属性过滤
    .has("age", JsonValue.Number(30))
    // 沿出边走到邻居
    .out(["knows"])
    .limit(10)
    .toList()
```

支持的步骤：

| 步骤 | 作用 |
| --- | --- |
| `V()` / `V(ids)` | 全量起点 / 指定起点 |
| `hasLabel(label)` | 按标签过滤 |
| `has(key, value)` | 按属性过滤 |
| `out(labels)` / `in(labels)` / `both(labels)` | 沿边走出去 |
| `limit(n)` | 截断 |
| `toList()` / `next()` | 求值 |

**注意：目前不需要先 `V()`**——`V(ids)` 和 `V()` 都能直接开始。

### 2.3 事务与运维

```cangjie
// 显式事务
g.transaction({ txn =>
    txn.createVertex(...)
    txn.createEdge(...)
})

// 备份/恢复（流式）
g.backup(writer)
g.restore(reader)

// 统计
let stats = g.getStats()
```

外加 `registerSignalShutdown()` / `registerShutdownHook()`——和 sunku 一样从 badger-cj 继承的优雅退出能力。

## 三、它是怎么存的

看懂存储布局，才能理解它的性能特征。key 前缀一共五种：

| 前缀 | 存什么 |
| --- | --- |
| `v:<vid>` | 顶点（标签 + 属性） |
| `e:<eid>` | 边（谓词 + outVid + inVid + 属性） |
| `eout:<vid>:<label>:<eid>` | 出边索引（按「顶点 + 谓词」） |
| `ein:<vid>:<label>:<eid>` | 入边索引 |
| `el:<label>:<eid>` | 边标签索引 |

**这五个前缀是实打实的**，所以这两种查询是真正的索引查找：

```cangjie
// 一次前缀扫描
g.getOutgoingEdges(vid)
// 更窄的前缀
g.getOutgoingEdges(vid, "knows")
// 走 el: 前缀
g.has("Person")
```

这也是为什么「按谓词找边」「找某顶点的邻居」在这个库上是快的。

## 四、边界：三件还没做好的事

这一节是本文的重点。**买之前先知道哪里会撞墙**。

### 4.1 属性索引是空的

这是最重要的一条。`createIndex()` 的方法体是这样的：

```cangjie
public func createIndex(kind: IndexType,
        label: String,
        keys: ArrayList<String>): Unit {
    // 边标签索引始终启用（el: 前缀）
    // 属性索引直接依赖 PropValue 类型，
    // 不需要额外操作
}
```

**方法体里只有两行注释，没有实际动作。** `getIndexes()` 则直接返回硬编码的空列表：

```cangjie
public func getIndexes():
        ArrayList<IndexMeta> {
    ArrayList<IndexMeta>()
}
```

所以 `createIndex()` 调了也不会报错，但**不会有任何索引被创建**。

### 4.2 属性过滤走内存

因为属性索引不存在，`.has(key, value)` 的实现是往过滤器列表里塞一个闭包：

```cangjie
public func has(key: String,
        value: JsonValue)
        : VertexTraversal {
    filters.add({ v: Vertex =>
        let got = v.props.get(key)
        if (got.isNone()) { false }
        else {
            jsonEq(got.getOrThrow(),
                value)
        }
    })
    this
}
```

它做的是：**把顶点读进内存，然后逐个判断属性**。

后果：

- `has(label)` 走 `el:` 索引，快
- `has(key, value)` **不走索引**，是逐顶点过滤
- 数据量大时，`.has("age", 30)` 的代价与「顶点总数 × 属性比较」成正比

### 4.3 `V()` 是全量扫描

没有 `V(ids)` 指定起点时，`execute()` 会扫 `v:` 前缀把**所有顶点 ID** 读出来，再逐个 `getVertex`：

```cangjie
// 全量扫描
let ids = holt.db.view({ txn =>
    // 扫 v: 前缀拿所有 ID
    let r = ArrayList<String>()
    let opt =
        IteratorOptions(
            prefix: strb("v:"))
    let iter = txn.newIterator(opt: opt)
    iter.rewind()
    while (iter.valid()) {
        ... r.add(...) ...
    }
    r
})
for (id in ids) {
    // ↓ N 次单点读
    let v = holt.getVertex(id)
    if (v.isSome()) {
        vertices.add(v.getOrThrow())
    }
}
```

**先扫一遍 key 拿全量 ID，再逐个读音**——顶点多了会很慢。所以实际使用时，**尽量从 `V(ids)` 或已有顶点出发**，而不是从 `V()` 开始。

## 五、和「一个完整图数据库」差多远

| 能力 | 一个完整图库（Neo4j / Dgraph） | holt-cj |
| --- | --- | --- |
| 顶点 + 边 + 属性 | ✅ | ✅ |
| 多标签 | ✅ | ✅ |
| 邻接查询（按谓词） | ✅ | ✅（`eout:`/`ein:` 索引） |
| Gremlin/Cypher 风格遍历 | ✅ | ⚠️ 基本步骤有，无 `where`/`aggregate`/`order` |
| **属性索引** | ✅ | ❌ **未实现** |
| 变长路径（`*1..3`） | ✅ | ❌ |
| 最短路径算法 | ✅ | ❌ |
| 图算法（PageRank 等） | ✅ | ❌ |
| 分布式 | ✅ | ❌（嵌入式单机） |
| 事务 | ✅ | ✅（复用 LSM 事务） |

**定位很清楚**：它是「**能用 Gremlin 风格写遍历的嵌入式小图库**」，不是「轻量版 Neo4j」。

## 六、什么场景合适

**✅ 合适**

- **数据量中等、关系简单的本地图**：几千到几万个顶点，查询主要靠「邻接」而不是「属性过滤」
- **嵌入式场景**：CLI 工具、单机应用、离线分析
- **不想为图关系写一堆关联表**：用 `eout:`/`ein:` 表达「谁指向谁」，比 SQL 中间表直观
- **测试替身**：写图算法测试时，不用起 Neo4j
- **关系数据的一次性分析**：加载、遍历、导出

**⚠️ 不合适**

- **按属性找顶点**（这是最大的限制——`has(key, value)` 是全量过滤）
- **需要路径算法**（最短路径、变长路径）
- **顶点数量到十万级以上**（`V()` 全量扫描会拖慢）
- **需要持久化图算法结果 / 图计算框架**
- **多进程共享图**

## 七、一个实际例子：依赖关系图

用「项目依赖」来演示它合适的样子——这类图的特点是**关系比属性重要**：

```cangjie
// 每个项目一个顶点
let libs = ["badger-cj", "storm-cj",
            "tsdb-cj", "sunku-cj"]
let vs = HashMap<String, Vertex>()
for (name in libs) {
    let v = g.createVertex(
        ArrayList<String>(["Library"]),
        HashMap<String, JsonValue>([
            ("name",
             JsonValue.String(name))
        ])
    )
    vs.add(name, v)
}

// 依赖边：storm 依赖 badger
g.createEdge("depends",
    vs["storm-cj"].id,
    vs["badger-cj"].id,
    HashMap<String, JsonValue>())

// 问：storm-cj 直接依赖谁？
// 走 eout: 索引，快
let direct = g.getOutgoingEdges(
    vs["storm-cj"].id, "depends")
for (e in direct) {
    let target = g.getVertex(e.inVid)
    println(target.getOrThrow().props)
}

// 问：谁依赖 badger-cj？
// 走 ein: 索引，快
let users = g.getIncomingEdges(
    vs["badger-cj"].id, "depends")

// 遍历：从 storm-cj 出发，
// 找它依赖的依赖
let deps = g.V([vs["storm-cj"].id])
    .out(["depends"])
    .out(["depends"])
    .toList()
```

这段代码里所有查询都走索引——因为它们都是**邻接查询**。这正是这个库擅长的。

反过来，如果你要问「哪些库的版本号是 1.6.20」，那就是属性过滤，会退化成全量扫描。

## 八、小结

- **720 行**（4 个源文件），实现小而完整
- **真的做了的**：顶点/边/多标签/JsonValue 属性、三种邻接索引（`eout:`/`ein:`/`el:`）、Gremlin 风格惰性遍历、事务、备份恢复、级联删除
- **还没做的**：**属性索引（`createIndex` 是空操作）**、变长路径、图算法、分布式
- **合适的场景**：邻接查询为主的嵌入式图、中等数据量、单进程

> 想对比一下上面提到的 LSM 底座，见[从 Go 移植 BadgerDB 到仓颉](/2026/10/10/badger-cj-porting-notes/)；
> 想看在它之上的另一个库，见 [sunku-cj](/2026/10/22/sunku-cj-embedded-redis/)。
