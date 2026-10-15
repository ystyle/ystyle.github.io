---
title: "Go 一行注释就能把整个文件绑到平台，仓颉为什么不行？"
subtitle: 拆开「仓颉不能按文件分平台」这句话：它其实有三种粒度，以及一个真实项目绕的弯
date: 2026-10-15 10:00:00
lastmod: 2026-10-15 10:00:00
slug: cangjie-multiplatform-for-go-devs
categories:
  - 软件
tags:
  - Cangjie
  - golang
  - 跨平台
  - mmap-cj
---

<p align="center"><strong>从 Go 的 <code>//go:build</code> 到仓颉的 <code>common</code>/<code>specific</code></strong></p>

<p align="center"><em>拆开「仓颉不能按文件分平台」这句话：它其实有三种粒度，以及一个真实项目绕的弯</em></p>

<p align="center"><code>Cangjie</code> · <code>Go</code> · <code>跨平台</code> · <code>mmap-cj</code></p>

> 如果你写过 Go，多半见过 `src/net/fd_js.go` 这类文件——开头一行 `//go:build js`，整个文件就只属于 js 平台。转到仓颉之后你会发现：**没有等价的一行注释**。
>
> 这篇写给有 Go 背景的人。结论是：仓颉不是「不行」，而是**把这件事拆成了三种粒度**，你得先知道有哪三种，再决定用哪种。
>
> 文中所有仓颉命令与报错，都是本机 `cjc/cjpm 1.2.0` 实跑出来的；项目案例是真实的 `mmap-cj`——它先后用了两套方案，中间还切回去过一次。

---

## 一、先把 Go 那一行读明白 {#一先把go那一行读明白}

`src/net/fd_js.go` 是这样的：

```go
// Fake networking for js/wasm. It is intended to allow tests of other package to pass.

//go:build js          // ← 整个文件只在 js 平台编译

package net

import (
	"os"
	"syscall"
)

func (fd *netFD) closeRead() error {
	if fd.fakeNetFD != nil {
		return fd.fakeNetFD.closeRead()
	}
	return os.NewSyscallError("closeRead", syscall.ENOTSUP)
}
```

关键在于：**Go 的 `net` 包不是「一个实现 + 若干平台覆盖」，而是「同一批文件里，每个平台挑一组编译」。**

`src/net/` 目录下躺着 `fd_js.go`、`fd_plan9.go`、`fd_posix.go`、`fd_unix.go`、`fd_wasip1.go`、`fd_windows.go`。在 js 平台上编译时，`fd_unix.go` **压根不参与编译**——所以 `closeRead` 的 js 版本是全包唯一的那一份，不存在「覆盖」这回事。

Go 判断文件归属用三道闸门，**全都不需要写配置**：

| 闸门 | `fd_js.go` 里对应什么 |
| --- | --- |
| ① 文件名后缀 | `_js`（`xxx_GOOS.go`、`xxx_GOARCH.go`、`xxx_GOOS_GOARCH.go` 会被隐式当作约束） |
| ② 构建约束注释 | `//go:build js`（布尔表达式，支持 `\|\|` `&&` `!` 和括号） |
| ③ 环境变量 | `GOOS=js GOARCH=wasm`，决定上面两个标签是否满足 |

还能组表达式：

```go
//go:build (linux && 386) || (darwin && !cgo)
//go:build !(cgo && (linux || darwin))
//go:build ignore     // 永不参与构建
```

顺带一个细节，说明这套机制有多「物理」：同目录的 `fd_fake.go` 用的约束是 `//go:build js || wasip1`——也就是说，**一个平台可以由多个文件共同组成**，文件之间不需要有任何对应关系。

> **一句话**：Go 的哲学是**编译期物理排除**。不参与编译的文件就是一坨文本，里面的符号未定义也不会报错。于是你可以放心写「只有这个平台才有」的 API。

---

## 二、仓颉为什么不能直接照抄 {#二仓颉为什么不能直接照抄}

因为仓颉想回答的问题不太一样。

Go 的 `//go:build` 解决的是「**平台专有代码放哪儿**」——一个文件组织问题。谁跟谁配对、签名一致不一致，Go 不管。

而仓颉在设计 `common`/`specific` 时，想解决的是「**跨平台 API 的契约怎么立**」——一个接口契约问题：这个函数在所有平台都该存在，但各平台实现不同，**而且签名必须一致**。

这是两种诉求。所以仓颉长出了三种不同粒度的机制：

| 层次 | 粒度 | 机制 | 成熟度 |
| --- | --- | --- | --- |
| 声明级 | 单个函数 / 类 / 成员 | `common` / `specific` 修饰符 | 1.1.0 起，**实验性** |
| 文件 / 目录级 | **整个文件、整个目录** | `cjpm` 的 `source-set` + `features` | 1.1.0 起，**实验性** |
| 声明 / 导入级 | 单个声明、单条 import | `@When[os == "Linux"]` | 已有，非实验 |

**真正对标 Go `//go:build` 的是第二层**——`cjpm` 的 `source-set`。但它需要你在 `cjpm.toml` 里显式声明「目录 ↔ feature」的映射，远不如一行注释省事。这就是体感差距的来源。

---

## 三、机制一：`@When` 条件编译（最接近、但粒度更细） {#三机制一when条件编译最接近但粒度更细}

这是最容易上手的一套，也是**目前最实用**的一套。

```cangjie
@When[os == "Linux"]
func foo() {
    print("Linux, ")
}

@When[os == "Windows"]
func foo() {
    print("Windows, ")
}

@When[os != "Windows"]
func fee() {
    println("NOT Windows")
}

@When[os != "Linux"]
func fee() {
    println("NOT Linux")
}

main() {
    foo()
    fee()
}
```

我在 Linux 上实跑，输出：

```text
Linux, NOT Windows
```

内置条件变量（`manual/source_zh_cn/compile_and_build/conditional_compilation.md`）：

| 条件 | 取值 / 运算符 |
| --- | --- |
| `os` | `Windows` / `Linux` / `macOS`，支持 `==` `!=` |
| `backend` | `cjnative` / `cjvm`，支持 `==` `!=` |
| `arch` | `x86_64` / `aarch64`，支持 `==` `!=` |
| `cjc_version` | `xx.xx.xx`，支持 `==` `!=` `>` `<` `>=` `<=` |
| `debug` | 仅逻辑非 `!`（是否开 `-g`） |
| `test` | 仅逻辑非 `!`（是否 `--test`） |

多条件可以组合：

```cangjie
@When[(test || feature == "lion") && !debug]
func fee() { println("feature lion") }
```

自定义条件走 `--cfg`：

```shell
cjc --cfg "feature = lion, platform = dsp" source.cj
```

**和 Go 的差别**：`@When` 挂在**声明或 import** 上，不是文件上。所以每个顶层声明都得单独标一遍。

限制有两条要记：

- **不支持嵌套**。连续两个 `@When` 会报错——注意实际文案与文档不同，1.2.0 上是：

    ```text
    error: duplicated annotation: '@When'
    ```

    （文档里写的是旧文案 `illegal nested when conditional compilation`。）
    想同时满足两个条件，写成 `@When[os == "Linux" && arch == "x86_64"]` 即可，实测输出 `both`。

- 由**宏展开**产生的代码里含 `@When[...]` 会编译报错（它在导入前处理）。

写错平台会怎样？很好懂——**找不到那个符号**：

```cangjie
@When[os == "Windows"]
func windowsOnly(): Unit { println("这行只有 Windows 会编译") }

main() {
    windowsOnly()
}
```

在 Linux 上编译：

```text
error: undeclared identifier 'windowsOnly'
```

> 这正是「编译期物理排除」的效果：Windows 那一份根本没进编译，所以 `windowsOnly` 这个名字在 Linux 上不存在。跟 Go 行为一致。

---

## 四、机制二：`source-set` + `features`（对标 `//go:build`） {#四机制二source-set--features对标gobuild}

想要 Go 那种「整个目录绑平台」，就得用这层。

### 4.1 `cjpm.toml` 里声明映射

```toml
[profile]
experimental = true          # 实验特性，必须开

[package]
  cjc-version = "1.2.0"      # 必填，漏了会报 can't be empty
  name = "cjdemo"
  output-type = "executable"
  version = "1.0.0"

[[source-set]]
name = "common"              # 可选，仅用于调试报错
src-dir = "./common"
features = []                # 空 = 公共源码集，所有产品源码集都带上

[[source-set]]
src-dir = "./linux"
features = ["os.linux"]
product = true               # 显式声明为「产品源码集」

[[source-set]]
src-dir = "./windows"
features = ["os.windows"]
product = true
```

概念（官方文档口径）：

- **源码集（source-set）**：特定 feature 下要编译的源码目录；
- **产品源码集**：合入所有上游源码集后能编译出二进制的那个；没有出边的都算，有出边的可显式配 `product = true`；
- **公共源码集**：`features` 为空的源码集，所有产品源码集编译时都包含它。

内置 feature 是这批：

```text
os.android   os.ohos   os.ios   os.linux   os.windows   os.darwin
```

> ⚠️ 命名口径不一致，很容易写混：**`cjpm` feature 用小写点分**（`os.linux`），而 **`@When` 里 `os` 的值是首字母大写字符串**（`@When[os == "Linux"]`）。两套东西。

### 4.2 文件头还得自己声明

光配 `cjpm.toml` 不够，**源码文件里也要声明自己的 feature**，而且必须写在 `package` 之前：

```cangjie
features {}                 // 公共源码集
package cjdemo
```

```cangjie
features {os.linux}         // 平台源码集，与 toml 里的 features 保持一致
package cjdemo
```

非产品源码集要加 `@NonProduct`：

```cangjie
@NonProduct
features {}
package cjdemo
```

### 4.3 两套机制是配合的，不是二选一

我实测搭了一个最小工程，撞了几堵墙，这些文档没直说：

| 现象 | 报错 | 原因 |
| --- | --- | --- |
| 公共源码集忘了 `@NonProduct` | `Feature header of package 'cjdemo' is missing '@NonProduct' annotation` | 有出边的源码集要标 `@NonProduct` |
| 两个 source-set 的 `features` 完全相同 | `source set 'app' with the same features is declared at ...` | **一个 feature 组合只能对应一个目录** |
| `main` 放在非产品源码集 | `'main' is missing` | `main` 必须在产品源码集里 |
| 公共部分写了无函数体的 `func` | `body of function 'Platform' is missing` | 源码集**不提供**契约机制 |

最后一条尤其关键：**公共源码集里的无体函数，必须加 `common` 才合法。**

```cangjie
// common/platform.cj
@NonProduct
features {}
package cjdemo

public common func Platform(): String      // ← 只留签名，加 common 才认
```

```cangjie
// linux/linux.cj
features {os.linux}
package cjdemo

public specific func Platform(): String { "Linux" }

main() {
    println(Platform())
}
```

也就是说：**`source-set` 负责「哪个目录参与这次编译」，`common`/`specific` 负责「公共部分怎么声明契约」**，两者是配合关系。

### 4.4 构建与产物

```shell
cjpm build --no-feature-deduce --enable-features=os.linux
cjpm build --no-feature-deduce --enable-features=os.windows
```

产物落在 `target/release/bin/<source-set名>/product/`：

```text
target/release/bin/
├── linux/product/main
└── windows/product/main
```

实测（同一台 Linux 机器）：

```text
$ ./target/release/bin/linux/product/main
Linux
$ ./target/release/bin/windows/product/main
Windows
```

> ⚠️ **这不是交叉编译**。两个 `main` 都是当前平台的产物，只是**编译期选进了不同的源码集**。想真跨到别的架构/系统，那是 `--target` 的事。

---

## 五、机制三：`common` / `specific`（声明级契约，Go 没有对应物） {#五机制三common--specific声明级契约go没有对应物}

```cangjie
// 公共部分代码
package cmp

public common func foo(): Unit {
    println("I am common")
}
```

```cangjie
// 平台部分代码
package cmp

public specific func foo(): Unit {
    println("I am specific")
}
```

**两个文件都是 `package cmp`**——公共部分和平台部分属于同一个包，区别只是放在哪个目录、由哪次编译参与。

支撑范围相当全：全局函数、`class`/`struct`/`enum`/`interface` 及其成员、`extend`、泛型声明都支持。**不支持**的：静态成员变量、主构造函数、静态初始化器；`@Frozen` 修饰 `common/specific` 行为异常（文档「约束」节）。

三条最重要的规则：

1. `common` 有**完整实现**时，可以**不写** `specific`；`common` **只有签名**时，**必须**有对应的 `specific`。
2. `specific` 的签名必须匹配：参数类型一致、返回值相同或**子类型**、修饰符（除 `common`/`specific` 外）一致。
3. **每个 `specific` 必须匹配唯一的 `common`**。

「`specific` 会覆盖 `common`」这条我实测确认了——两边都写实现时，跑出来是：

```text
I am specific
```

而匹配关系是**编译期强校验**的，全部实测报错：

```text
error: 'common' function return type must be specified
error: 'common' and 'private' modifiers conflict on function declaration
error: at least one constructor is required in common class 'A'
error: 'specific' function 'bar' can not find 'common' match
error: 'common' function 'foo' can not find 'specific' match
```

**这几条恰好说明了两边的根本差异**：Go 是**排除法**，不建立文件之间的对应关系；仓颉是**配对法**，`common` 漏了实现、`specific` 多写了东西，编译器两遍都会查出来。

---

## 六、一个真实项目绕的弯 {#六一个真实项目绕的弯}

理论说完，来看 [`mmap-cj`](https://atomgit.com/ystyle/mmap-cj)——一个跨平台内存映射文件库（Linux/macOS/Windows）。它的 git 历史比任何文档都有说服力：

```text
2026-04-11  590d9e4  最初提交
                     方案：common/specific + cjpm source-set
                     src/common/mmap.cj（common class MmapFile）
                     src/linux/mmap_impl.cj（11 处 specific）
2026-07-17  fcb774e  重构为顶层 source-set 目录布局
                     src/common → common/、src/linux → linux/
2026-10-06  bbf668a  分支 feat/source-set-layout 定稿
2026-10-06  698e673  切回单 src 布局，用 @When 替代 source-set   ← 关键转折
2026-10-06  cc40de1  v1.1.0（master）
```

source-set 版完整代码在分支 [`feat/source-set-layout`](https://atomgit.com/ystyle/mmap-cj/tree/feat/source-set-layout)，可以和 master 对着看。

### 为什么切回去

提交信息写得很直白：

> source-set（多平台源码集）是 cjpm 的 experimental 特性：**消费者必须同样声明 `[profile] experimental = true` 才能编译本库**，否则报 `path of src directory 'src' ... does not exist`；而其正式发布尚需时间。改为单 src + `@When` 条件编译后，本库不再依赖 experimental，普通 cjpm 即可构建与测试。

我把这个因果链完整复现了一遍。

**消费者（不开 experimental）依赖 source-set 版库：**

```text
$ cjpm build
Error: path of src directory 'src' in .../mmap-cj/cjpm.toml does not exist
Error: cjpm build failed

$ cjpm test
Error: path of src directory 'src' in .../mmap-cj/cjpm.toml does not exist
Error: cjpm test failed
```

**同一个消费者，只是加上那一行：**

```toml
[profile]
experimental = true
```

```text
cjpm build success
```

**换成 `@When` 版的库，消费者什么都不用改：**

```text
$ cjpm build
cjpm build success
ok: @When 版库，消费者不开 experimental 也能构建
```

原因是：consumer 没开 experimental 时，`cjpm` 会**忽略依赖库 `cjpm.toml` 里的 `[[source-set]]` 配置**，回退到按默认 `src` 目录查找——而 source-set 版的库根本没有 `src/`，于是报错。

### 但真正致命的是这个：打开了开关，`test` 依然跑不了

上面那一步还只是「配置问题」。我按提示加上 `experimental = true` 之后，遇到了一个更硬的问题：

```text
$ cjpm build
cjpm build success          # ← 构建过了

$ cjpm test
Error: cjpm test failed      # ← 测试还是挂
```

我把两种情况**在同一台机器、同一个消费者工程上对照跑**了一遍，矩阵很清楚：

| 消费者 `experimental` | 依赖的库 | `cjpm build` | `cjpm test` |
| --- | --- | --- | --- |
| 关 | source-set 版 | ❌ | ❌ |
| **开** | **source-set 版** | **✅** | **❌** |
| 关 / 开 | `@When` 版 | ✅ | ✅ |

**也就是说：只要依赖了 source-set 布局的库，这个项目的单元测试就没法跑——不管你怎么配。**

失败发生在**链接**阶段，看不出具体原因（`cjpm` 只回一句 `cjpm test failed`）。我把链接命令捞出来过滤，才看到真正缺的东西：

```text
undefined reference to `_CN6mmapcj8MmapFile5closeHv'
undefined reference to `_CN6mmapcj8MmapFile5writeHRNat5ArrayIhEl'
undefined reference to `_CN6mmapcj8MmapFile6<init>HRNat6StringElb'
undefined reference to `mmapcj:MmapFile.ti'
```

而且那条链接命令里**根本没有 `-lmmapcj`**——同一构建里普通依赖的库都链接了，唯独漏了这个。

> 顺便说，为什么 `build` 能过而 `test` 不能：两边的链接命令是**分别生成**的。`build` 那条走对了路径，`test` 这条没有。

### 这个问题已经上报并修好了

这不是我一个人的环境问题。它被整理成 issue 上报：

- **issue**：[`Cangjie/UsersForum#3515` — cjpm test 无法解析 `[[source-set]]` 依赖](https://gitcode.com/Cangjie/UsersForum/issues/3515)
- **修复 PR**：[`Cangjie/cangjie_tools#1311`](https://gitcode.com/Cangjie/cangjie_tools/pulls/1311)
- **回归用例 PR**：[`Cangjie/cangjie_test#2261`](https://gitcode.com/Cangjie/cangjie_test/pulls/2261)

issue 里定位到两个缺陷，和我在上面观察到的现象一一对应：

1. **编译 test runner 时没传依赖的 `--import-path`**（同一构建里其它包都带了，唯独这条没有）；
2. **链接测试二进制时没链接该依赖的静态库**。

修复补在两处：给 test runner 编译补上依赖产物目录（注意 source-set 包的产物在 `<pkg>/<outputSuffix>/` 这类**带后缀的子目录**里，不能只给 `targetDir`）、链接路径补上 `outputSuffix`；同时让 test runner 编译与普通包一致地带上 `--experimental`。

修好之后，那些依赖 source-set 库的项目就能正常 `cjpm test` 了。

### 那 `mmap-cj` 当时该怎么选

把时间线摊开看，它面临的是一个**先有鸡还是先有蛋**的处境：

- `source-set` 是**实验特性**，会把「开实验开关」的成本转嫁给所有消费者；
- 而消费者**即便开了开关，测试仍然跑不了**（就是上面那个 cjpm 缺陷）；
- `mmap-cj` 是别人要用的库，被 `badger-cj` 依赖着——`badger-cj` 有几百个单元测试等着跑。

于是它切回了 `@When`：**不用实验开关，消费者 build 和 test 全通。** 代价就是下一节说的、满屏的重复标注。

> 这个决定不是「`source-set` 不好」，而是**在缺陷修好之前，一条能测的路比一条不能测的路更重要**。

### 这不是纸面推演，真实的第三方消费者已经撞上了

`badger-cj` 目前依赖 `mmap-cj`，它的 `cjpm.toml` 第一段就写着：

```toml
[profile]
# 依赖 mmap-cj 使用 experimental 的 [[source-set]] 多平台布局，消费侧需同样开启
# （否则 cjpm 忽略其 source-set 配置、按默认 src 查找而报错）
experimental = true
```

**一个库的实验特性，逼着所有下游一起打开实验开关**——这就是 `mmap-cj` 切回 `@When` 的直接原因。而开关打开后测试仍然失败，则把这条路彻底堵死了。

### 代价也是真实的

切回 `@When` 后，`master` 上的 `@When` 密度是这样的：

| 文件 | 行数 | `@When` 数量 |
| --- | ---: | ---: |
| `src/mmap_linux.cj` | 178 | 8 |
| `src/mmap_darwin.cj` | 180 | 8 |
| `src/mmap_windows.cj` | 250 | 8 |
| `src/mmap_test.cj` | 235 | 4 |
| `src/mmap.cj` | 16 | 1（只在注释里提到） |

每个顶层声明（FFI 声明、常量、实现类）都得单独标一遍 `@When[os == "..."]`。**声明一多，就是成片的重复标注**——这也是 Go 那种文件级方案的诱人之处。

顺带说，`@When` 版实测 `cjpm test` 6/6 通过，source-set 版 `cjpm test --enable-features=os.linux` 同样 6/6 通过。**两套方案都能用，差别在消费成本。**

---

## 七、对照速查表 {#七对照速查表}

| 你想在 Go 里做的事 | 仓颉对应写法 | 备注 |
| --- | --- | --- |
| `//go:build js` + `fd_js.go` | `cjpm` source-set（目录）+ 文件头 `features {os...}` | 需改 `cjpm.toml`，且是实验特性 |
| 同包内多平台同名函数 | `common func F()` + 各平台 `specific func F()` | 签名强制配对 |
| 只按平台择一，不要契约 | `@When[os == "..."]` 标在每个声明上 | **当前最实用** |
| `//go:build !windows` | `@When[os != "Windows"]` | |
| `-tags myfeature` | `--cfg "myfeature = xxx"` 或自定义 feature | |
| `GOOS=js GOARCH=wasm go build` | `cjpm build --target=...` | |
| 文件名后缀 `_linux.go` | 无等价物 | 必须显式配置或标注 |

---

## 八、踩坑清单 {#八踩坑清单}

1. **别把 `common/specific` 当成 Go 的 `//go:build`**。前者是声明级契约（强制校验签名），后者是文件级排除（零校验）。
2. **`os` 取值大小写不一致**：`@When[os == "Linux"]` 大写，`cjpm` feature `os.linux` 小写。
3. **`source-set` 一个 feature 组合只能对应一个目录**。
4. **`main` 必须在产品源码集里**。
5. **公共源码集要 `@NonProduct`**，文件头的 `features` 必须和 `cjpm.toml` 完全一致。
6. **`source-set` 会传染，而且会传染两次**：库用了，消费者得开 `experimental`；在旧版 cjpm 上，**开了开关测试仍跑不了**（链接漏依赖库，issue #3515）。给第三方用的库，慎用。
7. **`source-set` 不是交叉编译**，目标平台仍由 `--target` 决定。
8. **两套跨平台机制都是实验特性**。`cjc` 侧要 `--experimental`，`cjpm` 侧要 `[profile] experimental = true`。

> 一个附带的实测发现：官方文档里 `cjc` 三段式编译的第二步写的是把 chir 当位置参数传，但 1.2.0 上会报 `common .chir files count should be equal to common .cjo files count`。**能跑通的是用 `--common-part-chir` 显式传**（`cjc --help` 里有这个选项）。另外 `--output-dir` 指向的目录**必须先存在**。

---

## 结语 {#结语}

回到最初那句「Go 可以声明整个文件对应某个平台，仓颉不行」——更准确的说法是：

**仓颉有对标 Go 的那一层（`cjpm` source-set），能力和 Go 对得上；但它是实验特性、要写配置，而且会把「实验性」的成本转嫁给消费者。**

`mmap-cj` 走过的弯是个典型样本：`source-set` 本身没问题（它自己的 6 个测试全过），问题出在**别人依赖它之后**——消费者不仅要跟着开实验开关，在当时的 cjpm 上还会撞上「测试链接漏依赖库」的缺陷，连单元测试都跑不了。

好消息是那条路已经修了（[issue #3515](https://gitcode.com/Cangjie/UsersForum/issues/3515) → [PR #1311](https://gitcode.com/Cangjie/cangjie_tools/pulls/1311)）。**等 `source-set` 转正、不再需要消费者开开关，它会重新变得有吸引力。**

在那之前，给第三方用的库，`@When` 更稳妥——它啰嗦，但它不挑使用者。

---

*本文仓颉侧命令与报错均由 `cjc 1.2.0` / `cjpm 1.2.0` 在 x86_64 Linux 实测；项目案例来自 `mmap-cj` 真实 git 历史；Go 侧依据 `golang/go@master` 源码与官方文档。*

---

<p align="center">

[![](https://img.shields.io/badge/powered_by-dsh-4D6BFE?style=flat-square&logo=deepseek&logoColor=white)](https://github.com/deepseek-ai/deepseek-harness)

</p>
