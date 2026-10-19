---
title: "【鸿蒙PC】二进制签名解析：自签名、调试证书、二进制证书到底差在哪"
date: 2026-10-13T16:30:00+08:00
lastmod: 2026-10-13T16:30:00+08:00
draft: false
author: "ystyle"
summary: "鸿蒙 PC 上不给二进制签名就跑不起来，但官方文档把「自签名 / 调试证书签名 / 二进制证书签名」并列成三张对照表之后，反而更难看清它们到底是不是三种不同的东西。本文从开源实现里读回来一份答案：三种签名共用同一个 .codesign 段、同一个 fs-verity 描述符结构，区别只在 signature 字段里填什么、以及内核对它的信任等级。权限、分发范围、设备要求上的全部差异，都是从这一个字段推出来的。"
tags: ["HarmonyOS", "OpenHarmony", "鸿蒙PC", "二进制签名", "code_sign", "fs-verity"]
categories: ["鸿蒙PC"]
toc: true
slug: harmonyos-pc-binary-sign-types
---


## 摘要

上一篇[《二进制签名实战：三类签名、沙箱权限矩阵，以及一张调试证书的坑》](/2026/09/22/matebookpro-binrary-debug-sign/)是踩坑视角：怎么签、报什么错、日志去哪看。这一篇换个角度，只回答一个问题——**这三种签名，本质上差在哪？**

官方文档把它们并列成三张表（签名类型对比、沙箱权限矩阵、调试证书签名流程），照着做没问题，但表格是**结果**，不是**原因**。它会告诉你"自签名不能声明权限"，不会告诉你为什么不能。而"为什么"这件事，答案在开源实现里躺着。

把 OpenHarmony 的 `security_code_signature`、`developtools_hapsigner` 和内核 `kernel_linux_common_modules/code_sign` 三个仓对着读完，结论比想象的干净：

> **三种签名不是三个开关，而是同一个数据结构上「signature 字段填什么」的三种取值。**

一句话结论：**三种签名共用同一个 `.codesign` 段、同一个 fs-verity 描述符、同一个 0x3 版本号，区别只在 `signature` 字段——填描述符自己的摘要就是自签名，填调试证书链签出的 PKCS7 就是调试证书签名，填二进制证书链签出的 PKCS7 就是二进制证书签名。权限、分发范围、设备要求上的所有差异，都是从这一个字段推出来的。**

> 阅读约定：文中标注 **【源码】** 的结论读自 OpenHarmony 开源仓，标注 **【官方】** 的引自华为文档与工单回复，其余是我们的解释。
> 实测环境与上篇一致：HUAWEI MateBook Pro（`OpenHarmony-7.0.0.105` / API 26 / 2in1）。
>
> 如果你还没确定自己该用哪种签名，先看这一篇：[《二进制签名入门：证书从哪来、能要什么权限、该用哪一个》](/2026/10/13/harmonyos-pc-binary-sign-basics/)。
> 本文是它的"为什么"。

---

## 1. 先看签名产物：一个三段式的 ELF

签名工具往 ELF 里加的不是一段而是最多三段。段名是源码里的常量 **【源码】**（`developtools_hapsigner/binary_sign_tool/common/include/constant.h`）：

```cpp
const std::string CODE_SIGN_SEC_NAME = ".codesign";     // 代码签名块
const std::string PROFILE_SEC_NAME   = ".profile";      // Provision Profile（p7b）
const std::string PERMISSION_SEC_NAME = ".permission"; // module.json
```

| 段 | 内容 | 由谁写入 | 对应命令行参数 |
|---|---|---|---|
| `.codesign` | fs-verity 描述符 + 签名 | 签名工具（**总是会写**） | 无（核心动作） |
| `.profile` | Provision Profile（p7b） | 签名工具 | `-profileFile` |
| `.permission` | `requestPermissions` / `debug-info.device-ids` | 签名工具 | `-moduleFile` |

`display-sign` 打印的就是这里的权限段与证书链。**三种签名的差别，全在 `.codesign` 里。**

### 1.1 `.codesign` 段长什么样

内核侧的结构注释写得很清楚 **【源码】**（`kernel_linux_common_modules/code_sign/code_sign_elf.h`）：

```text
+-------------------------------------------------+
|       |type              (4 bytes)| code signing|
|       |length            (4 bytes)| block       |
|       |offset            (4 bytes)| header      |
|       +---------------------------+-------------|
|       |type              (4 bytes)| profile     |
|       |length            (4 bytes)| block       |
|       |offset            (4 bytes)| header      |
|       +---------------------------+-------------|
| SIGN  |type              (4 bytes)| merkle      |
|       |length            (4 bytes)| tree        |
| DATA  |merkle tree data  (N bytes)| block       |
|       +---------------------------+-------------|
|       |type              (1 byte )|             |
|       |version           (1 byte )|             |
|       |hash alg          (1 byte )|             |
|       |log2blocksize     (1 byte )|             |
|       |salt size         (1 byte )|             |
|       |signature size    (4 bytes)|  code sign  |
|       |data size         (8 bytes)|  block      |
|       |root hash        (64 bytes)|             |
|       |salt             (32 bytes)|             |
|       |flags             (4 bytes)|             |
|       |reserved          (4 bytes)|             |
|       |tree offset       (8 bytes)|             |
|       |reserved        (127 bytes)|             |
|       |cs version        (1 byte )|             |
|       |signature         (N bytes)|  ← 分水岭    |
|-------+---------------------------+-------------|
|       | magic string    (16 bytes)|             |
| SIGN  | version         (4 bytes) |             |
|       | sign data size  (4 bytes) |             |
| HEAD  | sign block num  (4 bytes) |             |
|       | padding         (4 bytes) |             |
+-------+-----------------------------------------+
```

设备侧的解析结构 `ElfSignInfo` 与之一一对应 **【源码】**（`security_code_signature/utils/include/elf_code_sign_block.h`）：

| 字段 | 大小 | 含义 | 校验约束 |
|---|---|---|---|
| `type` | 4 | 数据类型 | 必须 = `0x1`（fs-verity 描述符） |
| `length` | 4 | 本块长度 | 落在合法区间 |
| `version` | 1 | fs-verity 描述符版本 | 必须 = `1` |
| `hashAlgorithm` | 1 | 哈希算法 | `1`=SHA-256，`2`=SHA-512 |
| `logBlockSize` | 1 | log₂(块大小) | 必须 = `12`（4 KiB） |
| `saltSize` | 1 | 盐长度 | ≤ 32 |
| `signSize` | 4 | **签名字段长度** | ≠ 0 |
| `dataSize` | 8 | 被签数据字节数 | — |
| `rootHash` | 64 | fs-verity Merkle 树根哈希 | — |
| `salt` | 32 | 盐 | — |
| `flags` | 4 | 见第 2.2 节 | — |
| `csVersion` | 1 | ELF 代码签名块版本 | 必须 = `0x3` |
| `signature` | N | **签名字段** | — |

### 1.2 两条对齐约束（能解释两个常见现象）

`ElfCodeSignBlock::ParseSignBlock` 里有两条硬校验 **【源码】**：

```cpp
if (secOff % PAGE_SIZE != 0) { /* codesign section offset is not aligned */ }
if (csBlockSize == 0 || csBlockSize % PAGE_SIZE != 0) { /* SECTION_SIZE */ }
if (fileSize < PAGE_SIZE) { /* file size is too small */ }
```

段的**偏移和长度都必须是 4096 的整数倍**，文件本身也不能小于 4 KiB。这两条约束顺手解释了两件事：

- 为什么 `llvm-objcopy --remove-section .codesign` 之后可以重新签——段是自包含、按页对齐的，摘掉不影响别的段；
- 为什么改完文件必须重签——`rootHash` 是整份文件的 Merkle 树根，动一个字节就全对不上。

> 顺带一条社区经验 **【源码·他人实证】**：预构建的 `.so` 从构建机复制到另一台设备后可能不被接受，即便它带着看起来完好的 `.codesign`；标准解是 `llvm-objcopy --remove-section .codesign` → 重新 `binary-sign-tool sign -selfSign 1` → 恢复权限位。参见 [build_in_harmonyos issue #3349](https://gitcode.com/OpenHarmonyPCDeveloper/build_in_harmonyos/issues/3349)。

---

## 2. 三种签名 = 同一个字段的三种填法

这是全文的核心。签名工具的 `CodeSigning::GetElfCodeSignBlock` 一共就干四件事 **【源码】**（`developtools_hapsigner/binary_sign_tool/codesigning/sign/src/code_signing.cpp`）：

```cpp
const int FLAG_SELF_SIGN = 1 << 4;

int flags = 0;
if (m_selfSign) { flags = flags | FLAG_SELF_SIGN; }

// 1) 算整份文件的 fs-verity Merkle 树，拿到 rootHash
fsVerityGenerator->GenerateFsVerityDigest(inputstream, fileSize, flags);

// 2) 填 signature 字段 —— 唯一的岔路口
if (!m_selfSign) {
    GetOwnerIdFromCert(ownerID);                            // 取叶子证书的 OU
    std::vector<int8_t> fsVerityDigest = fsVerityGenerator->GetFsVerityDigest();
    GenerateSignature(fsVerityDigest, ownerID, signature);  // 证书链签出的 PKCS7
} else {
    signature = fsVerityGenerator->GetDescriptorDigest();   // ← 描述符自己的摘要
}

// 3) 组描述符
fsdbuilder.SetFileSize(fileSize).SetHashAlgorithm(...).SetLog2BlockSize(12)
          .SetSalt(...).SetSignSize(signature.size()).SetRawRootHash(...)
          .SetFlags(flags).SetCsVersion(0x3);

// 4) 描述符 + 签名写进 .codesign
```

**第 2 步就是全部的秘密。** 自签名分支填进去的是 `GetDescriptorDigest()`——描述符**自己算自己**得到的一个摘要，不是任何第三方签出来的东西。而证书分支填进去的是用证书链对描述符做的 PKCS7 签名，且把叶子证书的 **OU（organizationalUnitName）** 作为 `ownerid` 一并塞进了 PKCS7。

"被签对象"到底是什么，内核头文件里定义得很精确 **【源码】**（`kernel_linux_5.10/include/linux/code_sign.h`）：

> The file measurement is the hash of this structure excluding the signature and with the `sig_size` field set to 0, while version is replaced by code sign version.

也就是说，两条分支签的是**同一个东西**——把 `sig_size` 归零后算出的描述符摘要。区别只在于拿它怎么办：

| | 自签名 | 证书签名 |
|---|---|---|
| 对这个摘要做什么 | **直接把它当签名字段填回去** | 请证书链对**同一个摘要**做一次 PKCS7 |
| 性质 | 自证（self-referential） | 他证（third-party attested） |

**三种签名的全部差异，就压缩在"自证"与"他证"这两个词之间。** 自证只能回答"文件还是原来那份吗"，他证才能回答"这是谁签的"。

### 2.1 两种证书签名，工具层面没有区别

源码里 `m_selfSign` 是个 `bool`，**没有第三个分支**。也就是说：

- **调试证书签名**和**二进制证书签名在签名工具眼里是同一个动作**——都是"用某张证书链 + 私钥对描述符做 PKCS7"；
- 区别不在工具，在**你递进去的是哪张证书**，以及**内核对这张证书所在的信任表怎么看**。

这一点很重要：它意味着你无法通过"换一个命令行参数"把调试签名变成正式签名，两者是同一条代码路径的两种输入。

### 2.2 `flags` 位：谁在标记身份

`flags` 字段里的位是分开的 **【源码】**：

| 位 | 名字 | 谁设置 | 含义 |
|---|---|---|---|
| `1 << 4` | `FLAG_SELF_SIGN` | 签名工具（`-selfSign 1`） | 这是自签名产物 |
| `1 << 5` | `BINARY_CERT_FLAGS` | 设备侧（`IS_LOCAL_HSP_PLUGIN`） | 原生库来自**二进制证书**签的 HSP |
| `1 << 6` | `SIDE_LOADING_FLAGS` | 设备侧（`IS_SIDE_LOADING_APP`） | 原生库来自**侧载**（调试安装）的应用 |

注意后两位在 `security_code_signature/utils/include/code_sign_block.h` 里，是**设备侧解析 HAP 内嵌原生库**时用的 **【源码】**：

```cpp
if (flag & IS_LOCAL_HSP_PLUGIN)   { arg.flags |= BINARY_CERT_FLAGS; }
if (flag & IS_SIDE_LOADING_APP)   { arg.flags |= SIDE_LOADING_FLAGS; }
```

所以对**独立 ELF 二进制**来说，签名工具只会动 bit 4；bit 5/6 是应用内嵌原生库场景下的身份标记。这个区别在排查时有用：手搓的独立二进制不该看到 bit 5/6 被置位——那说明产物是在被包进 HSP/应用之后（或由设备侧）重新打过标的。

---

## 3. 运行时谁在拦：exec → fs-verity → 信任表

签完只是把数据写进去了，能不能跑是另一回事。执行一个二进制的判定链大致是：

```text
exec()
  └─ code_protect（用户态服务，日志 TAG：CODE_SIGN / BSS）
       ├─ 调 EnforceCodeSignForFile → 解析 .codesign 段
       │    └─ 解析失败：CS_CODE_SIGN_NOT_EXISTS / CS_ERR_SECTION_OFFSET / …
       ├─ 调试证书：先查 .permission 的 device-ids（VerityHdcStatusAndDeviceId）
       └─ fsverity_ioctl_enable_code_sign(fd, arg)
            └─ 内核 fs_security_verity
                 ├─ 按 dataSize/rootHash/salt 算并比对 Merkle 树      ← 完整性
                 └─ code_sign_verify_certchain(PKCS7)                ← 来源
                      └─ hmcrypt_rnd: PKCS7_signatureVerify
```

### 3.1 内核那段的判定逻辑

`code_sign_verify_certchain` 的分支不多，但每一个都对应一条官方规则 **【源码】**（`kernel_linux_common_modules/code_sign/verify_cert_chain.c`）：

```c
pkcs7 = pkcs7_parse_message(raw_pkcs7, pkcs7_len);
if (!pkcs7->signed_infos)  goto untrusted;

/* 没有证书链 —— 走"本机代码"分支 */
if (!pkcs7->certs) { *ret = MAY_LOCAL_CODE; goto exit; }

is_dev_mode = (get_developer_mode_state() == STATE_ON);

for (sinfo = pkcs7->signed_infos; sinfo; sinfo = sinfo->next) {
    signer = sinfo->signer;
    source = find_matched_source(signer, false);        /* 先查发行信任表 */
    if (!source) {
        if (is_dev_mode) {
            source = find_matched_source(signer, true); /* 再查调试信任表 */
            if (!source) goto untrusted;
        } else {
            goto untrusted;
        }
    }
    /* 校验链深度不超过 source->max_path_depth */
}
```

三行关键结论，前两行读代码就能定，第三行最值得记住：

| 代码 | 含义 |
|---|---|
| `if (!pkcs7->certs) → MAY_LOCAL_CODE` | PKCS7 里**不含证书链**时走这里：只能靠内核 keyring 里已有的证书兜底，否则按"本机代码"处理 |
| `find_matched_source(signer, false)` 先匹配 | 发行信任表（二进制证书）始终参与匹配 |
| `if (is_dev_mode) → find_matched_source(signer, true)` | **"调试证书签名要求设备处于开发者模式"在代码里就是一个 `if`** |

第三行是这节的重点：官方文档说"运行时要求设备处于开发者模式"，读起来像一条策略约定；源码里它的实际形态是**调试信任表是否参与匹配的开关**——开发者模式一关，调试证书签的二进制就直接落到 `untrusted`。

> **一条边界说明。** 上面这些 `path_type` 是一组枚举：发行侧 `RELEASE_CODE_START(0x0) … RELEASE_CODE_END(0x5)`，
> 调试侧 `DEBUG_CODE_START(0x100) … DEBUG_CODE_END(0x106)`，另有 `MAY_LOCAL_CODE = 0x201`。
> 在 `code_sign_elf.c` 里还有一层更严的 `validate_elf_source`：它要求 `code_sign_verify_certchain`
> 返回的类型落在**调试区间内**（且不等于 `DEBUG_DEVELOPER_CODE`），否则直接 `-EKEYREJECTED`。
> 这一条与"adhoc 和二进制证书签的 ELF 在我们的设备上都能跑"并不完全吻合——可能是开源仓 `master`
> 与设备实际发行版本之间的差异，也可能实际走的是另一条校验路径。**这里只陈述观察，不下结论。**

### 3.2 验完之后：给文件贴一个身份标签

过了信任表校验，内核会给文件打上 `ownerid` **【源码】**（`code_sign_ext.h` / `verify_cert_chain.c`）：

| ownerid | 标签常量 | 判定条件 |
|---|---|---|
| `FILE_OWNERID_SYSTEM` | `SYSTEM_LIB_ID` | 系统库 |
| `FILE_OWNERID_DEBUG` | `DEBUG_LIB_ID` | `path_type` 落在 DEBUG 区间，或 ownerid == `DEBUG_LIB_ID` |
| `FILE_OWNERID_SHARED` | `SHARED_LIB_ID` | ownerid == `SHARED_LIB_ID` |
| `FILE_OWNERID_COMPAT` | `COMPAT_LIB_ID` | **ownerid 为空** |
| `FILE_OWNERID_APP` | — | 其余情况，携带证书里的 ownerid |

而 `ownerid` 的原始来源，就是第 2 节里那句 `GetOwnerIdFromCert` 取到的**叶子证书 OU** **【源码】**：

```cpp
VerifyCertOpensslUtils::GetTextFromX509Name(subject, NID_organizationalUnitName, ownerID);
```

> 从这里就能看出内核对"身份"的依赖有多深：**整条权限体系的地基是"这个文件是谁签的"**，而这个"谁"最终落在证书的一个字符串字段上。

---

## 4. 三种签名正面对照

现在可以正面回答了。左边是你能观察到的差异，右边是它在源码里的来源：

| 维度 | 自签名（adhoc） | 调试证书签名 | 二进制证书签名 |
|---|---|---|---|
| **`signature` 字段内容** | 描述符自身摘要 | 调试证书链签出的 PKCS7 | 二进制证书链签出的 PKCS7 |
| **需要证书 / 密钥库** | 否 | 是（`-appCertFile` + `-keystoreFile`） | 是（同上） |
| **`flags` bit 4** | `1` | `0` | `0` |
| **内核对它的处理** | 只有完整性校验，没有可验证的签发主体 | 调试信任表（**仅开发者模式**） | 发行信任表（始终参与） |
| **`ownerid` 归类** | 无身份 | `FILE_OWNERID_DEBUG` | `FILE_OWNERID_APP` |
| **设备绑定** | 无 | `.permission` 的 `debug-info.device-ids`（UDID） | 无 |
| **官方要求的设备状态** | 无 | **开发者模式** | 无 |
| **能否声明权限** | ❌ 不生效 | ✅（**共享库除外**） | ✅ |
| **分发范围** | 无限制（但只对本机有意义） | 仅限 `device-ids` 列出的设备 | 无限制 |
| **获取门槛** | 零成本 | 个人开发者可自行申请 | 需华为认证，个人开发者基本拿不到 |
| **典型场景** | 本机编译自用 | 开发者内部调试 | 面向用户大范围分发 |

**把这张表从上往下读一遍会发现：除了第一行，其余每一行都是第一行的推论。**

---

## 5. 三个"为什么"

### 5.1 为什么 adhoc 能跑，却不能声明权限

因为**完整性和来源是两件事**，而 adhoc 只解决了前一件。

`signature` 字段填的是描述符自身的摘要，它能证明的只有一件事：*"这份文件从签名那一刻起，一个字节都没被改过。"* 它证明不了"这是谁签的"——因为这个摘要不是任何主体签出来的，**没有一个可以为之背书的身份**。

而权限授予的对象恰恰是身份。回头看签名工具那段代码就很直白：自签名分支里**根本没有证书参与**，产出的也不是 PKCS7，只是一个自证的摘要。既然"签发者"这个信息从一开始就不存在，运行时自然也换不出任何身份——你不是"某个被信任的签发者"，只是"一个自我校验通过的 ELF 文件"。

> ⚠️ 顺带纠一个常见误解：**自签名不绑定设备。** `.codesign` 段里只有文件自身的大小、
> merkle 根哈希和摘要，**没有任何设备标识**，所以产物可以拷到别的鸿蒙 PC 上直接运行。
> 绑定设备的是**调试证书**——它走 `device-ids` 里的 UDID 白名单（见 5.2）。
> 也就是说 adhoc 的"弱"在于**没有身份**，而不是"只在这台机器上有效"。

所以 **【官方】**"自签名的二进制（adhoc）权限策略段运行过程不会生效"这句话要这么理解：**不是策略段没写进去，而是没有一个主体来认领它。** 你就算把 `-moduleFile` 传进去、`.permission` 段也确实被写进了 ELF，运行时依然不会有任何权限上身。

### 5.2 为什么调试证书要求开发者模式 + 绑定 UDID

这两条是同一个设计意图的**两道锁**：把"开发期凭证"的影响半径压到开发者自己的机器上。

- **UDID 锁**：`.permission` 里必须写明 `debug-info.device-ids`，运行前由 `VerityHdcStatusAndDeviceId` 校验。缺了就是 `[FAILED] verity deviceId for debug signer: udid not in module.json`。这一道锁管的是**哪些设备**。
- **开发者模式锁**：第 3.1 节那行 `if (is_dev_mode)`。这一道锁管的是**什么状态**——同一台列在白名单里的设备，关掉开发者模式同样跑不了。
  （另一个源码观察：内核 `code_sign_elf.c` 的 `elf_file_enable_fs_verity` 第一步就检查开发者模式，`!= STATE_ON` 直接返回 `-EINVAL`——这条路径与开发者模式是硬绑定的，不是建议。）

这是典型的**能力与约束对偶**：既然调试证书被授予了"声明权限"的能力，就必然要限制它能传播到哪里，否则调试证书就等价于正式证书了。二进制证书没有这两道锁，代价是它几乎拿不到。

### 5.3 为什么调试证书签的共享库不能声明权限

这条是 **【官方】** 明写的，但文档只给了结论、没给理由。下面这段是我们的解释，不是源码事实：

权限的主体是**进程/应用**，而不是文件。`.so` 被 `dlopen` 进某个宿主进程之后，它在内核眼里并不是一个可以独立承担权限的实体——它藉由宿主进程的身份运行。所以"给一个 `.so` 授予权限"这件事本身缺少可挂靠的授权对象。

反过来说，**可执行程序拥有自己的进程，因此拥有可被授权的身份**。这正好解释了为什么官方把这条单独拎出来强调：它不是一个容易忽略的细节，而是一条结构性限制。

---

## 6. 签名之外还有第二道门：沙箱矩阵

签名决定"这个文件的身份是否可信"，沙箱决定"这个文件能不能被某个应用拉起来"。两者是独立的两道关。

官方的强/弱沙箱定义 **【官方】**：

- **弱沙箱应用**：具备 `ohos.permission.CUSTOM_SANDBOX`
- **强沙箱应用**：不具备该权限

| 应用类型 | `ALLOW_EXTERNAL_NATIVE_CODE` | normal bin | debug bin | adhoc bin |
|---|---|---|---|---|
| 弱沙箱 | 无 | ✅ | ✅ | ✅ |
| 弱沙箱 | 有 | ✅ | ✅ | ✅ |
| 强沙箱 | 无 | ❌ | ❌ | ❌ |
| 强沙箱 | 有 | ✅ | ✅ | ❌ |

这张表要和第 2 节的结论连起来读才有意思：

- **弱沙箱应用怎样都能拉起独立二进制**——它本来就拿到了 `CUSTOM_SANDBOX`（一条 ACL 权限），等于自带"允许外部原生代码"的身份；
- **强沙箱应用必须申请 `ALLOW_EXTERNAL_NATIVE_CODE`，而且即便如此也拉不起 adhoc bin**——因为 adhoc 没有身份，无法参与"这个二进制是谁给的、能不能信"的判断。

再叠加一条 **【官方】** 重要说明：

> 使用 DevEco Studio 的 clang 编译的二进制属于**自签名场景**，二进制类型是 `adhoc bin` 而不是 `debug bin`（`debug bin` 必须使用调试证书签名）。

也就是说：**交叉编译出来的产物默认就是 adhoc**。如果你的目标是"在强沙箱应用里拉起自编译的二进制"，那么这条路从编译那一刻起就已经被堵死了——必须补一步调试证书签名，把它从 `adhoc bin` 变成 `debug bin`。

> 补充一个省事的办法 **【官方·工具链】**：ohos-sdk 的 `ld.lld` 支持 `--code-sign`，可以在链接期就把签名打好，省掉单独的 `binary-sign-tool` 步骤：
> ```bash
> clang -Wl,--code-sign my_program.c -o my_program
> llvm-readelf -S my_program      # 末尾能看到 .codesign 段
> ```
> 不过它默认没开（macOS 上 lld 是默认开的），而且链接期没有证书参与，所以产物仍然落在**自签名**路径上。

---

## 7. 和 macOS 对照一下

这套机制在设计上和 macOS 的代码签名是同构的，对照着看会快很多：

| | macOS | HarmonyOS / 鸿蒙 PC |
|---|---|---|
| 签名工具 | `codesign` | `binary-sign-tool` |
| 正式签名 | Developer ID / App Store | **二进制证书签名** |
| 开发签名 | Development 证书 | **调试证书签名** |
| 无身份签名 | Ad Hoc | **自签名（adhoc）** |
| 链接期签名 | lld / Go 链接器**默认**打 adhoc | `ld.lld --code-sign`，**需手动开启** |
| 完整性机制 | 代码目录哈希 | **fs-verity Merkle 树** |
| 校验位置 | 内核 + `amfid` | 内核 `fs_security_verity` + 用户态 `code_protect` |
| 信任判断 | 系统信任库 | 内核**证书来源信任表**（发行表 / 调试表） |

差异最大的一格是"链接期签名"：macOS 上 lld 默认就打 adhoc 签名，所以开发者几乎对签名无感；鸿蒙这边同一个能力存在但**默认关闭**，于是每个人都得显式补一步。

还有一点值得说清楚：**这套验签机制在开源仓里有完整实现，但"是否强制校验"取决于设备与发行版配置。** 在鸿蒙 PC（2in1）上它是强制的——不签名就是 `Permission denied`，没有商量余地。

---

## 8. 怎么选

| 你的情况 | 该用哪种 | 关键动作 |
|---|---|---|
| 本机自己写的小工具，不需要任何权限 | **自签名** | `-selfSign 1` + `chmod 755` |
| 需要声明权限（JIT、继承父权限、独立加载库…） | **调试证书签名** | 用**自己申请的**调试证书；`.permission` 写 UDID；开启开发者模式 |
| 要在应用里被拉起 | 看第 6 节矩阵 | 注意交叉编译产物默认是 `adhoc bin` |
| 要分发给大量用户 | **二进制证书签名** | 需华为认证，个人开发者目前不适用 |
| 只想让 `clang` 一步到位 | 链接期签名 | `-Wl,--code-sign`，产物仍是 adhoc |

三条最容易踩的：

1. **二进制签名一定要用自己申请的调试证书。** DevEco Studio 自动签名生成的那张不能用——它签出的 ELF 会在内核 `PKCS7_signatureVerify` 处被拒，详见[上一篇](/2026/09/22/matebookpro-binrary-debug-sign/)的完整证据链。
2. **`.so` 别指望声明权限**，第 5.3 节那条是结构性限制。
3. **签名 ≠ 能跑**：`write code sign data success` 只代表数据写进去了，判定发生在运行时的 `code_protect` + 内核里，证据在 `hilog` / `kmsg`。

---

## 附录：命令速查

```bash
# ---- 自签名（adhoc）----
binary-sign-tool sign -inFile tool -outFile tool.signed -selfSign 1
chmod 755 tool.signed

# ---- 调试证书签名 ----
binary-sign-tool sign -keyAlias <alias> -signAlg SHA256withECDSA \
  -appCertFile  <cert.cer> -keystoreFile <key.p12> \
  -keyPwd <pwd> -keystorePwd <pwd> \
  -inFile tool -outFile tool.signed -moduleFile module.json
chmod 755 tool.signed

# ---- 链接期自签名（省掉单独一步）----
clang -Wl,--code-sign my_program.c -o my_program

# ---- 看产物：段与签名信息 ----
llvm-readelf -S tool.signed     # 段表末尾应有 .codesign
binary-sign-tool display-sign -inFile tool.signed   # 权限段 + 证书链

# ---- 摘掉签名重签（预构建 .so 落到本机不可用时）----
llvm-objcopy --remove-section .codesign in.so out.so

# ---- 实时看验签判定 ----
hdc shell "hilog -x | grep -E 'code_protect|CODE_SIGN'"

# ---- 打开内核日志后再复现（原因证据在这里）----
hdc shell "hilog -k on; hilog -w start -t kmsg"
hdc shell "hilog -t kmsg" | grep -E "fsverity|hmcrypt"
```

---

## 参考资料

- 华为《二进制签名工具》官方文档：[developer.huawei.com/consumer/cn/doc/harmonyOS-guides/binary-sign-tool](https://developer.huawei.com/consumer/cn/doc/harmonyOS-guides/binary-sign-tool)
- OpenHarmony 代码签名部件：[security_code_signature](https://gitcode.com/openharmony/security_code_signature)
- OpenHarmony 签名工具仓（含《二进制签名工具》章节）：[developtools_hapsigner README_ZH](https://gitcode.com/openharmony/developtools_hapsigner/blob/master/README_ZH.md)
- 内核侧实现：[kernel_linux_common_modules/code_sign](https://gitcode.com/openharmony/kernel_linux_common_modules)
- 预构建 `.so` 签名被拒的社区实证：[build_in_harmonyos issue #3349](https://gitcode.com/OpenHarmonyPCDeveloper/build_in_harmonyos/issues/3349)
- 本博客踩坑视角的上一篇：[《二进制签名实战：三类签名、沙箱权限矩阵，以及一张调试证书的坑》](/2026/09/22/matebookpro-binrary-debug-sign/)

> 说明：本文标注 **【源码】** 的结论读自上述开源仓（`master` 分支），标注 **【官方】** 的引自华为开发者文档与工单回复，
> 其余为我们的解释，可能有误，欢迎指正。实测环境为 HUAWEI MateBook Pro（`OpenHarmony-7.0.0.105`，API 26，2in1）。
