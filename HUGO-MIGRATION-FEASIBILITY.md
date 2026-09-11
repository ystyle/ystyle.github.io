# Hexo 3.7 → Hugo 迁移可行性调研报告

> 调研对象：本站（`东方星痕`，Hexo 3.7.1 + hexo-theme-material-indigo 1.6.10，96 篇文章）
> 调研日期：2026-09（Hugo 最新稳定版 v0.166.0，2026-09-09 发布）
> 方法：所有关键结论均通过**读取本仓库真实源码 / 实际运行 Hugo v0.165.0 extended 构建验证**得出，而非仅凭文档推断。凡未经验证的推测均在文末「未验证」章节单列。

---

## 结论速览

| # | 议题 | 结论 | 定性 |
|---|---|---|---|
| 1 | Hugo 版 indigo 主题 | **不存在任何移植版** | 需要自己写 / 换主题 |
| 2 | Hexo→Hugo 迁移工具 | 只有 front-matter 转换器，且大多废弃 | front-matter 有现成方案；URL/锚点**需要自己写** |
| 3 | URL/permalink 保持 | **已实测 96/96 完全一致**（含 1 篇无 slug 的中文 URL 与 9 篇含大写 slug） | **有现成方案（已给出配方）** |
| 4 | 前端全文搜索 | Pagefind 官方支持中文分词（**已实测 `zh-cn` 生效**），是最优解；但**体积与现状同量级**，收益在能力而非省流量 | **有现成方案** |
| 5 | TOC | 结构可复刻，但**锚点 ID 默认全部不兼容**（811 个标题） | 需要自己写（脚本注入 `{#id}`） |
| 6 | 其他功能 | 大部分平移；gitalk 建议换 giscus | 混合 |
| 7 | 构建与部署 | 收益明确，单一二进制 + 实测 0.3s 构建 | **有现成方案** |

---

## 1. Hugo 移植版 indigo 主题 —— **不存在**

### 结论
GitHub 上**没有任何 `hexo-theme-material-indigo` 的 Hugo 移植**。搜索到的同名 / 近名仓库全部是「同名不同设计」，必须避免误认。

### 排查证据（逐条可复核）

| 仓库 | 实际情况 | 是否移植版 |
|---|---|---|
| [yscoder/hexo-theme-indigo](https://github.com/yscoder/hexo-theme-indigo) | 原主题。**2802★ / 525 fork，最后 push 2022-03-08**（已停更 4 年+） | 原版（Hexo） |
| [AngeloStavrow/indigo](https://github.com/AngeloStavrow/indigo) | 57★，2022-10-27 最后 push。README 自述："a lightweight, responsive, **typography-first** theme for Hugo, marked up with **microformats2** for **IndieWeb** goodness, including IndieAuth" | ❌ **只是名字都叫 indigo（颜色名）**，设计毫无关系 |
| [blogless/polymer-indigo](https://github.com/blogless/polymer-indigo) | ⚠️ **陷阱仓库**。它只是 [pdevty/polymer](https://github.com/pdevty/polymer) 的 fork，GitHub API `compare` 显示 **ahead_by = 0 / total_commits = 0（与原仓库逐字节相同）**，唯一 commit 是 pdevty 2015-06-30 的 "initial commit"。仓库简介里写的 "combined with hexo-theme-indigo" 与代码无关 | ❌ **不是移植版**，描述误导 |
| [TGNYC/indigo](https://github.com/TGNYC/indigo)、[j-wang/indigo](https://github.com/j-wang/indigo) | 均为 AngeloStavrow/indigo 的 fork（0★） | ❌ |
| [wearewebera/indigo-theme](https://github.com/wearewebera/indigo-theme)、[lorainemg/hugo-theme-indigo-night](https://github.com/lorainemg/hugo-theme-indigo-night) | `topic:hugo-theme` 下仅有的两个含 "indigo" 的仓库，0★，2025/2026 新建，均为个人作品 | ❌ |
| [yscoder/vuepress-theme-indigo](https://github.com/yscoder/vuepress-theme-indigo) | **原作者本人**把主题移植到了 VuePress（88★），**但从未移植到 Hugo** | 参考信息 |

补充证据：
- GitHub 搜索 `hugo port of hexo` 仅 4 个结果 —— [digitalcraftsman/hugo-icarus-theme](https://github.com/digitalcraftsman/hugo-icarus-theme)（205★）、`iahsanujunda/hugo-theme-cactus`、`beyondgrayzone/nopal`、`xun404/hugo-theme-journal`，**没有 indigo**。
- 搜索 `material-indigo`（19 个结果）无一为 Hugo 主题。
- 逐字节抓取 `themes.gohugo.io` 首页（389 KB）后 grep `indigo`，**0 次命中**（该页主题列表为 JS 渲染，故仅作旁证）。

### 对你的影响
**"找一个 Hugo 版 indigo，改改配置就上线"这条路不存在。** 只剩三个选项：
1. **自己移植主题**（EJS→Go template + Less/Stylus→CSS，工作量最大，但能 100% 保留视觉）
2. **换一个 Material Design 风格的 Hugo 主题**（如 [fauzanmy/pehtheme-hugo](https://github.com/fauzanmy/pehtheme-hugo) 125★ MD3 风、[digitalcraftsman/hugo-material-docs](https://github.com/digitalcraftsman/hugo-material-docs) 699★，但后者是文档站主题且 2021 年停更）
3. **自写轻量主题**（96 篇文章规模下，功能面其实不大）

> **定性：需要自己写。这是整个迁移中最大的一块工作量，且不是"配置"问题。**

---

## 2. Hexo → Hugo 迁移工具 —— **front-matter 有工具，URL/锚点没有任何工具覆盖**

### 现存的工具（全部实测核查）

| 工具 | 语言 | ★ | 最近更新 | 能力边界 |
|---|---|---|---|---|
| [pplmx/h2h](https://github.com/pplmx/h2h) | Go | 3 | **2026-09-08（活跃）** | 仅 front-matter 双向转换（hexo2hugo / hugo2hexo，yaml/toml）。Apache-2.0。`h2h --src ... --dst ...` |
| [gucheen/HexoConvertToHugo](https://github.com/gucheen/HexoConvertToHugo) | Python | 0 | **2016-03-29（仅 1 次提交，已死）** | 仅 front-matter；改写自 coderzh/ConvertToHugo |
| [aimer1124/python-format-md](https://github.com/aimer1124/python-format-md) | Python | — | 早期 | 仅 front-matter 头部格式调整 |

- **npm / PyPI 上不存在** `hexo-to-hugo`、`hexo2hugo`、`hugo-import` 包（已查 registry，均 404）。
- 官方 Hexo 的 `hexo-migrator-*` 系列全部是**导入进 Hexo** 用的，方向相反，无用。

### 已知坑（结合本站实际情况）

1. **permalink 完全不处理**：所有工具都只动 front matter 字段名，**没有一个会把 Hexo 的 `permalink:` 映射成 Hugo 的 `slug:`** —— 而本站 95/96 篇文章靠这个字段决定 URL。这是必须自己写的部分。
2. **`tags` 数组形态差异**：Hexo 支持 `tags:\n  - a\n  - b` 与 `tags: [a, b]`，也支持字符串；Hugo 亦兼容，但 Hexo 老站常见 `categories: 系统`（标量）需确认。
3. **`date` 格式**：本站混用 `date: 2015-10-20 15:47:13`（裸 YAML 时间戳）与 `date: '2017-01-06 19:36:34'`（带引号）。Hugo 两种都能解析，且**日历日期不会因时区而漂移**（见第 3 节实测）。
4. **Hexo 私有字段污染**：本站 front matter 里有 `id: 44`、`hero: {...}`、`subtitle:` 等 Hexo/主题私有字段，Hugo 会当成 `.Params` 原样保留（无害，但模板里要留意）。
5. **中文文件名**：本站 **91/96 篇文章文件名含中文**，仅 5 篇纯 ASCII。若启用 `enableGitInfo`，Hugo 在非 ASCII 文件名上取 git 信息会失败，[peaceiris/actions-hugo README](https://github.com/peaceiris/actions-hugo) 明确给出解法：CI 里加 `git config core.quotePath false`。

### 实际工作量
front-matter 转换本身**约 30 行 Python 即可完成**（本次调研已写出并跑通，96 篇全部转换成功）。**真正的成本在 URL 映射与锚点 ID 修复，而这两块没有任何现成工具。**

> **定性：front-matter 转换 = 有现成方案（但工具不成熟，建议自写 30 行）；URL/锚点 = 需要自己写。**

---

## 3. URL / permalink 保持 —— ✅ **已实测 96/96 完全一致**

这是本次调研最硬的结论：我在本机用 **Hugo v0.165.0+extended** 实际转换并构建了全部 96 篇文章，与 `public/` 里 Hexo 已生成的 URL 逐条比对，**96 条全部命中，0 缺失、0 新增**。

### 3.1 先搞清 Hexo 的 URL 到底怎么算出来的

读源码（`node_modules/hexo/lib/plugins/processor/post.js:125-127`）：

```js
if (data.permalink) {
  data.slug = data.permalink;   // ← front-matter 的 permalink 变成了 slug
  delete data.permalink;
}
```

再看 `node_modules/hexo/lib/plugins/filter/post_permalink.js`：

```js
const meta = {
  title: data.slug,                              // ← :title 令牌取的是 slug
  post_title: util.slugize(data.title, {transform: 1}),
  year: data.date.format('YYYY'), ...
};
return permalink.stringify(_.defaults(meta, config.permalink_defaults));
```

**所以本站的 URL 规则实际是：`permalink: chronomem-oom-hunt` 替换掉配置里 `:year/:month/:day/:title/` 的 `:title` 位置。**

> 这跟 Hugo 的语义**天然一一对应**：Hugo 的 `:slug` 令牌 = front matter `slug`，缺省回落到 `title`。

### 3.2 实测通过的标准配方

**`hugo.toml`：**
```toml
baseURL = "https://ystyle.top/"
timeZone = "Asia/Shanghai"

# 【最关键的一行】否则含大写的 slug 会被 Hugo 强制小写化，9 篇文章 URL 直接改变
disablePathToLower = true

[permalinks]
  [permalinks.page]
    posts = '/:year/:month/:day/:slug/'
```

**front matter 改写：`permalink: X` → `slug: X`**（其余字段不变）

**关于 `[permalinks]` 的三种写法（实测对比）：**

| 写法 | 结果 |
|---|---|
| `[permalinks]`<br>`  posts = "/:year/:month/:day/:slug/"` | ✅ 可用（旧式、最简洁） |
| `[permalinks]`<br>`  [permalinks.page]`<br>`    posts = "/:year/:month/:day/:slug/"` | ✅ 可用（官方文档现推荐，按 kind 分组，更明确） |
| `[[permalinks]]`<br>`  pattern = "/:year/:month/:day/:slug/"` | ⚠️ **危险**：无 `target` 时**匹配所有页面**，实测会连 section/分类/标签页一起改写成日期路径（产出 `/2026/index.html`、`/2026/09/09/T/index.html` 等），**不要这样写** |

推荐用第二种；若要跨 section 统一规则，用数组写法但**必须加 `[permalinks.target]`**。

**验证结果：**
```
Hexo post URLs: 96
Hugo post URLs: 96
### 缺失（Hexo 有、Hugo 无）: 0
### 新增（Hugo 有、Hexo 无）: 0
匹配: 96 / 96
```

### 3.3 两个必须知道的坑（均已实测复现）

**坑 A：Hugo 默认会把 slug 小写化 —— 本站 9 篇文章受影响**

Hugo 默认 `disablePathToLower = false`。实测：

| front matter | Hexo 产出 | Hugo 默认产出 |
|---|---|---|
| `slug: Use-dat-instead-of-resilio-sync-to-share-data` | `/2018/12/03/Use-dat-.../` | `/2018/12/03/use-dat-.../` ❌ |
| `slug: Paranoia` | `/2017/04/07/Paranoia/` | `/2017/04/07/paranoia/` ❌ |

受影响的 9 篇（从 `public/` 实测得出）：
```
/2018/12/03/Use-dat-instead-of-resilio-sync-to-share-data
/2018/11/01/Windows-10-open-with-wsl-Archlinux
/2018/05/11/Lets-Encrypt-convert-to-pkcs1
/2018/01/23/Win10-auto-start-hyper-v-version-of-Docker
/2015/10/20/Docker-搭建redis-集群
/2020/11/07/porting-Lua-to-openharmony
/2017/09/27/use-docker-to-build-ELKStack
/2017/04/07/leanote-Add-the-search-function
/2017/04/07/Paranoia
```
加上 `disablePathToLower = true` 后**全部还原**（实测确认）。

**坑 B：唯一一篇没有 `permalink` 的文章也能自动对上**

`source/_posts/Docker-搭建redis-集群.md`（front matter 无 `permalink`）：
- Hexo：`/2015/10/20/Docker-搭建redis-集群/`（`slugize` 不做大小写变换）
- Hugo（`disablePathToLower = true`，无 `slug`，从 title `Docker 搭建redis 集群` 推导）：`/2015/10/20/Docker-搭建redis-集群/` ✅ **完全一致**

> 这是个巧合但很关键的巧合：`disablePathToLower = true` 同时修好了坑 A 和坑 B。

**备用方案**：Hugo 的 `url:` front matter 会**整段覆盖**且**完全保留大小写**（实测 `/2015/10/20/Docker-搭建redis-集群/` 原样输出），可以用于任何个别对不上的文章，比 `slug` 更保险（但可读性差）。

### 3.4 中文标题的 slug 处理：两者**行为一致，都不转拼音**

实测 Hexo（直接调用本站安装的 `hexo-util@0.6.3`）：

```
"安装flutter"        -> "安装flutter"
"Docker 搭建redis 集群" -> "Docker-搭建redis-集群"
"Windows 右键菜单设置"  -> "Windows-右键菜单设置"
"Émilie 测试"         -> "Emilie-测试"     ← 只有拉丁变音符被归一化
```

原因在 `hexo-util/lib/escape_diacritic.js`：它只对 `\u0000-\u007E` 之外的字符查一张**拉丁字母变音表**，查不到就 `|| a` 原样返回 —— 中日韩字符不在表里，**原样保留**。

Hugo 的 `urlize` 同样保留 CJK（URL 里以百分号编码呈现）。

> **结论：Hexo 和 Hugo 都不做中文→拼音转写。** 本站 URL 里那些拼音 slug（`spagobi-5-2-zhong-wen-yi-hua-bu-ding-bao` 等）**全部是人工写在 front matter `permalink` 里的**，不是工具生成的。迁移后这些手写值原样搬到 `slug` 即可，不存在"中文标题处理差异"问题。
>
> ⚠️ 注意：`hexo-generator-feed` / `hexo-generator-sitemap` 等插件不会改 URL；但**如果你曾用过 `abbrlink` 插件**（本站未使用），那才需要单独处理。

### 3.5 关于 `timeZone` 的一个反直觉实测结论

本站有 **15 篇文章的发布时间在 00:00–07:59（CST）**，理论上若把裸时间戳当 UTC 解析，日期会回退一天、URL 随之改变。

实测（在 `TZ=UTC` 下模拟 GitHub Actions runner，对比有/无 `timeZone`）：

| 配置 | 匹配率 |
|---|---|
| `timeZone = "Asia/Shanghai"` | 96/96 |
| 不设 `timeZone` | 96/96 |

进一步用合成用例（`date: 2016-01-02 03:00:00`，`TZ=UTC` 构建）验证：
```
有 timeZone:  2016-01-02 03:00:00 +0800 CST | /2016/01/02/early-post/
无 timeZone:  2016-01-02 03:00:00 +0000 UTC | /2016/01/02/early-post/
```

> **即：Hugo 把裸 YAML 时间戳当作"墙钟时间"，`:year/:month/:day` 令牌取的是字面日历分量，不会因时区而漂移。`
> `timeZone` 对 **URL 保持不是必需的**，但对日期显示、`.PublishDate` 比较、RSS `pubDate` 是正确的 —— 建议仍然设置以与 Hexo 的 `timezone: Asia/Shanghai` 对齐。

> **定性：URL 保持 = 有现成方案，且已在本仓库实测 96/96 通过。**

---

## 4. 前端全文搜索

### 4.1 现状基线（实测）

- `public/content.json` = **357,447 B（349 KB）**原始（`hexo-generator-json-content@3.0.1` 产出，96 篇正文全文）
  → **gzip -9 = 131,572 B（128.5 KB / 压缩比 36.8%）**；**brotli -q11 = 108,196 B（105.7 KB / 30.3%）**
  （纯正文 title+tags+text 去掉 JSON 结构后 = 296,733 B → gzip 123,064 B）
  > ⚠️ 这个压缩后数字是后续选型的关键：**Fuse.js / 自写方案的真实传输量只有 105–130 KB，96 篇规模完全可接受**。真正的问题不是体积，而是**匹配质量**。
- 主题 `themes/indigo/source/js/search.js`（141 行）的核心匹配逻辑：

```js
var regExp = new RegExp(key.replace(/[ ]/g, '|'), 'gmi');   // 空格→OR，子串匹配
function matcher(post, regExp) {
  return regtest(post.title, regExp)
      || post.tags.some(t => regtest(t.name, regExp))
      || regtest(post.text, regExp);
}
```

> 关键洞察：**当前搜索是"纯子串匹配、零分词"**。正因如此它对中文天然可用。这既是它的优点（简单可靠），也是它的天花板（无相关性排序、无拼写容错、每次全量下载 352 KB）。

### 4.2 方案对比

> ⚠️ **重要更正**：本节表格的初版把 Pagefind 的体积写成"明显小于 352 KB 全量"，**这是错的**。实测本站 `content.json` 的压缩后体积：**357,447 B 原始 → gzip -9 = 131,572 B (128.5 KB) → brotli -q11 = 108,196 B (105.7 KB)**。而 Pagefind 首次搜索实载约 **130–290 KB**。**两者是同一量级，Pagefind 并不省流量。**
> **Pagefind 的真实收益是能力升级**（真正的中文分词、相关性排序、拼写容错、按需分片、sub-results 锚点定位），**不是带宽**。请勿以"省流量"作为选型理由。

| 方案 | 需要 Node 构建步骤 | 索引体积特征 | **中文分词** | GitHub Actions 集成 | 外部服务 |
|---|---|---|---|---|---|
| **Pagefind** | ⚠️ **非必须**：`npx` / `pip install 'pagefind[extended]'` / 预编译二进制 / `cargo install` 四选一 | `.pf_index` 分片**落盘即 gzip**（实测文件头 `1f 8b 08 00`）；zh-cn 10 片合计 277 KB；首次搜索实载 ≈130–290 KB（含 68 KB WASM + 45.5 KB js）；整目录 1.31 MB（含 3 套 UI） | ✅ **官方支持**（charabia → jieba-rs）；**必须给 `<html>` 加 `lang`**，否则静默不切分 | 最简单（`hugo` 后加 1 个 step） | ❌ |
| **Hugo 原生 `outputs: JSON` + 自写 JS** | ❌ 不需要 | = 全文 JSON：**357 KB 原始 / 128.5 KB gzip / 105.7 KB brotli**（本站实测） | ✅ 自己控制，可原样做子串匹配 → **与现状 100% 等价** | 最简单 | ❌ |
| **lunr.js + lunr-languages** | ✅ 需要 | 中（倒排索引 + 文档存储） | ✅ **官方已有 `lunr.zh.js`**（实测 HTTP 200；v1.21.0 / **2026-08-09**，活跃）：浏览器用 `Intl.Segmenter` + CJK bigram，Node 下自动用 `@node-rs/jieba`。⚠️ **无 `Intl.Segmenter` 的浏览器无 fallback**；lunr 内核停在 **2.3.9 / 2020-08-19**（但 README **无**"停止维护"声明，勿写成"已进入维护模式"） | 中 | ❌ |
| **Fuse.js** | 可选 | = 整个 JSON 体积（同上）；`Fuse.createIndex()` **只省 CPU 不省体积** | ⚠️ 默认把连续 CJK 当**一个 token**，官方明确要求 CJK 传 `Intl.Segmenter` 自定义 tokenizer；有 **32 字符 pattern 上限**；`threshold` 默认 0.6 | 简单 | ❌ |
| **FlexSearch** | 可选 | 小（bundle ≈16 KB gzip），另加自建索引 | ✅ **官方 `Charset.CJK`** + "CJK Word Break" 专章 | 中（索引导出/加载全自己写） | ❌ |
| **Orama（自托管）** | 可选 | 小，可导出索引 | ⚠️ `@orama/tokenizers/mandarin` 官方标注 **experimental** | 中 | ❌ |
| **Algolia DocSearch** | ❌（爬虫） | 托管 | ✅ | 中（需申请 + 域名验证） | ✅ **技术博客可免费申请** |
| **Meilisearch / Typesense 等** | ❌ | 托管 | ✅ | 中 | ✅ **Meilisearch 无免费档**（仅 14 天试用，usage-based $30/mo 起）；Typesense 免费额度未验证 |
| [hugo-lunr](https://www.npmjs.com/package/hugo-lunr) / [hugo-lunr-zh](https://www.npmjs.com/package/hugo-lunr-zh) / `hugo-search-index` | ✅ 需要 | 中 | hugo-lunr-zh 用 **nodejieba**（native 编译风险） | 中 | ❌ **三者均已停更**（2016 / 2018 / 2019） |
| [hugo-search-fast](https://github.com/tangf-ai/hugo-search-fast) | — | — | — | **不可用** | ✅ 必须自备服务器（Go + Sonic + Gin） |

### 4.3 Pagefind（推荐）—— 官方文档原文

Pagefind 官方 [Multilingual search](https://pagefind.app/docs/multilingual/) 文档定义了 "Specialized languages"：

> "This section currently applies to **Chinese, Japanese, and Korean** languages. Specialized languages are only supported in Pagefind's **extended release**, which is the default when running `npx pagefind`."
>
> "Currently when indexing, Pagefind does not support stemming for specialized languages, but **does support segmentation for words not separated by whitespace**."
>
> "In practice, this means that on a page tagged as a `zh-` language, `每個月都` will be indexed as the words `每個`, `月`, and `都`."
>
> "searching for `每個`, `月`, or `都` individually will work. Searching `每個月都` will segment the query into words and return results containing each word. Additionally, searching `每個 月 都` will return results containing each word in any order, and searching `"每個 月 都"` in quotes will match `每個月都` exactly."

配合 `lang="zh-cn"`，Pagefind 会自动只索引中文页面。

#### ⚠️ 实测发现（重要）：Pagefind 依赖 `lang` 属性，否则静默退化为"无分词"

我用 **Pagefind 1.5.2 在本地对本站真实的 364 个页面**跑了两轮索引，结果如下：

| 场景 | Pagefind 日志 | 索引词数 | 体积 |
|---|---|---|---|
| **无 `lang` 属性**（本站现状） | `Discovered 1 language: unknown` | 13,626 words | 2.5 MB |
| **注入 `<html lang="zh-cn">`** | `Discovered 1 language: zh-cn`<br>`Note: Pagefind doesn't support stemming for the language zh-cn.` | **8,781 words** | 2.4 MB |

三个结论：
1. ✅ **`zh-cn`（简体中文）被 Pagefind 正确识别**，并**确实启用了 CJK 分词**（词数从 13,626 变为 8,781，且出现了 zh-cn 专属的 stemming 提示）—— 这**证实了官方文档的说法，并消除了"文档只举繁体例子、简体是否适用"的疑问**。
2. ⚠️ **但这个能力是"看 `lang` 属性下菜碟"的**：没有 `lang` 就退化成 `unknown`，**静默不做中文分词**，你不会收到任何报错。
3. ⚠️ **本站当前生成的是裸 `<html>`，完全没有 `lang` 属性**（实测 `grep -o '<html[^>]*>'` 输出就是 `<html>`；主题 `head.ejs` 里也搜不到 `<html`）—— 这既是一个现存的可访问性/SEO 缺陷，也是迁移到 Pagefind 时**必须一并修掉**的前提。

→ **Hugo 侧必须确保模板输出 `<html lang="{{ site.Language.LanguageCode }}">`，并在 `hugo.toml` 里正确设置 `languageCode = 'zh-cn'`。**

#### 分词机制的硬证据（解剖索引内部）

上述"词数变化"只是间接证据。进一步把 `.pf_index` 分片解压后直接看词条形态，证据更直接：

- `.pf_index` **落盘即 gzip**（实测文件头 `1f 8b 08 00`）—— 这也印证了官方"Pagefind handles compression of the files in the bundle directly"。
- **无 `lang`（unknown）**：解压 733,794 B，中文词条是**超长未切分的连续字串** —— `阿波罗是携程框架`、`阿里妈妈前端团队`、`安全性和性能兼顾`。12,441 次出现 / 8,501 个去重。
- **`lang="zh-CN"`**：解压 585,621 B，中文词条是**真正的 jieba 词** —— `阿波罗`、`阿里云网盘`、`安装`、`安装方法`、`安全`、`按钮`。3,003 次出现 / 2,910 个去重。

→ 直接证明：**（a）简体中文确实走 jieba 分词；（b）没有 `lang` 时 Pagefind 不切分，只是把连续汉字当成超长 token**。附带一个有用的观察：**分词后索引反而更小**（解压 585 KB vs 733 KB）。

**分词器溯源**（纠正一个流传很广的说法）：准确链路是 **Pagefind → `charabia` → `jieba-rs`**，而不是常说的"Pagefind 直接用 jieba"。Pagefind 主仓库 `pagefind/Cargo.toml` 中 `charabia` 开启了 `features = ["chinese","japanese","thai"]`，且 `extended = ["dep:charabia"]` —— **中日支持就是 extended 版的唯一区别**；`charabia` 的 `chinese-segmentation` feature 才引入 `jieba-rs`。同一份 Cargo.toml 里 `pagefind_stem` 的语言清单**不含 chinese**，这正是"中文无词干"的根因。

#### 体积口径（避免误读）

- 整目录 `pagefind/` 实测 unknown 1,311,121 B / zh-cn 1,328,847 B，**但该数字含 3 套 UI**（`pagefind-ui.js` 120 KB、`pagefind-component-ui.js` 175 KB、`pagefind-modular-ui.js` 15 KB）+ 2 套 CSS + highlight + worker，**前端永远只用到其中一小部分**。
- **首次搜索实际加载**：`pagefind.js` 45,555 B + WASM 68,024 B + `pagefind-entry.json` + 1~3 个分片（zh-cn 13,434–34,114 B）≈ **130–290 KB**。
- 索引耗时：365 个 HTML → 索引 364 页（`404.html` 因无 `<html>` 被跳过，Pagefind 会明确提示）；unknown **0.353 s**，zh-cn **1.528 s**。

> 说明：我还尝试用 Pagefind 的 Node API 跑真实中文查询做端到端演示，但沙箱阻止了 Node 进程访问本地 HTTP 服务（`curl` 可通、Node `fetch` 被拒），**故未取得查询结果截图**。但索引内部词条形态已是比"词数变化"更硬的证据。

#### 部署侧（⚠️ 三条注意，比"无额外配置"更准确）

官方 [Troubleshoot Hosting](https://pagefind.app/docs/hosting/) 说 "no hosting configuration is required"，这在 **GitHub Pages 根路径部署**下成立，但有三点必须补充：

1. **子路径部署必须显式配 `baseUrl`**。官方 [Search config](https://pagefind.app/docs/search-config/) 原文：
   > "Base URL — Defaults to `/`. **If hosting a site on a subpath, `baseUrl` can be provided, and will be appended to the front of all search result URLs.**"
   `bundlePath` 通常能从 import URL 自动探测，但 **`baseUrl` 不会自动推断**。`github.io/<repo>/` 这种项目页若不传 `baseUrl: "/<repo>"`，搜索结果链接会指向域名根、**全部 404**。
   （推荐写法：`<pagefind-config base-url="/docs/">` 或 `pagefind.options({ baseUrl })`。⚠️ 经典 `PagefindUI` 的 `baseUrl` 支持情况未能从当前文档证实。）
   > ✅ **本站是 `ystyle.top` 根路径部署，不受此条影响。**
2. **不要用 `_pagefind` 作为输出目录名**。[Pagefind 1.0 迁移文档](https://pagefind.app/docs/v1-migration/) 原文：
   > "The only breaking change in Pagefind 1.0 is that the default output location has changed from `/_pagefind/` to `/pagefind/`. **This change was made as some hosting providers won't serve directories with a leading underscore, and some tooling would also ignore the `_pagefind` directory in unexpected ways.**"
   这正是 GitHub Pages（Jekyll 默认忽略 `_` 前缀目录）的经典坑，也是网上老教程里满地 `/_pagefind/` 的由来 —— **解释了为什么社区教程互相矛盾**。用当前默认的 `pagefind/` 即可；若走 GitHub Actions artifact 发布（不经 Jekyll），本就不受影响。
3. **严格 CSP 下 WASM 需要 `script-src 'unsafe-eval'`**（GitHub Pages 默认不发 CSP，本站不受影响）。

#### ⚠️ 已知代价与索引配置

- **本地开发模式不可用**：`hugo server` 里看不到搜索，因为索引来自构建产物。官方 issue [#14 "Implement local development mode"](https://github.com/Pagefind/pagefind/issues/14)（2022-05-31 开，标签 improvement，**至今 Open**）。需 `hugo` 后手动跑一次 pagefind。
- **`data-pagefind-body` 有"全站生效"语义**（[Indexing 文档](https://pagefind.app/docs/indexing/)）：
  > "**If `data-pagefind-body` is found anywhere on your site, any pages without this attribute will not be indexed.**"
  即给文章模板加了它，首页/归档页就会**全部从搜索里消失** —— 这是最容易踩的一条。
- `data-pagefind-ignore` 默认值为 `index`（排除该元素及其子元素**但仍处理其中的 filters 与 metadata**），设为 `all` 才完全排除；`<nav>`/`<footer>`/`<script>`/`<form>` 默认自动跳过。
- 另有 `data-pagefind-weight`（0.0–10.0，二次方加权；`h1`=7.0 … `h6`=2.0，正文=1.0）与 `data-pagefind-meta`（可覆盖结果的 `title`/`image`/`url`）。

### 4.4 其他方案要点

**Fuse.js（v7）的准确画像** —— 纠正"它就是无倒排索引的模糊匹配"这一过时说法：
- 核心仍是 **Bitap 近似匹配**，且有 **32 字符 pattern 长度上限**；`threshold` 默认 **0.6**（0.0=完全匹配，1.0=匹配一切）。
- 默认 `location: 0` + `distance: 100` ⇒ 有效窗口 = `threshold × distance` = 60 字符；**必须 `ignoreLocation: true` 才全字段搜索**。
- **v7 新增 Token Search（`useTokenSearch: true`）：官方文档明写 "An inverted index is built at construction time"，IDF 用 BM25 公式**。所以"Fuse 没有倒排索引"已不准确。
- ⚠️ **中文仍是坑**：官方 "Custom Tokenizer" 一节明确点名 —— "**Word-segmenting CJK or Thai — the default keeps each script run as one token; pass a function that uses `Intl.Segmenter` to split into actual words.**" 即默认把整段连续汉字当一个 token。
- `Fuse.createIndex()` **确实存在**，但用途是**省 CPU 不是省体积**。
- **实例参考**：[PaperMod](https://github.com/adityatelange/hugo-PaperMod) 确实用 Fuse.js（`assets/js/fastsearch.js`），默认参数是 `distance: 100, threshold: 0.4, ignoreLocation: true, keys: ['title','permalink','summary','content']`。**把这套参数放到中文长文上**（本站最长单篇正文实测 **20,078 字符**）：只要任意位置有 60% 字符命中就算匹配、且单字也计 → **中文短词查询会明显偏噪**。这比"模糊匹配对中文语义有限"这种定性说法有说服力得多。
  > ⚠️ 上述噪声分析是**基于官方 threshold/ignoreLocation 语义 + PaperMod 实际默认参数的推理，不是实测数据**，报告中应作"分析"看待。

- **`hugo-theme-stack` 不用 Fuse.js**：其 `assets/ts/search.tsx` 是**自写正则子串匹配**（`item.content.matchAll(regex)` + `escapeRegExp` + 生成高亮摘要），索引来自 `layouts/page/search.json` 全量 dump。
  → **这套机制与本站现在的 Hexo `search.js` 在语义上完全等价**，可直接抄来做"零新增依赖、行为 100% 不变"的保真替代。**这是"不想改变搜索行为"时最值得参考的现成实现。**

- **[hugo-lunr-zh](https://github.com/stkevintan/hugo-lunr-zh)**（21★，最后 push **2018-09-25**；npm 2.0.0 发布于 **2018-01-12**）：构建期用 **`nodejieba`** 把中文切成空格分隔，输出 `oriTitle` + 已分词的 `title`/`content`；浏览器端还需自己注入 `lunr.zh` trimmer。native 模块 + 已停更 7 年，**思路可借鉴，不建议直接用**。
- **[hugo-lunr](https://www.npmjs.com/package/hugo-lunr)**（npm 0.0.4 / **2016-02-16**）：更古老，无中文支持。
- **`hugo-search-index`**：npm 0.5.0 / **2019-04-07**，Gulp + `search-index`，产物 `search_index.gz`，周下载量个位数 —— 已死（作者自述其博客索引 gzip 后约 600 KB，可作体积参照）。
- **`hugo-search-fuse-js`**（`kaushalmodi/hugo-search-fuse-js`）：真实的 Hugo Module，Fuse.js + mark.js 高亮，但要求主主题使用 `baseof.html` + `main`/`footer` block。
- ⚠️ **纠正两个常见误传**：
  1. [tangf-ai/hugo-search-fast](https://github.com/tangf-ai/hugo-search-fast)（109★）**不是客户端方案**，而是 Go + Sonic + Gin 的**服务端方案，需要常驻服务器，不能用于 GitHub Pages**；npm 上也不存在这个包。
  2. `hugo-search` 这个名字**未能确认存在同名仓库**，建议不要引用。
- **FlexSearch**：**有官方 CJK 支持** —— `Charset.CJK` 编码器 + 专门的 "CJK Word Break (Chinese, Japanese, Korean)" 章节，用法 `new Index({ encoder: Charset.CJK })`；npm 0.8.212 / 2025-09-06。（其 README 首页的跑分表是**自家基准**，不宜直接引用。）
- **Orama**：`@orama/orama` + `@orama/tokenizers/mandarin`，官方 README 原文 "Available tokenizers: **Chinese (Mandarin, experimental)**, Japanese (experimental), Korean (experimental)"。**标注 experimental**。
- **Algolia DocSearch**：官方 [Who can apply](https://docsearch.algolia.com/docs/who-can-apply/) 明确 "**Open for all developer documentation and technical blogs**... we are offering a free hosting version to all public online technical documentations and **technical blogs**" → **中文技术博客有资格免费申请**，代价是引入外部服务与爬虫依赖。
- **Meilisearch Cloud**：官方定价页显示**没有免费档**（仅 14 天试用），usage-based 基础档 **$30/mo** 起 → 个人博客不划算。

### 4.5 建议
**仍推荐 Pagefind**，但**选型理由应当是"能力升级 + 零外部依赖 + 与 Hugo 官方推荐一致"，而不是"省流量"**（实测两者体积同量级，见 4.2 更正）。Hugo 官方 [Search tools](https://gohugo.io/tools/search/) 页也把 Pagefind 列在开源方案首位。

- **有现成方案**：Pagefind（含中文分词，前提是加 `lang`）；Hugo 原生 `outputs: JSON` + 抄 hugo-theme-stack 的 `search.tsx`（**语义与现状 100% 等价的保真替代**）
- **需要自己写**：FlexSearch / Orama 自托管（索引生成 + 加载 + UI 全自己写）；任何想要更精准中文（同义词、词形变化互相命中）的方案 —— **Pagefind 不支持中文词干**，做不到
- **无法完全等价（重要，需向读者说明）**：Pagefind 这类倒排索引方案会**改变匹配语义**。现状 `search.js` 是"整串子串匹配"，搜 `数据库索引` 能命中正文里连续出现的那 4 个字；分词后变成"数据库"与"索引"两个词各自命中（**顺序无关、可能跨句命中**）。这是**行为变更而非纯升级** —— 搜索结果会变多，也可能出现以前搜不到的结果。反过来，现状搜不到"拼错/少字"，Pagefind 的容错与 sub-results 锚点定位是纯增益。

**构建集成**：在现有 `hugo --minify` 之后加一个 step 即可。真实中文 Hugo 博客用例（`pseudoyu/yu-blog`）：
```yaml
- run: hugo --gc --minify
- run: npm_config_yes=true npx pagefind --source "public"   # --source 是 <1.0 旧名，现名 --site
```
> ⚠️ **`npx` 不是唯一途径**：Pagefind 还支持 `pip install 'pagefind[extended]'`、**直接下载预编译二进制**、`cargo install`。`npx` 只是"下载对应平台二进制"的包装器（包用 `optionalDependencies` 拉各平台二进制，**未声明 `engines`**）—— 这意味着 **Pagefind 可以完全绕开 Node**，对"Hexo 3.x 锁 Node 12"的困境是好消息。（但 `npx` 的最低 Node 版本无法确认，勿写"只需 Node 20.x"。）

> **定性：有现成方案（Pagefind）。**
> **⚠️ 两个落地前提**：① 必须让页面输出正确的 `lang` 属性（本站现状是裸 `<html>`），否则 Pagefind **静默**不做中文分词；② 若用 GitHub 项目页子路径部署需配 `baseUrl`（本站根路径部署，不适用）。

---

## 5. TOC 差异 —— **结构可复刻，但锚点 ID 默认全线不兼容**

### 5.1 Hexo 侧的真实实现（读源码）

**`node_modules/hexo/lib/plugins/helper/toc.js`** —— 注意它解析的是**已经渲染好的 HTML**，用 cheerio 选 `h1..hN`，**直接读取标题上已有的 `id` 属性**：

```js
const headings = $(headingsSelector);
if (!headings.length) return '';          // ← 无标题时返回空串
let result = `<ol class="${className}">`;
...
result += `<li class="${className}-item ${className}-level-${level}">`;
result += `<a class="${className}-link" href="#${id}">`;
if (listNumber) result += `<span class="${className}-number">1.2.</span> `;
result += `<span class="${className}-text">${text}</span></a>`;
```

- 默认 `max_depth = 6`、`list_number = true`（**本站主题配置 `toc.list_number: true`**）
- 输出结构：`<ol class="toc">` → `<li class="toc-item toc-level-N">` → `<a class="toc-link" href="#id">` → `<span class="toc-number">` + `<span class="toc-text">`；子级用 `<ol class="toc-child">`

**`node_modules/hexo-renderer-marked/lib/renderer.js`** —— id 从哪来：

```js
Renderer.prototype.heading = function(text, level) {
  var id = anchorId(stripHTML(text));       // anchorId = util.slugize(str.trim())  ← 无 options！
  if (headingId[id]) { id += '-' + headingId[id]++; } else { headingId[id] = 1; }
  return '<h'+level+' id="'+id+'"><a href="#'+id+'" class="headerlink" ...></a>'+text+'</h'+level+'>';
};
```

注意 `slugize(str.trim())` **没传 `{transform: 1}`**，所以：**保留大小写、保留全角标点、保留中文**。重复标题加 `-1`、`-2` 后缀。

### 5.2 实测对比（Hugo v0.165.0，默认 `autoIDType = 'github'`）

| 标题 | Hexo 生成的 id | Hugo 默认生成的 id | 一致? |
|---|---|---|---|
| `鸿蒙PC融合开发引擎架构解析：虚拟机与容器双模式` | `鸿蒙PC融合开发引擎架构解析：虚拟机与容器双模式` | `鸿蒙pc融合开发引擎架构解析虚拟机与容器双模式` | ❌ |
| `Awesome Stars` | `Awesome-Stars` | `awesome-stars` | ❌ |
| `安装仓颉 SDK` | `安装仓颉-SDK` | `安装仓颉-sdk` | ❌ |
| `第二现场：256MB 的 GC 堆与 4MB 的 memtable` | `第二现场：256MB-的-GC-堆与-4MB-的-memtable` | `第二现场256mb-的-gc-堆与-4mb-的-memtable` | ❌ |
| `Windows 右键菜单设置` | `Windows-右键菜单设置` | `windows-右键菜单设置` | ❌ |
| `用docker编译方舟编译器` | `用docker编译方舟编译器` | `用docker编译方舟编译器` | ✅ |

**两条系统性差异：**
1. **Hugo 强制小写**（Hexo 保留大小写）
2. **Hugo 删除全角标点**（`：`、`，` 等被直接丢弃；Hexo 原样保留）

### 5.3 本站受影响规模（实测统计）

```
全部标题数（96 篇文章）      : 811
已有显式 {#id} 的标题        : 0
唯一 heading id 数           : 521
含大写字母的 id              : 120
含中文字符的 id              : 485
文章内 #锚点 链接            : 43
```

> **811 个标题的 id 几乎全部会变，43 处站内锚点链接会失效，所有外部深链（`#xxx`）也会失效。**

### 5.4 修复方案（已实测可行）

Hugo 的 `markup.goldmark.parser.attribute.title` **默认为 `true`**，所以标题可以写显式 id：

```markdown
## 鸿蒙PC融合开发引擎架构解析：虚拟机与容器双模式 {#鸿蒙PC融合开发引擎架构解析：虚拟机与容器双模式}
## Awesome Stars {#Awesome-Stars}
```

**实测输出：**
```html
<h2 id="鸿蒙PC融合开发引擎架构解析：虚拟机与容器双模式">
<h2 id="Awesome-Stars">
```
✅ **中文、大写、全角冒号全部原样保留。**

→ **需要写一个脚本**，用与 `hexo-util.slugize` 完全相同的算法（`escape_diacritic` + 特殊字符→`-` + 折叠 + 去首尾）给 811 个标题注入 `{#id}`。算法可以逐字照抄 `node_modules/hexo-util/lib/slugize.js`，也可以在 Node 里直接 `require('hexo-util')` 批量生成。

**其他 ID 策略不推荐：**
- `autoIDType = 'github-ascii'`：会**丢弃**非 ASCII 字符 → 中文标题的 id 会变成空串或极短串，**对中文站点更糟**
- `autoIDType = 'blackfriday'`：Blackfriday 是已废弃的旧渲染器，不建议

### 5.5 TOC 结构差异与自定义

Hugo `.TableOfContents` 实测输出：
```html
<nav id="TableOfContents">
  <ul>
    <li><a href="#一级标题-a">一级标题 A</a>
      <ul><li><a href="#二级标题-a1">二级标题 A.1</a></li></ul>
    </li>
    <li><a href="#一级标题-b">一级标题 B</a></li>
  </ul>
</nav>
```

| 维度 | Hexo `toc()` | Hugo `.TableOfContents` |
|---|---|---|
| 外层容器 | 裸 `<ol class="toc">` | `<nav id="TableOfContents">` 包裹 |
| 有序/无序 | 默认 **`<ol>`** + 数字（`list_number: true`） | 默认 `<ul>` **无数字** |
| 层级 class | ✅ `toc-item` / `toc-level-N` / `toc-child` | ❌ 无 |
| 层级范围 | `max_depth`（默认 6） | `startLevel`（默认 2）/ `endLevel`（默认 3） |

**Hugo 侧的三种做法：**

1. **配置级**：
```toml
[markup.tableOfContents]
  startLevel = 2
  endLevel   = 3
  ordered    = false
```
2. **`.Fragments.ToHTML startLevel endLevel ordered`**（实测 `ordered=true` 产出 `<ol>`），可按页面单独控制层级。
3. **完全自定义结构**（复刻 Hexo 的 class 名，从而**复用主题现有 CSS 与 scroll-spy JS**）—— 用 `.Fragments.Headings`：
```
ID | Level | Title | Headings（嵌套子级）
```
配套还有 `.Fragments.HeadingsMap`、`.Fragments.Identifiers`（扁平 id 列表）、`.Identifiers.Contains`、`.Identifiers.Count`（查重）。

> 好消息：主题的滚动高亮 JS（`themes/indigo/source/js/main.js` 里的 `Blog.toc.actived()` / `Blog.toc.fixed()`）用的是**通用选择器** `#post-toc a[href="#id"]` 和 `li.active`，**换成 Hugo 后无需改动即可工作**；只有 `.toc-number` 数字和 `.toc-level-N` 分级样式需要自定义 partial 才能保留。

### 5.6 "Hugo 是否为没有 id 的标题提供容错？"

**是的，而且比 Hexo 更健壮。** Hugo 在 `autoHeadingID = true`（默认）下**总是**为每个标题生成 id，因此 TOC 里不会出现 `href="#"`。

反过来，**Hexo 的容错更差**：`toc()` 直接读渲染结果里的 `id` 属性，如果某个渲染器不产出 id，就会生成 `href="#"` 的死链；而标题数为 0 时 `toc()` 返回空串 `''`，主题用 `if(topic)` 跳过整个侧栏。

Hugo 侧对应的守卫应改成：
```go-html-template
{{ if .Fragments.Headings }}
  <aside class="post-widget"><nav class="post-toc-wrap" id="post-toc">...</nav></aside>
{{ end }}
```

> **定性：TOC 结构 = 需要自己写（自定义 partial，可完全复刻）；锚点 id = 需要自己写脚本（811 处）；Hugo 的 id 容错 = 比 Hexo 好。**

---

## 6. 其他功能对照

### 6.0 一个非常重要的好消息：正文几乎零改动

实测扫描 96 篇文章：

```
Hexo 专有标签插件（{% asset_img %} / {% codeblock %} / {% link %} / {% raw %} / {% blockquote %} / {% note %} ...）: 0 处
<!-- more --> 摘要分隔符                                                                              : 0 处
含裸 HTML 块的文章                                                                                   : 7 篇
行内 <img> 标签                                                                                      : 1 处
```

**本站正文是"干净 Markdown"**，没有使用任何 Hexo 标签插件，也没有 `<!-- more -->`。这意味着**正文内容层几乎是零成本的**——这大幅降低了整体迁移风险。

#### ⚠️ 但要注意：摘要分隔符的写法在 Hugo 里**不能带空格**（实测）

Hugo 与 Hexo 的摘要分隔符写法**不同**，且**写错不报错**：

| 写法 | Hugo 实测结果 |
|---|---|
| `<!--more-->` | ✅ 生效（`.Truncated = true`，`.Summary` 只含分隔符之前的内容） |
| `<!--more-->` 后带空格 | ✅ 生效 |
| **`<!-- more -->`（带空格）** | ❌ **不生效**！`.Truncated = false`，`.Summary` 返回**全文** |

> **`<!-- more -->` 恰恰是 Hexo 的惯用写法。** 本站目前 0 处分隔符，所以本次迁移不受影响；但**如果你保持 Hexo 时期的手感继续写 `<!-- more -->`，摘要会静默失效**（配合 6.3 节的 `hasCJKLanguage` 问题，首页会显示全文）。建议在 Hugo 里统一用 `<!--more-->`。

### 6.1 gitalk 评论 —— 建议借迁移之机换掉

**现状（本站主题 `_partial/plugins/gitalk.ejs`）**：
```js
var id = location.pathname
if (location.pathname.length > 50) {
  id = location.pathname.replace(/\/\d+\/\d+\/\d+\//, '').replace('/', '').substring(0, 50)
}
const gitalk = new Gitalk({ clientID: ..., clientSecret: ..., repo: 'ystyle.github.io',
  owner: 'ystyle', admin: ['ystyle'], id: id, title: document.title.split('|')[0], ... })
```

- Hugo **没有任何原生 gitalk 支持**，但它是纯前端组件，**照抄脚本即可平移**（放进 `layouts/partials/`）。
- ⚠️ **评论身份绑定在 URL 上**：`id` 由 `location.pathname` 推导。**所以第 3 节把 URL 做到 96/96 一致，不只是 SEO 问题，更是"评论不丢"的前提。** 这是本次迁移里 URL 保持的第二重价值。
- ⚠️ **安全提示**：`client_secret` 明文硬编码在 `themes/indigo/_config.yml` 里（`05033003...`）。既然它是前端可见的，等于公开；建议迁移时**轮换该 secret**，或直接换掉评论系统。
- ⚠️ **gitalk 自身状况**：[gitalk/gitalk](https://github.com/gitalk/gitalk) 7.2k★ / 624 fork，**144 个 open issue、9 个 open PR**。其 README 里 `proxy` 的默认值是公共的 `https://cors-anywhere.azm.workers.dev/https://github.com/login/oauth/access_token` —— 这个公共 CORS 代理长期不稳定/限流，社区大量文章讨论 `Error: Network Error` 以及"自建 CORS-anywhere 服务"的绕法。**这是 gitalk 当前最主要的运维痛点。**

**推荐替代（giscus）**：[giscus.app](https://giscus.app/) 基于 GitHub Discussions，官方文档明确给出了从 gitalk 迁移的路径：

> "If you've previously used other systems that utilize GitHub Issues (e.g. **utterances, gitalk**), you can **convert the existing issues into discussions**. After the conversion, just make sure that the mapping between the discussion titles and the pages are correct, then giscus will automatically use the discussions."

映射方式选 `data-mapping="pathname"`（与 gitalk 的 `location.pathname` 语义一致）或 `title`。**因为本站 URL 保持 100% 不变，pathname 映射可以无缝接管。**
其他中文化更友好的选项：Waline、Twikoo、Artalk（需自部署或 Serverless）。

> **定性：gitalk 平移 = 有现成方案（照抄 JS）；但建议换 giscus = 有现成方案（含官方迁移路径）。**

### 6.2 百度统计 / 百度推送 —— 比预想简单

实测本站主题 `_partial/plugins/baidu.ejs` **全部是前端 `<script>` 片段，不是服务端 API**：

```html
<!-- 百度统计 -->
<script>var _hmt = _hmt || []</script>
<script async src="//hm.baidu.com/hm.js?<token>"></script>

<!-- 百度推送 -->
<script>
  var bp = document.createElement('script');
  bp.src = (window.location.protocol === 'https:')
    ? 'https://zz.bdstatic.com/linksubmit/push.js'
    : 'http://push.zhanzhang.baidu.com/push.js';
  ...
</script>
```

> ⚠️ 这纠正了一个常见假设：本站用的是**百度"自动推送"JS**（每次访问顺带提交 URL），**不是** `data.zz.baidu.com/urls` 那个主动推送 HTTP API，所以**不需要**写"构建后读 sitemap 批量 POST"的脚本。

**Hugo 做法**：把上述片段原样放进 `layouts/partials/baidu.html`，在 `baseof.html` 里引用，token 收到 `hugo.toml` 的 `[params]` 下。**10 分钟工作量，纯平移。**
（若将来想改用主动推送 API，则需自写构建后脚本解析 `public/sitemap.xml` 并 POST —— 目前**不需要**。）

> **定性：有现成方案（纯片段平移）。**

### 6.3 RSS —— ⚠️ 格式会变，需注意

**现状**：`public/atom.xml` 是 **Atom 1.0**（`<feed xmlns="http://www.w3.org/2005/Atom">`，由 `hexo-generator-feed@1.2.2` 生成），**实测 269,679 B（264 KB）/ 20 条 entry**。
> ⚠️ **勘误**：本节初版写成"16 KB" —— 那是 `sitemap.xml` 的体积，两者被我写反了（原因见 6.4 节勘误说明）。
> 而且它**每条 entry 内嵌完整正文 HTML**（`<content type="html">`，实测单条约 21 KB，其中正文 20,633 B）→ **264 KB 的 feed，订阅者每次抓取都要全量下载**。这本身是个值得顺便修掉的问题。

**Hugo 默认**：生成 **RSS 2.0** 格式的 **`index.xml`**（不是 `atom.xml`），并且**默认不限条数**。实测默认输出 **692,471 B（676 KB）/ 96 条 item**，`<description>` 用的是 `.Summary`。
→ 体积比现状大是因为**收了全部 96 篇**（Hexo 那份只收 20 篇）；用 `[services.rss] limit = 20` 即可对齐现状。

#### 🔴 重要发现：中文站**必须**开 `hasCJKLanguage = true`，否则 RSS 和摘要会失控

上面的 `<description>` 实测**最大 64,605 B、中位数 4,523 B，96 条里有 80 条是"全文级"长度** —— 这不是正常摘要。根因是 **Hugo 默认按空格切词统计 `.WordCount`，而中文没有空格** → 词数被严重低估 → 正文"看起来比 `summaryLength` 阈值短" → **`.Summary` 直接返回全文**。

加上 `hasCJKLanguage = true` 后（同一站点、同样 96 篇，仅此一项配置差异）：

| 配置 | `index.xml` 总大小 | `<description>` 中位数 | 全文级 desc（>2000 B）条数 |
|---|---|---|---|
| 默认（`false`） | **636,269 B（621 KB）** | 4,523 B | **80 / 96** |
| **`hasCJKLanguage = true`** | **244,202 B（238 KB）** | **791 B** | **25 / 96** |

→ **RSS 体积直接降到 38%**。更重要的是，`hasCJKLanguage` 不只影响 RSS，它还决定：
- **`.Summary`** —— 首页/列表页摘要。不开的话，首页每篇文章都会显示**几乎全文**（这会显著改变首页观感）
- **`.WordCount` / `.ReadingTime`** —— 阅读时长会算错（严重偏低）
- `.FuzzyWordCount`、相关文章（Related Content）的相似度计算

> **结论：`hasCJKLanguage = true` 是中文 Hugo 站的必填项，不是可选项。** 它应与 `languageCode`、`lang` 属性一起，作为迁移 checklist 的第一批配置项。
> （这也解释了为什么很多中文 Hugo 博客的首页摘要"看起来就是全文"。）

**Hugo 的做法**（[RSS templates 文档](https://gohugo.io/templates/rss/)、[Output Formats](https://gohugo.io/configuration/output-formats/)）：
- 默认已开启，为 home / section / taxonomy / term 各生成 feed，用 `[outputs]` 可逐 kind 控制
- 条数限制：`[services.rss] limit = -1`（-1 = 不限）
- 覆盖模板：`layouts/home.rss.xml`、`layouts/_default/rss.xml` 等
- **要保住 `atom.xml` 这个 URL 和 Atom 格式**，需要自定义 output format（`mediaTypes` 里定义 `application/atom+xml`，`outputFormats` 指定 `baseName = "atom"`）+ 自写 Atom 模板

**影响评估**：主流阅读器同时吃 Atom 和 RSS 2.0，所以**格式换成 RSS 2.0 通常不影响订阅者**；但 **URL 从 `/atom.xml` 变成 `/index.xml` 会丢掉已订阅的用户**。最省事的折中是加一条 `alias` 或自定义 output format 保留 `/atom.xml`。

> **定性：RSS 本身 = 有现成方案；完全等价（保留 atom.xml 的 Atom 格式）= 需要自己写模板。**

### 6.4 sitemap —— 有现成方案

Hugo **内置且默认开启**，生成 `public/sitemap.xml`（符合 sitemap protocol v0.9）。
- 逐页覆盖：front matter `sitemap: {changefreq, priority, disable}`
- 全局：`[sitemap]` 配置项；关闭用 `disableKinds = ['sitemap']`
- 覆盖模板：`layouts/sitemap.xml`
- ⚠️ `lastmod` 的取值与 `enableGitInfo` 相关；CI 里浅克隆（未设 `fetch-depth: 0`）会导致 `.GitInfo` / `.Lastmod` 拿不到值

**现状对比（实测构建 + 逐条统计）：**

| | Hexo（现状） | Hugo（实测转换后） |
|---|---|---|
| `<loc>` 数 | **100** | **190** |
| 文件大小 | **15,580 B（16 KB）** | **14,104 B（14 KB）** |
| 收录内容 | 96 篇文章 + 4 个静态页（**未含**分类/标签/归档） | 96 篇文章 + **79 个标签页** + **13 个分类页** + home/section |

Hugo 默认把 taxonomy 页也收进 sitemap，**URL 数几乎翻倍（190 vs 100）而文件反而更小**（14 KB vs 16 KB）。

> 🐛 **勘误**：本节初版把两个文件的体积写反了（Hexo sitemap 写成 264 KB）—— 那是因为 `ls -lh a b` 按字母序输出（`atom.xml` 在前）而我丢失了文件名关联。**264 KB 其实是 `atom.xml` 的体积，不是 sitemap**。已按 `stat -c %s` 的字节数更正。

**Hexo 只收录 100 条的根因（已查明）**：读 `node_modules/hexo-generator-sitemap/lib/generator.js`，它只取 `locals.posts` + `locals.pages`：
```js
var posts = [].concat(locals.posts.toArray(), locals.pages.toArray())
  .filter(post => post.sitemap !== false && !isMatch(post.source, skipRenderList))
```
**完全不含 taxonomy（分类/标签）与归档页** —— 这是该插件的设计如此，不是配置问题。Hugo 则默认收录 taxonomy 页，**比现状更全**。

> ⚠️ 注意：Hugo **不会**自动生成 `archives/` 年月归档页（现在 Hexo 有 80 个），需要用模板自己实现 —— 若你需要保留 `/archives/`，这是额外的一点工作量。

> **定性：有现成方案（开箱即用，且覆盖更全）。**

### 6.5 图片 lightbox —— 有现成方案（render hook）

**现状**：主题 `lightbox: true`，用自写 JS（`main.js` 里的 `lightbox` 模块 + `.img-lightbox` class），**不是第三方库**。本站仅 **1 处行内 `<img>`**、79 张图片（多在 `source/images/`）。

**Hugo 的标准做法：image render hook**（[官方文档](https://gohugo.io/render-hooks/images/)），模板路径 `layouts/_markup/render-image.html`：

```go-html-template
<a href="{{ .Destination | safeURL }}" class="img-lightbox" data-lightbox="gallery">
  <img src="{{ .Destination | safeURL }}"
    {{- with .PlainText }} alt="{{ . }}"{{ end -}}
    {{- with .Title }} title="{{ . }}"{{ end -}}>
</a>
```

可用上下文：`.Destination`、`.PlainText`、`.Text`、`.Title`、`.IsBlock`、`.Ordinal`（v0.160+）、`.Position`（v0.160+）、`.Attributes`、`.Page`、`.PageInner`。

- **只需保留现有自写 JS** —— render hook 产出与主题 `.img-lightbox` 选择器匹配的 DOM，现有 lightbox JS 即可直接复用。
- 若要换成维护中的库：PhotoSwipe v5、GLightbox、Fancybox、medium-zoom 均可（v5/最新版请自行确认维护状态）。
- ⚠️ **注意 `static/` vs `assets/` 的区别**：Hugo 的**内嵌** image render hook 会按页面资源 → 全局资源顺序解析目标；全局资源必须放在 `assets/`。本站图片在 `source/images/`（对应 Hugo 的 `static/`）。若想用 Hugo 的图片处理（`Resize`/`WebP`），需把 `static` 挂载到 `assets`：
```toml
[module]
  [[module.mounts]]
    source = 'assets'
    target = 'assets'
  [[module.mounts]]
    source = 'static'
    target = 'assets'
```

> **定性：有现成方案（render hook + 复用现有 JS）。**

### 6.6 代码高亮 —— Chroma vs highlight.js

| 维度 | Hexo 3.7（现状） | Hugo（Chroma） |
|---|---|---|
| 时机 | **客户端 JS**（highlight.js） | **构建时服务端**，页面零 JS |
| 配置 | `_config.yml` 的 `highlight: {enable, line_number: true, auto_detect, tab_replace}` | `[markup.highlight]` |
| 主题样式 | 引入 highlight.js CSS | `hugo gen chromastyles --style=X > syntax.css` |
| 语言覆盖 | ~190 | ~250（Chroma，但只有 5 种支持自动检测） |

**实测 `hugo gen chromastyles --style=monokai` 正常工作，产出 3804 字节 CSS**，头部为 `/* Generated using: hugo gen chromastyles --style=monokai */`。

**Hugo 关键默认值（注意坑）：**
```toml
[markup.highlight]
  codeFences = true
  noClasses  = true      # ⚠️ 默认 true = 内联样式，不会生成 class！
  lineNos    = false     # ⚠️ 默认关，Hexo 那边 line_number 是 true
  style      = 'monokai'
  guessSyntax = false
```
→ **要复用外部 CSS，必须显式设 `noClasses = false`**；要保留行号需设 `lineNos = true`（另有 `lineNumbersInTable`、`anchorLineNos`、`lineAnchors`、`hl_Lines`、`lineNoStart`、`wrapperClass`）。

**```lang 围栏代码块原样通用**（Hexo 与 Hugo 都用标准围栏）。本站**未使用 `{% codeblock %}` 等 Hexo 专有标签**（实测 0 处），所以**代码块零改写**。

> **定性：有现成方案。服务端高亮还顺带减少了前端 JS 体积。**

### 6.7 微信二维码分享 —— 纯前端，原样平移

**现状**（`_partial/post/share.ejs`）：
```ejs
<img src="<%- 'qrcode' in locals ? qrcode(sUrl) : '//api.qrserver.com/v1/create-qr-code/?data=' + sUrl %>">
```
用 `hexo-helper-qrcode` 生成，回退到外部 API `api.qrserver.com`。同时分享栏还有 微博/QQ/Facebook/Twitter/**Google+**。

**Hugo 做法**：纯前端逻辑，**与静态生成器无关，原样搬到 partial 即可**。二维码可用 `qrcodejs` / `node-qrcode` / `qrcode-generator` 在浏览器端生成（推荐，避免依赖外部 API）。

**注意事项**：
- 微信内置浏览器无法调起系统分享，所以"显示二维码让用户长按/截图分享"是标准变通做法 —— 逻辑不变。
- **微信 JS-SDK（`wx.config` + `jsApiList`）需要服务端签名**（`jsapi_ticket` 换取 signature），**纯静态站点无法使用**。本站现在也没用它，所以无影响。
- 建议顺手清理：**Google+ 已于 2019 年关停**；`http://service.weibo.com/...` 等 `http://` 链接在 HTTPS 站上会被浏览器拦截（混合内容）。

> **定性：有现成方案（纯前端平移），顺手清理死链。**

### 6.8 汇总表

| 功能 | 定性 | 说明 |
|---|---|---|
| 正文 Markdown | ✅ **零成本** | 无 Hexo 专有标签、无 `<!-- more -->` |
| 裸 HTML | ⚠️ 需一行配置 | 默认 `unsafe=false` 会丢弃（**实测 7/96 篇受影响**，见下） |
| gitalk | ✅ 可平移 / 建议换 giscus | 换 giscus 有官方迁移路径 |
| 百度统计 + 推送 | ✅ 纯片段平移 | 前端 JS，非服务端 API |
| RSS | ⚠️ 部分需自写 | 默认变 RSS 2.0 + `index.xml`；保留 atom.xml 需自写模板 |
| sitemap | ✅ 开箱即用 | 覆盖比现状更全（190 vs 100 条 `loc`），文件反而更小（14 KB vs 16 KB） |
| 归档页 `/archives/` | ⚠️ **需自己写** | 现有 80 个年月归档页；Hugo 不自动生成，需模板（`groupByDate`/`.Pages.GroupByDate`），工作量不大 |
| lightbox | ✅ render hook | 可复用现有 JS |
| 代码高亮 | ✅ 开箱即用 | 注意 `noClasses` / `lineNos` 默认值 |
| 微信二维码 | ✅ 纯前端平移 | 顺手清理 Google+ 与 http:// 死链 |

### 6.9 ⚠️ 一个必须提前处理的坑：裸 HTML 被静默丢弃

Hugo 的 `markup.goldmark.renderer.unsafe` **默认为 `false`**，Markdown 里的裸 HTML 会被替换成 `raw HTML omitted`，并且（v0.138+）打印警告。

**实测（用本站真实文章构建）：**
```
WARN  Raw HTML omitted while rendering ".../chronomem-oom-hunt.md"
WARN  Raw HTML omitted while rendering ".../eclipse-和-IDEA-多JDK设置方法.md"
...
```
**受影响的 7 篇文章（精确清单）：**
```
妄想症Paranoia.md
用安卓设备DIY一个NAS.md
缘尽世间.md
chronomem-oom-hunt.md
eclipse-和-IDEA-多JDK设置方法.md
Intellij-IDEA部署Tomcat-Maven版.md
Quest2 激活与无线串流的设置.md
```
**修复：**
```toml
[markup.goldmark.renderer]
  unsafe = true
```
实测：设 `unsafe = true` 后 `<div class="custom-box">` 原样保留；设 `false` 则被替换为 `raw HTML omitted`。

由于内容完全由你自己掌控（自建博客），开启 `unsafe = true` 是安全且必要的。

---

## 7. 构建与部署

### 7.1 单一二进制 vs Node 老版本困境

| 维度 | Hexo 3.7（现状） | Hugo |
|---|---|---|
| 运行时依赖 | Node（**实际锁死 Node 12**） | **无**（单一静态二进制） |
| 依赖体量 | 本机实测 `node_modules` = **67 MB**，lock 文件 **315** 条依赖 | 0（主题是 git submodule / Go module） |
| 版本状态 | hexo 3.7.1 / hexo-util 0.6.3 / hexo-renderer-marked 0.2.11（**均为 2018 年版本**）。Hexo 官方当前已是 **v8.1.2（2026-05-06）**，落后 5 个大版本 | Hugo **v0.166.0（2026-09-09）**，活跃维护；仓库 89,779★，Apache-2.0 |
| 本机 Node | **v24.20.0** → 与 Hexo 3.x 不兼容（`hexo-fs@0.2.3` 是现代 Node 下产出 0 字节文件的已知原因） | 无关 |
| 扩展版 | — | 需要 **extended** 版才支持 Hugo Pipes 编译 SCSS/Sass（本机 `hugo v0.165.0+extended`） |

**本站 CI 现状（`.github/workflows/build.yaml`）已明显腐化：**
```yaml
- uses: actions/checkout@v1      # ⚠️ Node 12 运行时，已被 GitHub 弃用
- uses: actions/setup-node@v1    # ⚠️ 同上，且未指定 node-version
- run: npm install hexo-cli -g && npm install
- run: hexo clean && hexo g
- uses: JamesIves/github-pages-deploy-action@v4
- uses: ystyle/hwcdn-cache@master   # 华为云 CDN 刷新（自研 action）
```
GitHub 已在 runner 上强制把 node12 action 升级到 node16/20 并持续告警（如 `"The following actions uses node12 which is deprecated and will be forced to run on node16: actions/checkout@v2..."`）。`actions/checkout@v1` / `setup-node@v1` 属于必须升级的历史遗留。

### 7.2 实测构建耗时

我把 96 篇文章 + 79 张图片转换后，在本机用 Hugo v0.165.0 extended 实测（同一台机器，多次冷启动）：

```
cold  hugo             run1: 0.273 s   run2: 0.291 s   run3: 0.310 s
cold  hugo --minify    run1: 0.342 s   run2: 0.295 s   run3: 0.300 s
warm  hugo --minify          : 0.319 s
输出: 18 MB / 100 个 HTML
```

> ⚠️ **口径说明（重要，避免误导）**：以上是**纯内容处理**耗时，用的是极简模板，**不含主题的模板渲染、CSS 编译**。一个带完整主题的 Hugo 站点实测通常在 **0.5 – 3 秒**量级（Hugo 官方文档与社区普遍报告 1000 页站点亚秒级）。
> 与 Hexo 的对比要点不是绝对秒数，而是：**Hexo 需要 `npm install` 拉 315 条依赖（67 MB）+ 编译 EJS/Stylus/Less**，而 Hugo 是单二进制、无安装步骤。

**参考对照**：本地 `public/` 总量 33 MB（含主题资源），Hugo 纯内容输出 18 MB（`--minify`）。

### 7.3 GitHub Actions 标准部署方式

**当前社区主流的 Hugo Action 状况（已核实）：**

| Action | 状态 |
|---|---|
| [peaceiris/actions-hugo](https://github.com/peaceiris/actions-hugo) | ✅ README 标注 **"Project status: active – The project has reached a stable, usable state and is being actively developed."**，使用 `@v3`。**支持 extended、Hugo Modules、最新版**（`hugo-version: 'latest'`）。**未提示用户迁移他处** |
| `actions/configure-pages` + `actions/upload-pages-artifact` + `actions/deploy-pages` | GitHub 官方第一方方案，无需第三方 action |
| `JamesIves/github-pages-deploy-action@v4` | 本站现用，仍在维护，可继续用于推 `master` 分支的模式 |

**关键实践要点（来自 peaceiris/actions-hugo README）：**
```yaml
- uses: actions/checkout@v4
  with:
    submodules: true      # 主题用 git submodule 时必须
    fetch-depth: 0        # 用 .GitInfo / .Lastmod 时必须（浅克隆会拿不到）

- name: Setup Hugo
  uses: peaceiris/actions-hugo@v3
  with:
    hugo-version: '0.166.0'   # 或 'latest'
    extended: true            # 需要 SCSS/Sass 时

- name: Build
  run: hugo --minify
```

**⚠️ 与本仓库直接相关的一条（README 明确单列 "Non-ascii Filename"）：**
本站 **91/96 篇文章文件名含中文**。若启用 `enableGitInfo`（进而影响 sitemap 的 `lastmod`），Hugo 在非 ASCII 文件名上取 git 信息会失败。解法是在 CI 中加：
```yaml
- name: Disable quotePath
  run: git config core.quotePath false
```

**关于 `baseURL`**：本站是 `ystyle.top` 的**根路径**部署（`public/CNAME` 存在，`root: /`），不是 `<user>.github.io/<repo>` 项目页子路径，所以 **baseURL 子路径坑对本站不适用**。但仍应为不同环境正确设置（否则 canonical、sitemap、OG 图 URL 会错）。

> **定性：有现成方案。** 建议直接迁移到 `actions/checkout@v4` + `peaceiris/actions-hugo@v3`（或 GitHub 官方 Pages 三件套）+ `hugo --minify`，同时保留现有的华为云 CDN 刷新步骤。

---

## 8. 总体评估

### 8.1 风险分级

| 风险 | 级别 | 说明 |
|---|---|---|
| Hugo 版 indigo 主题不存在 | 🔴 **高** | 必须自己移植或换主题，是最大工作量 |
| TOC 锚点 ID 全线不兼容 | 🟡 **中** | 811 个标题需脚本注入 `{#id}`；算法可照抄 `hexo-util` |
| gitalk 评论丢失 | 🟡 **中** | 因 URL 100% 保持，**pathname 映射可无缝接管** —— 风险已被第 3 节的成果化解 |
| 裸 HTML 被丢弃 | 🟢 **低** | 一行 `unsafe = true`；实测仅 7 篇 |
| RSS 格式/URL 变化 | 🟢 **低** | 阅读器兼容两种格式；如需保留 atom.xml 自写模板 |
| `<html lang>` 缺失导致 Pagefind 不分词 | 🟢 **低（但易漏）** | 本站现状就没有 `lang`；迁移时补上即可，漏了则**静默**失效 |
| `hasCJKLanguage` 未开 | 🟡 **中（易漏）** | 漏了不报错，但 `.Summary` 返回全文 → 首页观感变化 + RSS 621 KB（开了降到 238 KB）+ 阅读时长算错 |
| URL 变化 | 🟢 **已消除** | **实测 96/96 一致** |
| 百度统计/推送 | 🟢 **低** | 纯前端片段 |
| 代码高亮 / lightbox / 微信 | 🟢 **低** | 有现成方案或纯平移 |

### 8.2 明确的"三分类"

**✅ 有现成方案（配置或少量代码）**
- URL/permalink 精确保持（配方已实测 96/96 通过）
- 前端搜索 → **Pagefind**（官方中文分词，**前提是页面必须有 `lang` 属性**）；若想保持搜索行为 100% 不变，抄 **hugo-theme-stack 的 `assets/ts/search.tsx`**（自写正则子串匹配，与现状机制等价）+ Hugo 原生 `outputs: JSON`
- sitemap（开箱即用，覆盖更全）
- RSS（默认可用；完全等价需自写模板）
- 代码高亮 → **Chroma**（`hugo gen chromastyles` 实测可用）
- 图片 lightbox → **image render hook**
- 百度统计/推送 → partial 片段平移
- 微信二维码 → 纯前端平移
- gitalk → giscus（含官方 GitHub Issues→Discussions 迁移路径）
- CI 部署 → `peaceiris/actions-hugo@v3` 或 GitHub 官方 Pages 三件套
- front-matter 转换 → 自写约 30 行脚本（或 `pplmx/h2h`）

**🔧 需要自己写**
- **Hugo 主题**（indigo 无移植版）—— 最大工作量
- **811 个标题的 `{#id}` 注入脚本**（算法照抄 `hexo-util/lib/slugize.js`）
- **复刻 Hexo TOC 的 class 结构**（`.toc-number` / `.toc-level-N`）—— 自定义 partial + `.Fragments.Headings`
- **`/archives/` 年月归档页**（现有 80 个）—— Hugo 不自动生成，需用 `.Pages.GroupByDate` 写列表模板
- （可选）保留 `/atom.xml` 的 Atom 格式模板

**❌ 无法完全等价**
- **TOC 的 `<ol class="toc">` + 数字 + 分级 class 结构**：Hugo 原生 `.TableOfContents` 是 `<nav><ul>` 无 class 无数字。**用自定义 partial 可 100% 复刻**，故严格说是"可等价但需自写"，**Hugo 原生输出不等价**。
- **当前搜索的"子串匹配"语义**：Pagefind 是真正的分词倒排索引，**匹配行为会改变**（搜 `数据库索引` 从"整串连续命中"变为"'数据库'+'索引'两词各自命中，顺序无关、可能跨句"）。这是**行为变更而非纯升级**，迁移说明里应提示"搜索结果会变多、也可能出现以前搜不到的结果"。若必须保持行为不变，用 hugo-theme-stack 那套自写正则方案（见 4.4）。
- **微信 JS-SDK（`wx.config`）**：需要服务端签名，**静态站点原理上无法使用**（本站当前未使用，无影响）。
- **Hexo 的 `toc()` 直接读渲染后 HTML 的 id**：Hugo 是渲染前从 AST 生成，机制不同，但结果可对齐。

### 8.3 中文站「必填配置」清单（迁移第一步就要做）

这几项**每一项漏掉都会静默出问题**（不报错、但功能减半或行为错误），建议作为 `hugo.toml` 的初始模板：

```toml
baseURL    = "https://ystyle.top/"
title      = "东方星痕"
languageCode = "zh-cn"        # ① 必须是 zh-*，否则 Pagefind 不做中文分词
hasCJKLanguage = true         # ② 必须开，否则 .Summary 返回全文、RSS 膨胀 62%、阅读时长算错
disablePathToLower = true     # ③ 必须开，否则 9 篇含大写 slug 的 URL 改变
timeZone   = "Asia/Shanghai"  # ④ 与 Hexo 的 timezone 对齐（对 URL 非必需，但日期显示/比较/feed 需要）

[permalinks]
  [permalinks.page]
    posts = '/:year/:month/:day/:slug/'

[markup.goldmark.renderer]
  unsafe = true               # ⑤ 必须开，否则 7 篇的裸 HTML 被静默丢弃

[services.rss]
  limit = 20                  # ⑥ 对齐现状的 20 条（Hugo 默认不限）
```
并在模板里输出 `<html lang="{{ site.Language.LanguageCode }}">`（对应 ①，本站现状缺失）。

### 8.4 建议的迁移顺序

1. **先写转换脚本**：`permalink:` → `slug:`，加 `disablePathToLower = true` + `[permalinks]`，`hugo server` 起一个空主题，**逐条 diff URL 直到 96/96**
2. **注入 811 个标题锚点 id**（此步做完，站内 43 处锚点链接与外部深链才安全）
3. **决定主题路线**（自移植 indigo / 换主题 / 自写）—— 这是工期大头
4. **逐个搬运功能**：搜索（Pagefind，**务必先补上 `<html lang="zh-cn">`**）→ 代码高亮 → lightbox → sitemap/RSS → 百度 → 评论
5. **评论系统单独做一次**：先保持 gitalk 照抄（URL 不变即可无缝），确认稳定后再择机迁 giscus
6. **CI 切到 `actions/checkout@v4` + `peaceiris/actions-hugo@v3`**，保留华为云 CDN 刷新
7. **上线前跑一次 URL 全集比对 + 锚点全集比对**

---

## 9. 未验证 / 不确定事项

1. **Hugo 是否严格遵守语义化版本**：Hugo 长期停留在 `0.x`，社区普遍反映小版本之间存在破坏性变更（找到过 discourse 讨论帖 [Hugo does not follow semantic versioning?](https://discourse.gohugo.io/t/hugo-does-not-follow-semantic-versioning/56406) 但**未逐字核实官方原话**）。实践建议：**在 CI 里锁定精确版本**（如 `hugo-version: '0.166.0'`）而不是 `latest`，并建立升级回归流程。
2. ~~**Pagefind 对简体中文的分词效果**~~ → ✅ **已实测解决**（且证据已升级到索引内部）：注入 `lang="zh-cn"` 后 Pagefind 1.5.2 报告 `Discovered 1 language: zh-cn`；解压 `.pf_index` 后可见中文词条从**超长未切分串**（`阿里妈妈前端团队`）变为**真正的 jieba 词**（`阿波罗`、`安装方法`、`安全`）。**但"分词质量是否满足实际检索需求"仍需你用真实查询词人工验证** —— 因沙箱阻止 Node 访问本地 HTTP，未能跑通端到端查询演示。
3. **Hugo 的 `anchorize` / `autoIDType = 'github'` 对全角标点的完整规则**：我**实测了 8 个代表性标题**（结论：小写化 + 删除全角标点），但未穷举全部 521 个唯一 id 的映射。**因此第 5 节的建议是"注入显式 id"而不是"依赖某种 autoIDType 配置对齐"** —— 这个建议本身不依赖上述规则的完整性。
4. ~~**Fuse.js 在中文下的表现、hugo-theme-stack / PaperMod 是否使用 Fuse.js**~~ → ✅ **已核实**：PaperMod **确实**用 Fuse.js（`assets/js/fastsearch.js`，`threshold: 0.4` + `ignoreLocation: true`）；hugo-theme-stack **不用**，其 `assets/ts/search.tsx` 是自写正则子串匹配。**但**"Fuse.js 在中文下的误召回率"没有权威基准，4.4 节的分析是**基于官方 `threshold`/`ignoreLocation`/`minMatchCharLength` 语义 + PaperMod 实际默认参数的推理，不是实测数据**。
11. **Pagefind 是否禁止 `file://` 打开**：官方文档全文（含下载下来的 docs 源码 grep）**无 `file://` 字样**，无法证实；官方只要求经 HTTP 服务器（`--serve` 或任意静态服务器）。"`file://` 下 fetch/WASM 会被浏览器拒绝"属技术推断。GitHub Pages 走 HTTPS，不受影响。
12. **`npx pagefind` 的最低 Node 版本**：pagefind@1.5.2 的 npm 元数据**没有 `engines` 字段**，无法确认。**故勿在方案里写"只需 Node 20.x"。**
13. **经典 `PagefindUI` 是否仍支持 `baseUrl`**：当前官方 [Default UI 配置页](https://pagefind.app/docs/ui/) 只列了 `bundlePath`，**未列 `baseUrl`**；`baseUrl` 明写在 [Search config](https://pagefind.app/docs/search-config/)（`<pagefind-config base-url>` / `configureInstance` / `pagefind.options` 三种写法）。真实项目在 `new PagefindUI({...})` 里用过 `baseUrl`，但**经典 UI 的支持情况未能从当前文档证实**（可能是旧版遗留参数）。**建议用文档明确保证的新写法。**
14. **Pagefind 是否支持增量索引**：官方文档中**未找到**任何"增量索引"表述。有中文社区文章声称支持，**未能证实，建议不要采信**（该文另有两处与官方文档冲突："中文需要配置 `--force-language`"——官方文档里 `--force-language` 的用途是"忽略检测到的语言、把整站建成单一语言索引"，**不是启用分词**；以及"Pagefind 原生不支持中文分词"——与官方 multilingual 文档直接矛盾）。
15. **GitHub Pages 的服务端 gzip/brotli 行为**：未找到 GitHub 官方对其静态站点压缩策略的明确说明。**故"gzip 后 128.5 KB"是本地压缩结果，实际线上传输量取决于 Pages CDN** —— 但 **Pagefind 不受此影响**（索引自带 gzip）。
16. **Typesense Cloud 免费额度具体数值**、**MiniSearch 的中文分词能力**、**`hugo-zbsearch` 的实现**（存在于 Hugo 官方文档源码但不在抓到的渲染页里，页面在变动中）：均未能验证。
5. **Hugo 带完整主题的真实构建耗时**：第 7.2 节实测的是**纯内容处理**（0.27–0.34 s，极简模板），非完整主题构建。未在真实主题下测得端到端数字。
6. ~~**`hexo-generator-sitemap@1.2.0` 为何只产出 100 个 `<loc>`**~~ → ✅ **已查明**：读该插件 `lib/generator.js`，它只取 `locals.posts` + `locals.pages`，**设计上就不含 taxonomy 与归档页**，不是配置问题。（同时更正：sitemap 实际为 15,580 B，此前误记为 264 KB —— 那是 `atom.xml` 的体积，两者被写反。）
7. **GitHub 对 node12 action 的强制升级时间线**：仅从多个仓库的 runner 日志中确认了 `"uses node12 which is deprecated and will be forced to run on node16"` 这类告警实际存在，**未核实官方 changelog 的精确日期与当前策略**。
8. **`actions/setup-node@v1` 未指定 `node-version` 时的实际行为**：本站 workflow 里没有写 `node-version`，我**未验证**它在当前 runner 上究竟解析成哪个 Node 版本。这也是"为什么现在还能构建出正确产物"的疑点之一，建议你在动迁移前先确认当前 CI 的实际 Node 版本。
9. **`gitalk` 最后一次 release 的具体日期**：GitHub API 触发限流，仅确认了 7.2k★ / 144 open issues / 9 open PR / 181 commits 与公共 CORS 代理这一痛点，**未取到最近发布日期**。
10. **`hugo-lunr-zh` 在现代 Node 上的可运行性**：仅从 npm 元数据确认其依赖 `nodejieba@^2.2.5`（native 模块）与 2018 年的发布/推送时间，**未实际安装运行验证**。

---

## 附：本次调研中的关键验证命令与实测数据来源

| 结论 | 验证方式 |
|---|---|
| Hexo URL 计算逻辑 | 读 `node_modules/hexo/lib/plugins/processor/post.js:125-127`、`node_modules/hexo/lib/plugins/filter/post_permalink.js` |
| Hexo slug 规则 | 直接 `require('hexo-util').slugize()` 跑 6 个用例；读 `hexo-util/lib/slugize.js`、`escape_diacritic.js` |
| Hexo TOC 实现 | 读 `node_modules/hexo/lib/plugins/helper/toc.js`、`hexo-renderer-marked/lib/renderer.js` |
| 96/96 URL 一致 | 用 Python 转换 96 篇 front matter → Hugo v0.165.0 extended 构建 → 与 `public/` 逐条 diff |
| Hugo 小写化 9 篇 | 构造含大写 slug 的最小站点，比对 `disablePathToLower` 开/关 |
| 时区不影响 URL | `TZ=UTC` 下分别构建有/无 `timeZone` 站点 + 合成凌晨时间戳用例 |
| 811 个标题 / 120 含大写 / 485 含中文 | 遍历 `public/**/index.html` 提取 `<hN id="...">` 去重统计 |
| Hugo 标题 id 差异 | 构造 8 个代表标题的最小站点，Hugo v0.165.0 实际输出 |
| `{#id}` 可原样保留 | 同上，实测中文/大写/全角冒号全部保留 |
| 裸 HTML 丢弃 7 篇 | 用默认配置构建全部 96 篇，抓取 `WARN Raw HTML omitted while rendering` 清单 |
| Chroma 可用 | 实跑 `hugo gen chromastyles --style=monokai` → 3804 字节 |
| 构建耗时 | `time.time()` 包裹 `hugo --minify`，冷/热各 3 次 |
| Pagefind 识别 zh-cn 并启用分词 | 实跑 `npx pagefind@1.5.2 --site <真实 public/>` 两轮：无 lang → `unknown`/13,626 words；注入 `lang="zh-cn"` → `zh-cn`/8,781 words + zh-cn stemming 提示 |
| 本站 HTML 无 lang 属性 | `grep -o '<html[^>]*>' public/**/index.html` 输出裸 `<html>`；主题 `head.ejs` 无 `<html` |
| sitemap 覆盖 190 vs 100 | 转换后带 taxonomies 构建 Hugo 站点，统计 `sitemap.xml` 的 `<loc>` 并按路径前缀分组对比 |
| `[permalinks]` 三种写法 | 分别用三种 config 构建最小站点，观察产出 URL（含数组写法无 `target` 时误伤 section 页的实测） |
| 归档页需自写 | 实测 Hugo 构建产物中不存在 `/archives/`，而现有 `public/archives/` 有 80 个 `index.html` |
| 依赖体量 | `du -sh node_modules` = 67 MB；`package-lock.json` 315 条 |
| 无 Hexo 标签插件 / 无 more 标记 | `grep -r` 全量扫描 `source/_posts/` |
| content.json 压缩后体积 | `gzip -9 -c` = 131,572 B；`brotli -q11 -c` = 108,196 B（原始 357,447 B） |
| lunr-languages 已有中文 | npm registry 实测 v1.21.0 / 2026-08-09；`lunr.zh.js` 与 `min/lunr.zh.min.js` 均 HTTP 200；lunr 内核 2.3.9 / 2020-08-19 |
| Pagefind `_pagefind` → `pagefind` | 抓取 [v1-migration 文档](https://pagefind.app/docs/v1-migration/) 原文确认 |
| Pagefind 子路径需 `baseUrl` | 抓取 [Search config 文档](https://pagefind.app/docs/search-config/) 原文确认（"will be appended to the front of all search result URLs"） |
| Pagefind 分词内部证据 | 解压 `.pf_index`（gzip，文件头 `1f 8b 08 00`）后直接比对词条形态：unknown → 超长未切分串；zh-CN → jieba 词 |
| 文件真实体积（纠正写反的错误） | `stat -c %s` / `wc -c`：`sitemap.xml` = 15,580 B、`atom.xml` = 269,679 B、`content.json` = 357,447 B |
| Hexo sitemap 只收 100 条的原因 | 读 `node_modules/hexo-generator-sitemap/lib/generator.js`：只取 `locals.posts` + `locals.pages` |
| atom.xml 内嵌全文 | 解析 `<entry>/<content type="html">`：单条 entry 21,756 B，其中正文 20,633 B |
| Hugo RSS 默认体积 | 构建后读 `public/index.xml`：692,471 B / 96 条 item，格式 RSS 2.0 |
| `hasCJKLanguage` 对 RSS 的影响 | 同一站点构建两次对比：`false` → 636,269 B / desc 中位数 4,523 B / 80 条全文级；`true` → **244,202 B / 中位数 791 B / 25 条** |
| 摘要分隔符写法 | 构造 4 个最小用例构建：`<!--more-->` 与 `<!--more--> ` → `Truncated=true`；`<!-- more -->`（带空格）→ `Truncated=false` 且 Summary 为全文 |
