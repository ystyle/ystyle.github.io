---
title: MCP-Term：一个未出生即夭折的想法
date: 2026-03-19 20:00:00
updated: 2026-03-19 20:00:00
tags:
- MCP
- AI
- Protocol
- Abandoned
categories: 思考
permalink: mcp-term-abandoned
---

> **⚠️ 已弃坑**
>
> 此项目在讨论阶段即放弃，无任何代码实现。
> 放弃原因：市场风向转变，目标场景已被钉钉、Obsidian CLI, anything CLI 等原生工具覆盖。
> 记录此文仅为保存思考过程。

---

## 起因：MCP 协议的 Token 困境

一切始于一个问题：**MCP 和 Function Call 有什么区别？**

讨论后得出结论：
- Function Call 是模型的底层能力
- MCP 是应用层协议，解决生态碎片化
- 但 MCP 的 JSON Schema 在 LLM 上下文中**极度费 tokens**

一个复杂工具的 JSON Schema 定义可能消耗 500-1000 tokens，而模型能理解更紧凑的格式——比如 TypeScript 的 `.d.ts`。

## 核心想法：用 S-Expr 替代 JSON

### 方案演进

**最初设想**：修改 MCP 协议
- Schema 用 `.d.ts` 定义（省 50% tokens）
- 传输用 CBOR（省带宽）

**第一次收缩**：不改协议，做转换层
- 客户端转换：JSON Schema → S-Expr → LLM
- 调用时：LLM 生成 S-Expr → 转回 JSON-RPC
- 兼容现有 MCP Server，零改动

**最终定位**：CLI 工具
- 不是协议扩展，而是命令行包装器
- 解决复杂嵌套参数在 CLI 中的表示问题

### MCP-Term 协议设计

设计了名为 **MCP-Term**（原名 MCP-Symbol）的 S-Expr 格式。

#### 基础语法

```
; 原子类型
number     := [0-9]+(\.[0-9]+)?          ; 整数或浮点
string     := "([^"\\]|\\.)*"            ; 双引号字符串
symbol     := [a-zA-Z_][a-zA-Z0-9_]*     ; 标识符
keyword    := :[a-zA-Z_][a-zA-Z0-9_]*    ; 冒号前缀，如 :utf8
list       := '(' expr* ')'              ; S-表达式列表
```

#### 工具声明

```
(declare
  (symbol long-name params return-type doc-string?)
  ...
)

; symbol      : 短码，1-4 字符，调用时用
; long-name   : 人类可读全称
; params      : (param-name type default? option*)*
; return-type : 返回类型
; doc-string  : 可选描述
```

示例：

```
(declare
  ;; 文件操作
  (fr file_read 
    (path string) 
    (opt (enc (or :utf8 :base64) :utf8)
         (off (opt number) nil)
         (lim (opt number) nil))
    string
    "Read file content")
  
  ;; 笔记操作
  (nu note_update
    (doc string)
    (ops (list Op))
    (tuple (ver number) (blocks (list Block)))
    "Update document with operations")
)
```

#### 类型系统

**基础类型**：`string` `number` `bool` `bytes` `any`

**复合类型**：

```
(list type)           ; 同质列表 => string
(map key-type val-type)  ; 映射 => int
(tuple type*)         ; 异构元组 => int)  ; 联合类型 => :utf8 :base64)  ; 可选，等价 => nil
```

**自定义类型**：

```
(deftype Op
  (i insert (pos number) (blocks (list Block)))
  (d delete (pos number) (len number))
  (r retain (pos number)))

(deftype Block
  (p paragraph (id string) (props (map keyword any)) (content (list Inline)))
  (h heading (level (or 1 2 3 4 5 6)) (content (list Inline)))
  (c code (lang (opt string)) (content string))
  (i image (src string) (alt string) (props (map keyword any))))
```

#### 调用格式

```
; 简单调用
(fr "/etc/hosts" :utf8)

; 嵌套调用（笔记编辑）
(nu "doc.md"
  (i 0 ((p "intro" () ("Hello world"))))
  (d 20 5))

; 批量调用
(batch
  (1 (fr "/etc/passwd"))
  (2 (fr "/etc/hosts"))
  (3 (ex "whoami")))
```

#### 返回格式

```
; 成功
(ok "file content here")
(ok (out "root" code 0))

; 错误
(err 404 "file not found")
(err 1 "command failed" (stderr "permission denied"))
```

#### JSON Schema 映射

| JSON Schema | MCP-Term |
|-------------|----------|
| `{"type": "string"}` | `string` |
| `{"type": "number"}` | `number` |
| `{"type": "boolean"}` | `bool` |
| `{"type": "array"}` | `(list any)` |
| `{"type": "object"}` | `(map keyword any)` |
| `{"enum": ["a","b"]}` | `(or :a :b)` |
| `{"type": ["string","null"]}` | `(opt string)` |
| `{"properties": {...}}` | `map` 或 `tuple` |

#### 复杂示例：企业数据查询

JSON Schema（约 3500 字符，1000+ tokens）：

```json
{
  "name": "data_platform_query",
  "inputSchema": {
    "type": "object",
    "properties": {
      "sources": {
        "type": "array",
        "items": {
          "oneOf": [
            {"type": "object", "properties": {"type": {"const": "sql"}, ...}},
            {"type": "object", "properties": {"type": {"const": "mongodb"}, ...}},
            {"type": "object", "properties": {"type": {"const": "api"}, ...}}
          ]
        }
      },
      "joins": {...},
      "transformations": {...},
      "output": {...}
    }
  }
}
```

MCP-Term（约 600 字符，170 tokens）：

```
(dp data_platform_query
  (qid string)
  (srcs (list Source 1 10))
  (joins (opt (list Join)))
  (trans (opt (list Xform)))
  (out Output)
  -> QueryResult)

(deftype Source (or SQL Mongo API))
(deftype SQL (sql (driver :pg|:my|:ch) (host string) (db string) (q (sql string))))
(deftype Join (join (left string) (right string) (type :inner|:left|:right) (on (list Cond))))
(deftype Xform (or (filter (cond string)) (agg (group (list string)) (aggs map))))
```

**Token 节省对比**：

| 场景 | JSON Schema | MCP-Term | 节省 |
|------|-------------|----------|------|
| 简单工具（3参数） | 180 | 60 | 67% |
| 复杂工具（10参数） | 600 | 150 | 75% |
| 超复杂（嵌套查询） | 3500 | 600 | 83% |
| 实际调用（嵌套操作） | 200 | 50 | 75% |

## 市场验证：风向已变

### 现有方案调研

调研了几个 MCP-CLI 项目：

1. **mcp-cli**：直接传 JSON 字符串，绕开参数问题
2. **FastMCP**：简单 key=value 参数
3. **cyclopts**：自动生成 `--flag`，嵌套时参数爆炸

**关键发现**：都没解决深层嵌套，但用户似乎不在意——因为有更简单的方案。

### 场景消失

原计划的目标场景：

**场景1：CLI 工具嵌套参数**
- 但市场风向已变：钉钉 CLI、Obsidian CLI、香港大学的 anything CLI 等纷纷涌现
- **CLI + Skills** 模式成为大趋势：用户通过 skills 模板封装复杂操作，而非手写嵌套参数
- 管道 + base64 等简单方案已覆盖大部分场景
- 结论：无需 S-Expr，市场已给出更简单的答案

**场景2：数据复杂查询**
- 现有方案：BI 工具（可视化）、JSON 配置
- 结论：市场 niche，且竞品成熟

**市场变化**：
- 原生 CLI 工具链成熟，各家都在做自己的 CLI
- Skills 模板封装成为主流，复杂操作被预定义
- 大模型直接操作文件/API，中间层价值稀释

## 放弃决策

### 直接原因

1. **场景消失**：复杂嵌套参数需求被简化方案覆盖
2. **竞争出现**：原生 CLI 生态成熟，无差异化空间
3. **时间成本**：继续验证已无意义，市场已给出答案

### 根本原因

- 从"协议扩展"退到"CLI 工具"时，价值已打折
- CLI 层无技术壁垒，易被复制/绕过
- 大模型进化快，中间层易被端到端替代

## 收获

虽无代码产出，但获得：

1. **快速验证方法论**：市场调研 → 场景分析 → 放弃决策
2. **止损判断标准**：当目标场景被简化方案覆盖时，放弃
3. **MCP 生态理解**：协议设计、现有工具链格局

## 未来信号

若出现以下情况，可重新评估：

1. 新协议需要紧凑嵌套表示
2. LLM 上下文窗口瓶颈重现（<4K）
3. 特定领域出现复杂结构 CLI 痛点

**当前：无。**

