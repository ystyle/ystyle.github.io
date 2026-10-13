---
title: "【鸿蒙PC】二进制签名入门：证书从哪来、能要什么权限、该用哪一个"
date: 2026-10-13T16:40:00+08:00
lastmod: 2026-10-13T16:40:00+08:00
draft: false
author: "ystyle"
summary: "鸿蒙 PC 上不签名的二进制根本跑不起来，但官方文档一上来就摆出三种签名，反而让人卡在第一步：我到底该用哪种？这篇把三种签名的证书来源、能声明的权限、以及在 HiShell 里跑和在自己应用里拉起两种场景下的对应关系，整理成几张能直接查的表。不涉及原理，只回答该用哪个、要做什么。"
tags: ["HarmonyOS", "OpenHarmony", "鸿蒙PC", "二进制签名", "HNP", "code_sign"]
categories: ["鸿蒙PC"]
toc: true
slug: harmonyos-pc-binary-sign-basics
---


## 摘要

鸿蒙 PC（2in1）上，**没有合法签名的二进制跑不起来**——直接 `./tool` 就是 `Permission denied`，不管你是从哪台机器交叉编译过来的。

但真去看文档，第一步就会卡住：

- 文档里有**三种**签名，名字很像，我该选哪个？
- 签名要证书，证书从哪来？要不要钱？个人能不能申请？
- 签完之后还是跑不起来，是签错了还是权限没给？
- 同样是这个二进制，我在 HiShell 里敲能跑，为什么放到我自己的应用里就拉不起来？

这篇就是回答这些的。不涉及原理（原理在[解析篇](/2026/10/13/harmonyos-pc-binary-sign-types/)），只给你能直接查的表和能直接抄的命令。

一句话结论：**自己本机用，自签名就够了；需要声明权限或在应用里被拉起，必须用自己申请的调试证书签名；要分发给别人，得是华为认证开发者拿到的二进制证书。**

---

## 1. 一张表看完三种签名

| | **自签名（adhoc）** | **调试证书签名** | **二进制证书签名** |
|---|---|---|---|
| **证书从哪来** | 不需要证书 | 华为颁发，**自己申请** | 华为颁发，面向认证开发者 |
| **门槛** | 零 | 有开发者账号即可 | 个人开发者基本拿不到 |
| **能声明权限吗** | ❌ 写了也不生效 | ✅（共享库 `.so` 除外） | ✅ |
| **能给别人用吗** | 只能自己本机用 | 只能给 `device-ids` 名单里的设备 | 随便分发 |
| **设备要开开发者模式吗** | — | **要** | 不要 |
| **典型用途** | 本机编译自己用 | 开发调试 | 正式发布 |
| **一句话** | 能跑，但没身份 | 能干活的开发凭证 | 正式身份证 |

> 三种签名签出来的文件结构其实是同一套，区别在"谁来给你作证"。想搞清楚这一点，看[解析篇](/2026/10/13/harmonyos-pc-binary-sign-types/)。

---

## 2. 证书从哪来

这是最容易绕晕的部分，因为三种签名里只有两种真的用到证书。

### 2.1 自签名：根本没有证书这回事

命令里连证书参数都不用传：

```bash
binary-sign-tool sign -inFile tool -outFile tool.signed -selfSign 1
chmod 755 tool.signed
```

工具会算一个"文件有没有被改过"的校验值写进去。**它证明的是"这个文件没被篡改"，不是"这是谁做的"。** 没有身份，自然也就没有权限可谈。

### 2.2 调试证书：华为发的，但**必须自己申请**

调试证书是华为签发的，个人开发者申请得到。但它有**两条获取路径，其中一条是坑**：

| 获取方式 | 能不能用于二进制签名 |
|---|---|
| ✅ **自己申请**的调试证书 | **能用** |
| ❌ DevEco Studio「自动签名」下发的 | **不能用** |

DevEco Studio 的自动签名看起来最省事——在 IDE 里点一下，`.p12` 和 `.cer` 就生成好了。**但用它签出来的二进制，执行时会被内核拒掉**，报的是 `Operation not permitted`，在应用日志里只能看到 `errno = 129`，真正的原因得翻内核日志才看得到。

我们用同一个文件、同一个 `module.json`、同一台设备做了对照：**唯一变量就是证书，换掉就能跑**。所以这不是姿势问题，是那张证书本身不行。完整证据链在[实战篇](/2026/09/22/matebookpro-binrary-debug-sign/)里。

> 结论记住一句话：**二进制签名一律用自己申请的调试证书，别用 IDE 自动签名给的。**

### 2.3 二进制证书：个人开发者基本拿不到

"二进制证书"是华为发给**认证开发者**的，用来做面向用户的大范围分发：不限设备、不用开发者模式。对绝大多数个人开发者来说这条路暂时走不通——官方文档里也把它标注为"面向华为认证的已知开发者"。

这也是为什么社区里的实践几乎都集中在前面两条路上。

---

## 3. 需要什么权限

这里有两层权限，**它们不是一回事，很多人会混**：

| | 谁声明 | 写在哪 | 决定什么 |
|---|---|---|---|
| **二进制自己的权限** | 二进制 | `module.json` → 签进 `.permission` 段 | 这个程序能不能用某些底层能力 |
| **应用侧的权限** | 拉起它的应用 | 应用的 `module.json` | 应用能不能拉起这个二进制 |

### 3.1 二进制自己声明权限

只有**调试证书签名**和**二进制证书签名**的产物，声明的权限才生效；**自签名（adhoc）写多少都白写**。

写法是在 `module.json` 里声明，签名时通过 `-moduleFile` 传进去：

```json5
{
  "requestPermissions": [
    { "name": "ohos.permission.kernel.LOAD_INDEPENDENT_LIBRARY" },
    { "name": "ohos.permission.INHERIT_PARENT_PERMISSION" },
    { "name": "ohos.permission.kernel.EXEMPT_ANONYMOUS_EXECUTABLE_MEMORY" },
    { "name": "ohos.permission.kernel.IGNORE_LIBRARY_VALIDATION" },
    { "name": "ohos.permission.kernel.ALLOW_WRITABLE_CODE_MEMORY" }
  ],
  "debug-info": {
    "device-id-type": "udid",
    "device-ids": ["<你的设备 UDID>"]
  }
}
```

几个常见的对应关系：

| 你想要的能力 | 对应的权限名 |
|---|---|
| 自己加载动态库 | `ohos.permission.kernel.LOAD_INDEPENDENT_LIBRARY` |
| 继承父进程权限 | `ohos.permission.INHERIT_PARENT_PERMISSION` |
| JIT / 可写可执行内存 | `ohos.permission.kernel.ALLOW_WRITABLE_CODE_MEMORY` |
| 跳过动态库校验 | `ohos.permission.kernel.IGNORE_LIBRARY_VALIDATION` |
| 匿名可执行内存 | `ohos.permission.kernel.EXEMPT_ANONYMOUS_EXECUTABLE_MEMORY` |

两点必须注意：

1. **`device-ids` 是调试证书签名的必填项**，缺了直接报 `udid not in module.json`。取 UDID：`hdc shell bm get --udid`。
2. **共享库（`.so`）不能声明权限**——这条是官方明确的。要权限就签可执行程序。

### 3.2 应用侧要开的权限

这决定"你的应用能不能把这个二进制拉起来"。规则和应用的沙箱强弱有关：

- **弱沙箱应用**：具备 `ohos.permission.CUSTOM_SANDBOX`（这是一条 **ACL 权限**）
- **强沙箱应用**：不具备该权限

具体见下一节的矩阵。

---

## 4. 场景对应：HiShell 里 vs 自己的应用里

这应该是你最关心的部分。**同一个二进制，在这两个地方的待遇完全不同。**

### 4.1 在 HiShell 里直接跑

就是连上设备、打开终端、敲 `./tool` 那种。对应关系很干脆：

| 你想要的 | 该用哪种签名 | 还要做什么 |
|---|---|---|
| 自己写的小工具，能用就行 | **自签名** | `chmod 755` |
| 要声明权限（JIT、独立加载库…） | **调试证书** | 填 `device-ids` + 开开发者模式 |
| 给别人也能跑 | **二进制证书** | 个人拿不到 |

> ⚠️ 两个高频坑：
> 1. **签完必须 `chmod +x`**。签名工具是往已有文件里写，会沿用旧权限位；`cp` 过来的文件没有执行位，签完照样 `Permission denied`，很容易误判成"签名没用"。
> 2. **别放在 `/data/local/tmp`**。这个目录因为 SELinux 标签读不了，反而跑不起来。放家目录就行。

### 4.2 在自己的应用里拉起

应用里拉起二进制，除了签名本身，还要看**应用的沙箱类型**和**有没有申请开关**：

| 应用类型 | `ALLOW_EXTERNAL_NATIVE_CODE` | normal bin | debug bin | adhoc bin |
|---|---|---|---|---|
| 弱沙箱 | 无 | ✅ | ✅ | ✅ |
| 弱沙箱 | 有 | ✅ | ✅ | ✅ |
| 强沙箱 | 无 | ❌ | ❌ | ❌ |
| 强沙箱 | 有 | ✅ | ✅ | ❌ |

读法是三句话：

1. **弱沙箱应用怎样都能拉起独立二进制。** 因为它握有 `CUSTOM_SANDBOX` 这条 ACL 权限，本身就自带"允许外部原生代码"的身份。
2. **强沙箱应用必须申请 `ALLOW_EXTERNAL_NATIVE_CODE`**，否则一律拉不起来。
3. **就算申请了，强沙箱也拉不起 adhoc bin。** 因为自签名没有身份，参与不了"这个二进制是谁给的、能不能信"的判断。

### 4.3 最关键的一条对应关系

把上面两张表连起来看，会得到一个很容易踩的结论：

> **用 DevEco Studio 的 clang 编译出来的二进制，默认就是 adhoc bin，不是 debug bin。**

所以如果你的目标是"在（强沙箱）应用里拉起自己编译的二进制"，**从编译那一刻起就已经注定失败了**——必须补一步调试证书签名，把它从 `adhoc bin` 变成 `debug bin`。

一句话对照：

| 你手上是 | 在 HiShell 里 | 在弱沙箱应用里 | 在强沙箱应用里 |
|---|---|---|---|
| `adhoc bin`（交叉编译默认） | ✅ | ✅ | ❌ |
| `debug bin`（调试证书签过） | ✅ | ✅ | ✅ |
| `normal bin`（二进制证书签过） | ✅ | ✅ | ✅ |

---

## 5. 怎么选：三步

```text
第 1 步：需要声明权限吗？或者在（强沙箱）应用里被拉起吗？
          ├─ 不需要 ──────────────→ 自签名（adhoc）
          └─ 需要 ──┐
                    ↓
第 2 步：要发给别人的设备用吗？
          ├─ 只给自己/名单上的设备 → 自己申请的调试证书
          └─ 要公开发布 ──────────→ 二进制证书（需华为认证）
```

对照成表格：

| 你的情况 | 用哪种 | 关键动作 |
|---|---|---|
| 本机自用、不要权限 | **自签名** | `-selfSign 1` + `chmod 755` |
| 要声明权限 | **调试证书** | **自己申请**的证书 + `device-ids` + 开发者模式 |
| 要在应用里被拉起 | 看第 4.2 节矩阵 | 注意交叉编译默认是 `adhoc bin` |
| 要分发给大量用户 | **二进制证书** | 需华为认证 |

---

## 6. 命令速查

```bash
# ---- 取设备 UDID（调试证书签名要用）----
hdc shell bm get --udid

# ---- 自签名（adhoc）----
binary-sign-tool sign -inFile tool -outFile tool.signed -selfSign 1
chmod 755 tool.signed

# ---- 调试证书签名 ----
binary-sign-tool sign -keyAlias <alias> -signAlg SHA256withECDSA \
  -appCertFile  <cert.cer> -keystoreFile <key.p12> \
  -keyPwd <pwd> -keystorePwd <pwd> \
  -inFile tool -outFile tool.signed -moduleFile module.json
chmod 755 tool.signed

# ---- 看看签成了什么（权限段 + 证书链）----
binary-sign-tool display-sign -inFile tool.signed

# ---- 跑不起来时看日志 ----
hdc shell "hilog -x | grep -E 'code_protect|CODE_SIGN'"
```

---

## 相关文章

- [《二进制签名实战：三类签名、沙箱权限矩阵，以及一张调试证书的坑》](/2026/09/22/matebookpro-binrary-debug-sign/)——完整的踩坑记录：五种签名组合实测、内核日志取证、为什么 IDE 自动签名的证书不能用
- [《二进制签名解析：自签名、调试证书、二进制证书到底差在哪》](/2026/10/13/harmonyos-pc-binary-sign-types/)——原理篇：从 OpenHarmony 源码看三种签名在文件结构和内核校验上的真实差异

> 说明：本文的规则部分整理自华为开发者支持与官方文档，命令均在实际设备
> （HUAWEI MateBook Pro，`OpenHarmony-7.0.0.105`，API 26，2in1）上验证过。
> 如果只想快速决定用哪种签名，看到第 5 节就够了。
