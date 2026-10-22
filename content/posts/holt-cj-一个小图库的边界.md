---
title: "holt-cj 1.1.0：从 720 行长到 3300 行的图数据库"
subtitle: 属性索引、变长遍历、六种图算法——以及四条仍然存在的限制
date: 2026-10-22 10:00:00
lastmod: 2026-10-22 15:30:00
slug: holt-cj-graph-db
categories:
  - 软件
tags:
  - Cangjie
  - holt
  - 图数据库
  - 数据库
---

<p align="center"><strong>holt-cj 1.1.0 介绍</strong></p>

<p align="center"><em>能力补齐了，限制也写清楚了</em></p>

> holt-cj 是基于 [badger-cj](/2026/10/10/badger-cj-porting-notes/) 的嵌入式图数据库。
> 这个库在 1.1.0 里做了一次大改：**实现从 720 行长到 3273 行**，
> 补上了属性索引、变长遍历和图算法。本文按新版重写。

## 一、它是什么

一句话：**嵌入式图数据库，顶点 + 边 + 属性索引 + Gremlin 风格遍历 + 图算法。**

```cangjie
import holt.*
import jsonvalue.*

let g = Holt.openInMemory()
// let g = Holt.open("/data/graph")

// 建顶点（多标签 + JsonValue 属性）
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

// 建边
g.createEdge("knows", alice.id, bob.id,
    HashMap<String, JsonValue>([
        ("since", JsonValue.Number(2020))
    ]))
```

数据模型：**顶点** = ULID + 多标签 + `HashMap<String, JsonValue>`；
**边** = ULID + 谓词 + 起终点 + 属性。

## 二、1.1.0 加了什么

这是本文的重点——因为**上一版的能力缺口基本都补上了**。

| 能力 | 1.0.x | **1.1.0** |
| --- | --- | --- |
| 顶点/边/多标签/属性 | ✅ | ✅ |
| 邻接查询（`eout:`/`ein:`） | ✅ | ✅ |
| **顶点标签索引（`vl:`）** | ❌ | ✅ |
| **属性索引（精确/范围）** | ❌ 空操作 | ✅ **可注册/回填/重建** |
| Gremlin 风格遍历 | 6 个步骤 | **25 个方法** |
| **变长路径** | ❌ | ✅ `repeatOut/In/Both` |
| **最短路径** | ❌ | ✅ BFS + Dijkstra |
| **图算法** | ❌ | ✅ PageRank/连通分量/拓扑/环 |
| 事务 | ✅ | ✅ 索引同事务维护 |

### 2.1 属性索引：真的能用了

上一版的 `createIndex()` 方法体只有两行注释——**调了不报错，但什么也不做**。
现在是完整实现（`property_index.cj`，537 行）：

```cangjie
// 注册索引（会回填存量顶点）
g.createIndex(IndexType.Exact, "Person",
    ArrayList<String>(["age"]))

// 查已注册的索引
let idx = g.getIndexes()

// 删掉
g.dropIndex("Person@age")
```

支持的形态：

| 类型 | 说明 |
| --- | --- |
| **精确索引**（`Exact`） | `has(key, value)` 走索引 |
| **范围索引**（`Range`） | `hasBetween(key, lo, hi)` 走索引 |
| **复合索引** | 多字段，最左连续字段等值 + 下一字段范围 |

几个实现细节值得说：

- **作用域按 label**：`Person@age` 和 `Employee@age` 是两个索引
- **只索引标量**：String / Number / Bool，不索引数组和对象
- **回填分批**：存量顶点每 500 个一批，避免长事务撑大内存
- **同事务维护**：写顶点时在同一事务里更新索引项，旧值用于删过期项
- **可重建**：`rebuildIndexes()` 全量重写且幂等；打开 1.0.x 旧库自动触发

索引 key 的布局：

```
索引项：vi:<索引名>:<字段值段...><vid 段>
元数据：_idx:<索引名> → JSON
```

**值段经过编码，保证字节序 = 语义序**——所以范围扫描可直接按字节序 seek，
不用解码比较。

### 2.2 遍历：从 6 个方法到 25 个

```cangjie
let result = g.V()
    .hasLabel("Person")
    .has("age", JsonValue.Number(30))
    .out(["knows"])
    .dedup()
    .order()
    .limit(10)
    .toList()
```

完整步骤清单：

| 类别 | 步骤 |
| --- | --- |
| 起点 | `V()` `V(ids)` |
| 过滤 | `has` `hasLabel` `hasNot` `hasBetween` `where` |
| 导航 | `out` `in` `both` `outE` `inE` `bothE` `outV` `inV` |
| 变长 | `repeatOut` `repeatIn` `repeatBoth` |
| 变换 | `values` `path` |
| 聚合 | `count` `dedup` `order` `limit` `range` |
| 求值 | `toList()` `next()` |

两个值得一提的设计：

**拉取式游标 + 单事务流式执行。** 遍历不是「每步物化一个列表」，而是按需拉取；
整个遍历在一个事务里完成，保证看到一致快照。

**起点规划。** 从 `V()` 开始时，引擎按成本选起点：

```
V(ids) 直接给
  → 用给定的
有属性索引命中
  → 走 vi: 索引
纯 hasLabel
  → 走 vl: 标签索引
都没有
  → 全量扫 v:
```

这解决了上一版「`V()` 永远是全量扫描」的问题。

### 2.3 图算法：包级函数

不用自己写 BFS 了：

```cangjie
// 最短路径：无权图用 BFS
let path = shortestPath(g, fromVid, toVid)

// 带权：按边属性权重做 Dijkstra
let weighted = shortestPathWeighted(
    g, fromVid, toVid, "weight")

// 其他
let ranks   = pageRank(g)
let comps   = weaklyConnectedComponents(g)
let sorted  = topologicalSort(g)
let hasLoop = hasCycle(g)
```

外加 `hasPath` / `successors` / `predecessors` / `from` / `vertices` 这些基础工具。

对「嵌入式小图库」来说这套能力已经够用——**依赖分析、路径查找、环路检测**
这些常见需求都有直接支持。

### 2.4 事务与索引一致性

1.1.0 修了一处事务问题：**索引维护现在和顶点写入在同一事务内**。这意味着：

- 写顶点失败 → 索引项也不会留下
- 不会出现「索引里有、数据里没有」的孤儿项

## 三、它是怎么存的

看懂 key 布局，才能判断什么样的查询快。

| 前缀 | 存什么 |
| --- | --- |
| `v:<vid>` | 顶点 |
| `e:<eid>` | 边 |
| `eout:<vid>:<label>:<eid>` | 出边索引 |
| `ein:<vid>:<label>:<eid>` | 入边索引 |
| `el:<label>:<eid>` | 边标签索引 |
| `vl:<label>:<vid>` | **顶点标签索引**（1.1.0） |
| `vi:<索引名>:...` | **属性索引项**（1.1.0） |
| `_idx:<索引名>` | 属性索引元数据 |

所以这些查询**都走索引**：

```cangjie
// 邻接：eout: 前缀
g.getOutgoingEdges(vid)
g.getOutgoingEdges(vid, "knows")

// 标签：vl: 索引
g.V().hasLabel("Person")

// 属性（需先注册索引）：vi: 索引
g.V().has("age", JsonValue.Number(30))
```

**最后一条是 1.1.0 和 1.0.x 最大的区别**——上一版这里会退化成全量内存过滤。

## 四、仍然存在的四条限制

能力补齐了，但边界依然清楚。这几条来自 README 的「已知限制」。

### 4.1 内存模式只适合测试/小数据

```cangjie
Holt.openInMemory()   // 测试用
Holt.open("/data/db") // 生产用
```

原因不在 holt 自己，而在底层 badgercj：1.6.7~1.6.21 的 in-memory 模式在
memtable 高频轮转时**偶发丢写**（写管道对同一请求重复 done，导致 commit
提前唤醒）。

1.1.0 起依赖 badgercj **1.6.22** 已修复，但**批量导入仍建议用 `open(path)`**。

### 4.2 属性索引的三条边界

| 边界 | 说明 |
| --- | --- |
| **按 label 作用域** | `Person@age` 与 `Employee@age` 是两个索引 |
| **只索引标量** | String/Number/Bool；数组和对象不索引 |
| **复合索引受限** | 最左连续字段等值 + 下一字段范围 |

第三条展开一点。多字段索引 `Person@age,name` 支持：

- `age == 30` ✅ 最左字段等值
- `age == 30 && name == "Alice"` ✅
- `age > 20 && name == "Alice"` ✅ 等值 + 下一字段范围
- `name == "Alice"` ❌ 跳过最左字段，用不上这个索引

这是标准的复合索引语义，不是缺陷——但**设计索引时要知道**。

### 4.3 `IndexCache` 非线程安全

> 同一 `Holt` 实例按单线程写使用。

很实在的一条：索引缓存不是线程安全的。多线程写同一个 `Holt` 实例会有问题，
**写要串行**。

### 4.4 事务是单写者语义

> 读旧值用于索引维护，不在 badger 事务冲突检测范围内。

也就是说：事务的原子性是有的（单事务原子落库、索引同事务维护），但
**并发写冲突检测不是强保证**。

这跟 [sunku-cj](/2026/10/22/sunku-cj-embedded-redis/) 里提到的那个问题同一类根源——
读写分离在事务外。区别是 holt 这边**明确写进了文档**。

### 4.5 明确不做的

| 不做 | 说明 |
| --- | --- |
| 分布式 / 多进程共享 | 嵌入式单进程定位 |
| 全文索引 | 只有标量属性索引 |
| Cypher / Gremlin 解析器 | 只用 fluent API |

## 五、和「一个完整图数据库」的距离

| 能力 | Neo4j / Dgraph | holt-cj 1.1.0 |
| --- | --- | --- |
| 顶点/边/属性/多标签 | ✅ | ✅ |
| 邻接查询 | ✅ | ✅ 三种前缀索引 |
| 属性索引（精确/范围） | ✅ | ✅ |
| 复合索引 | ✅ | ⚠️ 受限（最左连续） |
| Gremlin 风格遍历 | ✅ | ✅ 25 个方法 |
| 变长路径 | ✅ | ✅ 固定步数 repeat |
| 最短路径 | ✅ | ✅ BFS + Dijkstra |
| 图算法 | ✅ | ✅ 5 种 |
| 全文索引 | ✅ | ❌ |
| 查询语言解析器 | ✅ | ❌ fluent API |
| 分布式 | ✅ | ❌ |

**定位**：一个**能力相当完整、但只在单进程内可用**的嵌入式图库。

## 六、什么场景合适

**✅ 合适**

- **依赖/调用关系分析**：包依赖、服务调用链、代码引用图
- **路径查找**：两个实体间最短路径、可达性判断
- **环路检测**：构建系统、任务调度里的循环依赖
- **中等数据量的本地图**：几万到几十万顶点，嵌入式部署
- **单机应用 / CLI / 离线分析**
- **不想为图关系写一堆关联表**：`eout:`/`ein:` 比 SQL 中间表直观

**⚠️ 不合适**

- **多进程/多机共享图**（嵌入式定位）
- **需要全文检索**顶点属性（只有标量索引）
- **需要写查询语句**（只能 fluent API）
- **高并发写同一实例**（`IndexCache` 非线程安全 + 单写者语义）
- **超大图（亿级顶点）**——没有分布式和分区

## 七、一个实际例子：依赖关系图

用「项目依赖」演示——这类图的特点是**关系比属性重要**：

```cangjie
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

// 建依赖边
g.createEdge("depends",
    vs["storm-cj"].id,
    vs["badger-cj"].id,
    HashMap<String, JsonValue>())

// 问 1：storm-cj 直接依赖谁？
// 走 eout: 索引
let direct = g.getOutgoingEdges(
    vs["storm-cj"].id, "depends")

// 问 2：谁依赖 badger-cj？
// 走 ein: 索引
let users = g.getIncomingEdges(
    vs["badger-cj"].id, "depends")

// 问 3：有路径吗？最短路径是什么？
if (hasPath(g, vs["storm-cj"].id,
            vs["sunku-cj"].id)) {
    let p = shortestPath(g,
        vs["storm-cj"].id,
        vs["sunku-cj"].id)
}

// 问 4：有没有循环依赖？
let bad = hasCycle(g)
```

这四个问题在新版里**都有直接 API**——第 3、4 个在 1.0.x 里要自己写。

## 八、小结

1.1.0 是一次实质性的能力补齐：

- **实现 720 → 3273 行**，9 个模块
- 补上**属性索引**（精确/范围/复合）、**顶点标签索引**、
  **变长遍历**、**6 种图算法**
- 遍历从 6 个方法扩到 **25 个**
- 修复了**索引与数据的事务一致性**
- **四条限制写进 README**：内存模式定位、索引作用域与类型、
  `IndexCache` 非线程安全、单写者事务语义

如果你在找一个「单进程、能力够用、不用起服务」的图存储，
它现在的能力面已经覆盖了大部分实际需求。

> 底座见[从 Go 移植 BadgerDB 到仓颉](/2026/10/10/badger-cj-porting-notes/)，
> 同期另一个库见 [sunku-cj](/2026/10/22/sunku-cj-embedded-redis/)。
