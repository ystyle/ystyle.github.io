---
title: "【鸿蒙PC】二进制签名实战：三类签名、沙箱权限矩阵，以及一张调试证书的坑"
date: 2026-09-22T20:30:00+08:00
lastmod: 2026-09-22T20:30:00+08:00
draft: false
author: "ystyle"
summary: "鸿蒙 PC 上二进制必须合法签名才能加载运行。本文把官方给出的三类签名规则、应用拉起二进制的沙箱权限矩阵整理成表，再补上我们在 MateBook Pro（OpenHarmony-7.0.0.105）上实测出的五种组合结果——包括一张 DevEco 自动签名调试证书被内核 fs-verity 拒掉的完整证据链，以及换成自申请调试证书后立刻能跑的对照实验。"
tags: ["HarmonyOS", "OpenHarmony", "鸿蒙PC", "二进制签名", "HNP", "code_sign"]
categories: ["鸿蒙PC"]
toc: true
slug: matebookpro-binrary-debug-sign
---


## 摘要

鸿蒙 PC（2in1）和手机一样，**只允许合法签名的二进制程序加载和运行**——这是为了识别开发者身份、保障程序完整性。但对刚从 Linux 迁移过来的命令行工具来说，这条规则的具体边界并不直观：

- 交叉编译出来的 ELF 直接 `./tool` 会报什么错？错误码背后是谁在拦？
- 自签名（adhoc）和调试证书签名到底差在哪？为什么"能跑"和"能声明权限"是两件事？
- 签名成功 ≠ 能运行。我们在实测中遇到的现象是：`binary-sign-tool` 报 `write code sign data success`，但执行时 `Operation not permitted`，**内核日志里才看得到真正原因**。

本文分两部分：先把华为开发者支持给出的**官方规则**（三类签名对比、应用拉起二进制的强弱沙箱权限矩阵、调试证书签名流程）整理成可查的表；再给出我们在 HUAWEI MateBook Pro（`HAD-W24 7.0.0.105` / `OpenHarmony-7.0.0.105` / API 26 / 2in1）上的**实测结果**——五种签名组合逐一验证，并用内核 `kmsg` 日志定位到一张调试证书失败的真实原因。

一句话结论：**自签名（adhoc）能跑但不能声明权限；调试证书签名能用，但请务必用"自己申请的"那张证书——DevEco 自动签名下发的那张调试证书，在我们的设备上被内核的 PKCS7 校验拒掉了。**

---

## 1. 官方规则：三类签名

### 1.1 三种签名类型的区别

| 类型 | 证书 | 分发范围 | 可执行程序声明权限 | 典型场景 |
|---|---|---|---|---|
| **二进制证书签名** | 华为颁发的二进制证书（面向华为认证的已知开发者） | 无限制 | ✅ 支持 | 面向用户大范围分发 |
| **调试证书签名** | 华为颁发的调试证书 | 只能分发到**开发者指定的设备**（`.permission` 里的 `device-ids`）；运行时要求设备处于**开发者模式** | ✅ 支持（**共享库不支持**） | 开发者内部调试 |
| **自签名（adhoc）** | 不需要证书 | 无限制 | ❌ 不支持 | 编译后**仅在本地**加载运行 |

两条容易被忽略的细节：

1. **"调试证书签名的二进制可执行程序可以声明权限，但共享库不支持声明权限"**——如果你签的是 `.so`，权限段是无效的。
2. **自签名的二进制（adhoc）权限策略段运行过程不会生效**，也就是说：`-selfSign 1` 签出来的程序，写多少 `requestPermissions` 都没用。

> 个人开发者目前基本拿不到"二进制证书"，所以本文的实践集中在**自签名**与**调试证书签名**两条路上。

### 1.2 应用拉起二进制：强弱沙箱权限矩阵

官方的"强/弱沙箱"定义：

- **弱沙箱应用**：具备 `ohos.permission.CUSTOM_SANDBOX`
- **强沙箱应用**：不具备该权限

| 应用类型 | `ALLOW_EXTERNAL_NATIVE_CODE` | normal bin | debug bin | adhoc bin |
|---|---|---|---|---|
| 弱沙箱 | 无 | ✅ | ✅ | ✅ |
| 弱沙箱 | 有 | ✅ | ✅ | ✅ |
| 强沙箱 | 无 | ❌ | ❌ | ❌ |
| 强沙箱 | 有 | ✅ | ✅ | ❌ |

读法：**弱沙箱应用怎样都能拉起独立二进制；强沙箱应用必须申请 `ALLOW_EXTERNAL_NATIVE_CODE`，而且即便如此也拉不起 adhoc bin。**

### 1.3 官方重要说明里最该记住的一条

> 使用 DevEco Studio 的 clang 编译的二进制属于**自签名场景**，二进制类型是 `adhoc bin` 而不是 `debug bin`
> （`debug bin` 必须使用调试证书签名）。如果二进制类型是 `adhoc bin`，需要申请弱沙箱权限
> `ohos.permission.CUSTOM_SANDBOX`，该权限为 **ACL 权限**。

也就是说：**交叉编译出来的产物默认是 adhoc**。要让它变成 `debug bin`（可声明权限、受限分发），必须补一步调试证书签名。

---

## 2. 调试证书签名：完整流程

### 2.1 签名命令

```bash
./binary-sign-tool sign \
  -keyAlias "密钥别名（证书签名时必填）" \
  -signAlg "SHA256withECDSA 或 SHA384withECDSA（必填）" \
  -appCertFile "开发者申请的调试证书（必填）" \
  -inFile "待签名的二进制程序文件（必填）" \
  -keystoreFile "密钥库文件（必填）" \
  -outFile "签名后输出的二进制程序文件名（必填）" \
  -keyPwd "密钥口令（可选）" \
  -keystorePwd "密钥库口令（可选）" \
  -moduleFile "权限声明等信息（json 文件）"
```

实测可用的完整命令（鸿蒙 PC 本机，用 SDK 自带的 **aarch64 原生** `binary-sign-tool`）：

```bash
SDK=~/.local/opt/deveco_tools/sdk/default/openharmony
"$SDK/toolchains/lib/binary-sign-tool" sign \
  -keyAlias ystyle -signAlg SHA256withECDSA \
  -appCertFile  ~/Documents/通用测试证书.cer \
  -keystoreFile ~/Documents/ystyle-test.p12 \
  -keyPwd "$SIGN_PWD" -keystorePwd "$SIGN_PWD" \
  -inFile tool.unsigned -outFile tool -moduleFile module.json

chmod 755 tool     # ← 见 2.3，必须
```

签完可以用 `display-sign` 自检：

```bash
"$SDK/toolchains/lib/binary-sign-tool" display-sign -inFile tool
```

输出里会打印 `.permission` 段内容、证书链（叶子 → 中间 CA → 根 CA）与有效期。

### 2.2 权限策略段 `module.json`

```json5
{
  // 二进制需要的权限写这里；调试证书签名的二进制可以声明权限
  "requestPermissions": [
    { "name": "ohos.permission.kernel.LOAD_INDEPENDENT_LIBRARY" },
    { "name": "ohos.permission.INHERIT_PARENT_PERMISSION" },
    { "name": "ohos.permission.kernel.EXEMPT_ANONYMOUS_EXECUTABLE_MEMORY" },
    { "name": "ohos.permission.kernel.IGNORE_LIBRARY_VALIDATION" },
    { "name": "ohos.permission.kernel.ALLOW_WRITABLE_CODE_MEMORY" }
  ],
  "debug-info": {
    "device-id-type": "udid",
    // 调试证书签名的二进制为控制传播范围，必须写入运行它的设备 udid
    "device-ids": ["<你的设备 UDID>"]
  }
}
```

设备 UDID 取法：

```bash
hdc shell bm get --udid
```

> **实测确认**：`device-ids` 这一项缺失或为空时，程序会在运行时被直接拒掉，
> 日志是 `[VerityHdcStatusAndDeviceId]:[FAILED] verity deviceId for debug signer: udid not in module.json`。
> 填对了则是 `[SUCCESS] debug cert with valid udid`——**这一步过了，后面的失败就跟 UDID 无关了**。

### 2.3 签名后必须 `chmod +x`

`binary-sign-tool` 是**往预先存在的 `outFile` 里写**，文件权限位沿用旧文件。如果 `outFile` 是
`cp` 出来的（源文件本来没有执行位），签完仍然不可执行，运行时报的是 `Permission denied`
——很容易被误判成"签名没用"。

```bash
chmod 755 tool && ./tool --version
```

### 2.4 顺带一提：签名口令可能是密文

DevEco 自动签名写进 `build-profile.json5` 的 `storePassword` / `keyPassword` 并不是明文，而是一串
`00000019...` 形式的加密 blob（hvigor 的 `DecipherUtil` 加密）。它的结构是：

```
blob = [4B BE e][IV][密文][16B GCM tag]，其中 IV 长度 = len(blob) - 4 - e
根密钥 = AES-GCM( PBKDF2-SHA256(utf8(xor(fd0,fd1,fd2,component)), salt=material/ac, 10000, 16), material/ce )
口令   = AES-GCM(根密钥, blob)
```

`material/` 目录就在 p12 旁边（`fd/` 三个文件 + `ac/` 盐 + `ce/` 加密的根密钥）。
如果只是想在脚本里复用 DevEco 的签名物料，按这个流程解一下即可；不打算复用的话，直接用自己申请的
调试证书更省事。

---

## 3. 本机实测：五种组合的结果

测试对象统一是一份 `eza`（aarch64 musl 动态 ELF，PIE），设备是 HUAWEI MateBook Pro
（`HAD-W24 7.0.0.105(SP10C00E100R13P5)` / `OpenHarmony-7.0.0.105` / API 26 / 2in1），
开发者选项已开启，调试 HAP 可正常安装。文件都放在家目录（`/storage/Users/currentUser`，
注意这是 **hmdfs**）。签名工具为 SDK 自带的 aarch64 原生版（本机 JVM 起不来，
`Failed to mark memory page as executable`，官方 `hap-sign-tool.jar` 用不了）。

| # | 签名方式 | `.permission` 段 | 结果 |
|---|---|---|---|
| 1 | `-selfSign 1`（adhoc，自签名） | 无 | ✅ **可执行**（补 `chmod +x` 后） |
| 2 | 二进制证书（叶子 `…,DevID`） | 无 | ✅ **可执行** |
| 3 | 调试证书（**DevEco 自动签名**下发，叶子 `…,Development`） | 无 | ❌ `udid not in module.json` |
| 4 | 同上 + `-moduleFile`（填了本机 UDID） | 有 | ❌ `Operation not permitted`（EPERM） |
| 5 | 调试证书（**自己申请**的通用测试证书，叶子 `…,Development`） + `-moduleFile` | 有 | ✅ **可执行** |
| — | 第 4 组放到 `/data/local/tmp` | 有 | ❌ `Permission denied`（另一条原因，见 3.3） |

### 3.1 第 4 组为什么失败：应用侧日志只给了半句话

```text
I code_protect/BSS: [VerityHdcStatusAndDeviceId]:[SUCCESS] debug cert with valid udid
D code_protect/CODE_SIGN: [EnforceCodeSignForFile]:Start to enforce elf file, path = .../eza.signed
E code_protect/CODE_SIGN: [EnableCodeSignForFile]:Enable fs-verity failed, errno = <129, Key was rejected by service>
E code_protect/BSS: [BinSec][svc:certmgr][EnforceCodeSign]:enforce codeSign failed. ret: -768
```

`errno = 129` 是 `EKEYREJECTED`——"key was rejected"。**光看这里会以为是自己签名姿势不对，或者文件系统不支持。**

### 3.2 真正的答案在内核日志里

打开内核日志（`hilog -k on` + 持久化 kmsg）后再复现，`kmsg` 给出了完整链路：

```text
<1> [fs_security_verity:1549] fsverity: fsverity_ioctl_enable_code_sign begin, file:eza.signed, vn_index=1701822
<2> [hmcrypt_rnd:1169] fsverity certchain, failed to verify signature
<2> [hmcrypt_rnd:1171] fsverity certchain, FILE: , LINE: 0, FUNC: PKCS7_signatureVerify, DATA: , FLAGS: 0
<2> [fs_security_verity:932]  FS Verity: verify signature failed, err=137
<2> [fs_security_verity:1194] FS verity: error while initializing fsverity info, err=E_HM_KEYREJECTED
<2> [fs_security_verity:1572] fsverity: fsverity_ioctl_enable_code_sign failed, err=E_HM_KEYREJECTED, file:eza.signed
```

**内核在 fs-verity 的 code-sign 流程里验 PKCS7 签名链失败**（`PKCS7_signatureVerify`），
于是 `E_HM_KEYREJECTED`，`code_protect` 判定强制验签失败，`exec` 返回 EPERM。

也就是说：**这不是文件系统问题，也不是路径/权限问题，而是这张证书签出来的签名内核不认。**

### 3.3 换成"自己申请的"调试证书，立刻就能跑

同样一台机器、同一个 `module.json`、同一份 `eza`，只把证书换成**自己申请的通用测试证书**
（叶子同样是 `…,Development`，签发者同样是 Huawei CBG Developer Relations CA G2），
结果：

```console
$ ~/eza-signed --version
eza - A modern, maintained replacement for ls
v0.23.4 [-git]
```

两张证书的链结构、扩展（`keyUsage` / `extendedKeyUsage=codeSigning` / `basicConstraints` 等）
完全一致，差别只在叶子证书本身。**所以：请用自己申请的调试证书——DevEco 自动签名那张，至少在我们的设备上过不了内核这一关。**（此问题已提工单，等官方确认根因。）

### 3.4 `/data/local/tmp` 那条是另一个问题

同一份签名产物放到 `/data/local/tmp`（`/data` 是 hmfs，与家目录的 hmdfs 不同），
报的是 `Permission denied`：

```text
E code_protect/BSS: [BinSec][svc:kmgr][Read]:read failed. ret: -1, msg: Permission denied
```

文件属性是 `-rwxr-xr-x shell shell u:object_r:data_local_tmp:s0`，把目录权限从 `0771` 放宽到
`0755` 也无效——`code_protect` 的 BSS 读不了这个 SELinux label。**结论：能跑的位置是普通目录
（家目录即可），`/data/local/tmp` 反而跑不了。** 这一点和 Android/OpenHarmony 的传统印象是相反的。

---

## 4. 排查工具箱

出问题时的完整取证流程（也是给华为提工单时他们要的那套）：

```bash
hdc shell
cd data/log/hilog
hilog -w clear          # 清历史，缩小日志体积
hilog -b D              # 打开 debug 级别（否则看不到 code_protect 的判定细节）
hilog -k on             # 让 hilogd 存 kmsg —— 关键！
hilog -w start -t kmsg  # kmsg 持久化任务
hilog -w start -j 20 -f hilog_full -l 32M -n 40   # app/core 持久化任务
exit

# 复现问题……

hdc shell "hilog -w stop"
hdc shell "cd /data/log && tar -czf /data/local/tmp/hilog-export.tar.gz hilog"
hdc file recv /data/local/tmp/hilog-export.tar.gz .
```

几个实测踩到的点：

| 坑 | 说明 |
|---|---|
| `hdc file recv` 不支持整目录 | 会报 `[Fail]Error opening file`，改成设备侧 `tar` 再 recv 单文件 |
| **必须带 `hilog_dict`** | `/data/log/hilog/hilog_dict.<日期>.zip` 是解析持久化日志的字典；顺带 `.dict_info.json`、`.processmap` 一起给，否则对方解不开 |
| app/core 持久化文件是容器格式 | `hilog_full.*.gz` 解压出来不是文本，需要字典；`hilog_kmsg.*.gz` 才是纯文本 |
| 现场排查直接看缓冲区 | `hdc shell "hilog -x \| grep -E 'code_protect\|CODE_SIGN'"`，不用等持久化 |
| 导出后记得恢复 | `hilog -b I`（否则一直刷 debug 日志）、`hilog -w stop` |

---

## 5. 踩坑清单（TL;DR）

1. **签名 ≠ 能跑**：`write code sign data success` 只代表段写进去了，能不能加载由 `code_protect` + 内核判定，证据在 hilog/kmsg 里。
2. **`errno 129 / E_HM_KEYREJECTED` 别往文件系统上想**，先看 kmsg 里的 `fsverity certchain` 一行——大概率是证书链/签名问题。
3. **调试证书用自己申请的那张**；DevEco 自动签名下发的那张，实测会被内核拒。
4. **`.permission` 段（含 `device-ids`）是调试证书签名的必填项**，缺了就是 `udid not in module.json`。
5. **签名后 `chmod +x`**：工具沿用 `outFile` 的旧权限位，不会自动加执行位。
6. **adhoc 不能声明权限**：`-selfSign 1` 签出来的程序写多少权限都不生效；要权限就得走调试证书。
7. **交叉编译默认是 adhoc bin**：要在应用里被拉起，弱沙箱应用没问题，强沙箱应用需要 `ALLOW_EXTERNAL_NATIVE_CODE`（且仍不支持 adhoc）。
8. 顺带一个和签名无关但很坑的点：鸿蒙 PC 上**没有 `/bin/bash`**（bash 装在 `/data/service/hnp/bin/bash`），脚本 shebang 请写 `#!/usr/bin/env bash`，否则报 `bad interpreter`。

---

## 6. 结论与建议

| 场景 | 推荐做法 |
|---|---|
| 本机开发自用、不需要声明任何权限 | `binary-sign-tool sign -selfSign 1` + `chmod 755`，最省事 |
| 需要声明权限（JIT、继承父权限、独立加载库等） | **自己申请调试证书**签名 + `.permission` 段写设备 UDID |
| 要分发到大量设备/用户 | 需要二进制证书（面向华为认证开发者），个人开发者目前不适用 |
| 要在应用里拉起 | 注意第 1.2 节的沙箱权限矩阵；长期方案是 HNP 打包安装 |

留给后续的两个问题：

1. DevEco 自动签名下发的调试证书为什么过不了内核 `PKCS7_signatureVerify`？（已提工单）
2. `/data/local/tmp` 因为 SELinux label 不能被 `code_protect` 读取，官方推荐的"临时二进制存放位置"到底是哪？

---

## 附录：命令速查

```bash
# 取设备 UDID
hdc shell bm get --udid

# 自签名（adhoc）
binary-sign-tool sign -inFile tool -outFile tool.signed -selfSign 1
chmod 755 tool.signed

# 调试证书签名
binary-sign-tool sign -keyAlias <alias> -signAlg SHA256withECDSA \
  -appCertFile <cert.cer> -keystoreFile <key.p12> \
  -keyPwd <pwd> -keystorePwd <pwd> \
  -inFile tool -outFile tool.signed -moduleFile module.json
chmod 755 tool.signed

# 查看签名信息（权限段 + 证书链）
binary-sign-tool display-sign -inFile tool.signed

# 实时看验签判定
hdc shell "hilog -x | grep -E 'code_protect|CODE_SIGN'"

# 打开内核日志后再复现（关键证据在这里）
hdc shell "hilog -k on; hilog -w start -t kmsg"
hdc shell "hilog -t kmsg" | grep -E "fsverity|hmcrypt"
```

> 说明：本文的官方规则部分整理自华为开发者支持在工单中的回复与《调试证书签名》文档；
> 实测部分全部来自 HUAWEI MateBook Pro（`OpenHarmony-7.0.0.105`，API 26，2in1）上的真实操作，
> 日志均为原文摘录（已隐去 UDID 与口令）。
