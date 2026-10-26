---
title: "atelier 怎么用：三种形态、四个概念、一条最短路径"
subtitle: 从零装到跑起来，以及它凭什么跟别的 Agent 方案不一样
date: 2026-10-26 17:00:00
lastmod: 2026-10-26 17:00:00
slug: atelier-getting-started
categories:
  - 软件
tags:
  - Cangjie
  - atelier
  - Agent
  - Harness
  - 入门
---

<p align="center"><strong>atelier 源码拆解 · 零</strong></p>

<p align="center"><em>先能跑起来，再谈它怎么实现</em></p>

> [第一篇](https://ystyle.top/2026/10/26/atelier-agent-harness/)讲它要解决哪六个问题，
> [第二篇](https://ystyle.top/2026/10/26/atelier-lessons-in-corrections/)讲它踩过的坑。
> 但两篇都默认你已经知道它是什么、怎么装、怎么跑——**这篇补上**。
>
> 如果你只想知道「这东西跟我有关系吗」，看第一节就够。

## 一、定位：它是什么，不是什么

一句话：**atelier 是一个纯仓颉实现的 Agent Harness——把模型变成 Agent 的那层脚手架。**

但「harness」这个词不常用，容易和框架、SDK 混。三者站在不同的位置：

| | 它替你决定什么 | 你要写的代码 | 例子 |
| --- | --- | --- | --- |
| **模型 SDK** | 无，只发请求收回响应 | 全部逻辑 | 各家 `chat()` |
| **编排框架** | **流程**：先调 A 再调 B、失败走哪个分支 | 声明流程，框架执行 | LangGraph、工作流引擎 |
| **Agent Harness** | **机制**：循环、上下文、工具、权限、会话 | 挂载工具、配 Agent、选存储 | Claude Code、Codex CLI、atelier |

差别在最后一行。**harness 不替你决定做什么，它提供「自主干活」所需的全部机制。**

这句话展开成三句更好判断：

- 它**不**要求你画流程图 —— 循环由模型自己驱动，你只给工具和约束
- 它**不**是个库函数集合 —— 它真的能把一个模型跑成一个能干活的 Agent
- 它**是**可嵌入的 —— 你既可以 `cli.app run` 直接用，也可以把它挂进自己的服务

README 里的一句话很适合概括：它是**成品工坊**而非**编排框架**。框架要求你按它的抽象描述应用，工坊只给你可挂载的零件。

### 什么时候该用它

适合：

- 想要一个**能自己调工具干活**的 Agent，而不是一问一答
- 已经在仓颉生态里（它的存储、协议层都是仓颉项目）
- 需要**可替换**的组件：换模型、换会话存储、换压缩策略、换权限闸门
- 需要**同一个 Agent 被不同宿主拉起**（终端 / HTTP / 编辑器 / 别的 Agent）

不适合：

- 只想调一次模型 API —— 直接用 provider 包更轻
- 要做**可视化编排**、DAG 工作流 —— 那是工作流引擎的事
- 要多机分布式 —— 它明确是单进程定位
- 主力语言不是仓颉 —— 它的所有扩展点都是仓颉接口

### 它为什么值得单独做一个

仓颉生态里没有现成的。而「把模型变成 Agent」这件事的难点不在调 API，在于那六个机制（循环、上下文、工具、权限、会话、协议）**每个都有大量细节**，且细节之间互相影响——比如工具顺序会影响缓存命中率，压缩时机影响会话能不能续上。

这些细节没法从文档里抄，只能做出来再撞一遍。atelier 现在有 **1029 个测试用例**、**15 个包**，就是这些细节堆出来的。

## 二、四个概念，够你上手

atelier 的 API 面很大（17 个注入点），但上手只需要四个概念：

| 概念 | 是什么 | 一句话 |
| --- | --- | --- |
| **HarnessSpec** | 装配束 | 「这次用哪些零件」——工具、provider、存储、钩子全在里面 |
| **AgentConfig** | 一个 Agent 的定义 | 名字、用哪个模型、系统提示词、能调用哪些工具 |
| **AgentRuntime** | 运行时 | 真正跑循环的东西，`chat()` 出事件流、能取消、能拿会话 id |
| **Message / Event** | 输入与输出 | 进去是消息，出来是事件流 |

前两个是**声明**，后两个是**执行**。记住这个分层，后面就不会乱：

```
HarnessSpec（零件清单）
  + AgentConfig（这个 Agent 怎么配）
            ↓
      AgentRuntime.chat(msgs)
            ↓
    EventStream（一个个事件）
```

**关键设计**：从 `Harness`（便利层）下钻到 `AgentRuntime`（细粒度），用的**是同一份装配束**——没有第二套配置。所以你可以先用三行代码跑起来，需要事件流时再下钻，不用重写。

## 三、最短路径：三条命令跑起来

前置：仓颉工具链（`cjc` 1.1.x）+ `cjpm`。

### 3.1 构建

```bash
git clone \
  https://atomgit.com/ystyle/atelier
cd atelier

# 一条命令构建三个成员
# （核心库 + server + cli）
cjpm build -j 16
```

产物在 `target/release/bin/cli.app`。三个成员分别是：

| 成员 | 产物 | 用途 |
| --- | --- | --- |
| `atelier/` | 静态库 | 核心库，可嵌进别的项目 |
| `server/` | 静态库 | HTTP 服务库 |
| `cli/` | `cli.app` | 终端产品，也是三种形态的入口 |

### 3.2 配一个 provider

`HarnessSpec.default()` **只认环境变量**里的 OpenAI 兼容端点：

```bash
export OPENAI_API_KEY="sk-xxx"
export OPENAI_BASE_URL=\
  "https://api.deepseek.com/v1"
```

> **注意**：默认装配**不读 TOML**。`HarnessSpec.default()` 的实现就是
> `withEnvProvider(withBuiltinTools(HarnessSpec()))`——它只做两件事：注册内置工具、
> 如果环境里有 `OPENAI_API_KEY` 就挂一个名为 `default` 的 provider。
> 换句话说，**零配置能跑的前提是有这两个环境变量**。

想用 DeepSeek、Ollama、多 Agent、MCP，就得写 `~/.atelier.toml`（下一节）。

### 3.3 跑

```bash
# 交互式 TUI（需要真终端）
./target/release/bin/cli.app tui

# 单次执行
./target/release/bin/cli.app run \
  "你好，介绍一下你自己"

# HTTP 服务
./target/release/bin/cli.app serve 8080
```

`run` 的返回就是答案文本。想要机器可读的输出：

```bash
cli.app run --json-events "跑一遍测试" \
  | jq -c 'select(.type=="tool_result")'
```

`--json-events` 把 stdout 改成逐行一个 JSON 对象（JSONL），人类可读进度走 stderr，两边各自可解析。

## 四、写配置文件：从能跑到好用

零配置只覆盖「一个 Agent + 一个 OpenAI 兼容端点」。真实使用需要四个部分。

### 4.1 最小可用配置

写 `~/.atelier.toml`：

```toml
[[provider]]
name = "deepseek"
type = "openai"
baseURL = "https://api.deepseek.com/v1"
apiKey = "${DEEPSEEK_API_KEY}"

[[agent]]
name = "assistant"
model = "deepseek-chat"
provider = "deepseek"
systemPrompt = "你是一个有用的助手"
tools = ["bash", "read_file",
         "write_file", "edit_file",
         "grep", "glob"]
```

`apiKey` 支持 `${ENV_VAR}` 引用——**不要把密钥明文写进配置文件**。

### 4.2 上下文窗口为什么写在 provider 下

这是个容易写错的地方。窗口不是 Agent 的属性，而是 **`(provider, model)` 这一对的属性**：

```toml
[[provider]]
name = "deepseek"
baseURL = "https://api.deepseek.com/v1"
apiKey = "${DEEPSEEK_API_KEY}"

  # 端点上的模型事实
  [[provider.model]]
  name = "deepseek-chat"
  contextWindow = 65536   # 含输入与输出
  maxTokens = 8192        # 默认完成预算
```

为什么不在 `[[agent]]` 里？因为**同名模型走官方端点和走一个截断过的代理，窗口可以不同**。声明在 provider 下是诚实的；声明在 agent 上会掩盖这个事实。

它直接影响压缩：压缩要按「窗口 − 完成预算 − 余量」留预算，窗口填错，压缩就会算错。

### 4.3 MCP 工具

```toml
[[mcpServer]]
name = "playwright"
transport = "stdio"
command = "npx @playwright/mcp"
```

然后在 agent 的 `tools` 里加 `"mcp_*"` 通配——已激活的 MCP 工具会全部暴露。也可以用 `"mcp_playwright_*"` 只暴露某个服务器的。

### 4.4 内置的十个工具

不写 `tools` 时并非没有工具——`HarnessSpec.default()` 注册了这十个：

| 工具 | 作用 |
| --- | --- |
| `read_file` / `write_file` / `edit_file` | 文件读写改 |
| `bash` | 执行命令 |
| `grep` / `glob` | 搜内容 / 找文件 |
| `todo` | 任务清单 |
| `ask_user` | 向用户提问（审批 / 选择 / 表单） |
| `use_skills` | 加载 Skill |
| `load_mcp_toolset` | 按需加载 MCP 工具集 |

`tools` 字段是**白名单**——不写就是「不给任何工具」。这点和「不写就全给」的直觉相反。

## 五、三种形态：同一个 Agent，不同外壳

atelier 最实用的设计是：**同一份装配束，三种形态**。你的 Agent 定义一次，可以：

### 5.1 当终端产品用

```bash
cli.app tui          # 交互式
cli.app run "..."    # 单次
```

TUI 里还有斜杠命令：

| 命令 | 作用 |
| --- | --- |
| `/agent` / `/model` | 切 Agent / 切模型 |
| `/session new\|list\|switch` | 会话管理 |
| `/compact` | 手动压缩 |
| `/trust <path>` | 信任一个目录 |
| `/subagent start \| send \| respond` | 起子 Agent 并与之对话 |

### 5.2 当 HTTP 服务用

```bash
cli.app serve 8080
```

```bash
curl http://localhost:8080/agent/run \
  -H "Content-Type: application/json" \
  -d '{"agent":"default",
    "messages":[{"role":"user",
    "content":"你好"}]}'
```

也可以**挂进自己的服务**，不占新端口：

```cangjie
let handler = AtelierHttpHandler(spec)
handler.registerRoutes(server.distributor)
```

### 5.3 被别的宿主拉起

这是它和「自己写个 Agent」最大的区别。atelier 实现了两个协议的服务端：

| 命令 | 协议 | 谁拉起它 |
| --- | --- | --- |
| `cli.app acp` | ACP v1（stdio） | Zed、opencode、JetBrains |
| `cli.app a2a [port]` | A2A v1（HTTP） | 别的 Agent / 编排器 |

以 Zed 为例，`settings.json` 里加一段就行：

```json
{
  "agent": {
    "command": "atelier",
    "args": ["acp"]
  }
}
```

**能力不是摆设**。ACP 侧支持 `session/new`、流式 `session/update`、`session/cancel`、`session/load`（重放历史）、`additionalDirectories`（附加工作区自动预信任）；A2A 侧支持 SSE 流式、推送通知、Bearer 认证、按调用方隔离任务可见性，还能反向把**远端** A2A Agent 接成自己的子 Agent。

> stdout 只输出协议帧，日志一律走 stderr——stdout 被污染会导致协议错乱。

### 5.4 当库嵌进项目

```toml
[dependencies]
atelier = { path = "/path/to/atelier" }
```

最省事的三行：

```cangjie
import atelier.agent.*

let h = Harness.open()
println(h.run("你好"))
h.close()
```

要换零件就派生装配束（`with*` 只影响这一份，不写穿共享组件）：

```cangjie
let spec = HarnessSpec.default()
    .withProvider("default",
        OpenAIProvider("default",
            baseUrl, apiKey))
    .withStore(
        StormSessionStore("./sessions"))
    .withTool(SqlTool())
    .withHook(AuditHook())

let h = Harness.open(spec)
```

需要事件流、会话 id、取消时，从**同一个装配束**下钻：

```cangjie
let runtime = AgentRuntime(spec, cfg)
let stream = runtime.chatWithSessionId(
    sid, msgs, env)
for (event in stream) { ... }
runtime.cancelSession(sid)
```

## 六、第一次跑会遇到什么

按顺序列，都是新手真会撞的：

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| `run` 能跑但模型说「没有工具」 | `tools` 是白名单，没写就等于不给 | 在 `[[agent]]` 里显式列工具 |
| 读文件、执行命令全被拒 | 信任闸门：目录未信任 | TUI 里审批一次，或 `/trust <path>` |
| 无人值守时工具全部被拒 | `run` 没有提问通道，需用户拍板的一律按「取消」处理 | `ATELIER_TRUST_DIR="$PWD" cli.app run "..."` |
| 很快就压缩，或压不动 | `contextWindow` 没声明或填错 | 在 `[[provider.model]]` 里声明真实窗口 |
| 配了 `DEEPSEEK_API_KEY` 却用不上 | 默认装配只认 `OPENAI_API_KEY` | 要么改环境变量名，要么写 TOML |
| 子 Agent 卡住不返回 | 父侧在等、子侧没登记等待 | 已修（见[第二篇](https://ystyle.top/2026/10/26/atelier-lessons-in-corrections/)） |
| `tui` 报错退出 | stdin 不是 tty | 非交互环境用 `run` |

最后一条值得展开：**`run` 是真正的无人值守模式**——它不读 stdin，也没有提问通道。所以信任必须提前用环境变量声明，否则 `bash`、`write_file` 这些会被一律拒绝。这不是 bug，是设计：无人值守时不该有「等人点确认」的分支。

## 七、怎么选形态

一张表收尾：

| 你的场景 | 用哪个形态 |
| --- | --- |
| 自己用来干活 | `cli.app tui` |
| 脚本 / CI 里跑一次 | `cli.app run --json-events` |
| 给团队提供 Agent 服务 | `cli.app serve` 或挂进既有服务 |
| 在编辑器里用 | `cli.app acp`（Zed / opencode） |
| 让别的 Agent 调用它 | `cli.app a2a` |
| 嵌进自己的仓颉程序 | 依赖核心库，`Harness.open(spec)` |
| 要审查它的行为 | `--json-events` + 事件流 |

## 八、小结

- **定位**：Agent Harness，不是框架也不是 SDK——它提供机制，不替你决定流程
- **四概念**：`HarnessSpec`（零件）+ `AgentConfig`（配置）→ `AgentRuntime`（执行）→ 事件流
- **最短路径**：`cjpm build` → 配 `OPENAI_API_KEY` → `cli.app run`，三条命令
- **配置文件**：provider / agent / mcpServer 三段，其中**窗口写在 provider 下**
- **三种形态**：终端、HTTP、被宿主拉起（ACP/A2A），外加库嵌入——**同一份装配束**
- **两个最容易错的点**：`tools` 是白名单（不写就没工具）；默认装配不读 TOML

> 装完之后想知道它内部怎么实现的，看
> [第一篇](https://ystyle.top/2026/10/26/atelier-agent-harness/)（六个问题怎么解）；
> 想知道它踩过哪些坑，看[第二篇](https://ystyle.top/2026/10/26/atelier-lessons-in-corrections/)。
