# 接续文档：Hexo → Hugo 迁移

> 写给下一个接手的人（或下一个会话的 AI）。
> 最后更新：2026-09-11
> 当前进度：**阶段 ① 完成**（内容 + 文章 URL 100% 对齐），下一步是阶段 ②（锚点注入）与阶段 ③（主题）。

---

## 0. 先读这一节

**目标**：把「东方星痕」博客从 Hexo 3.7 迁移到 Hugo，**保持现有 URL 与视觉不变**。

**当前结论**：可行。地基（内容/URL/搜索/部署）已验证；**唯一的硬骨头是主题** —— 不存在 `hexo-theme-material-indigo` 的 Hugo 移植版，47 个 EJS 模板（892 行）需要自己翻译。

**完整调研报告**：`HUGO-MIGRATION-FEASIBILITY.md`（1003 行，含全部证据、命令、风险分级、16 条未验证事项）。它原本在 Hexo 仓库根目录，**记得一并移过来**。

---

## 1. 两个仓库/目录

| 角色 | 路径 | 说明 |
|---|---|---|
| 源站（Hexo，生产） | `/home/ystyle/Code/Nodejs/ystyle.github.io` | 分支 `hexo`；push 触发 GitHub Actions 部署到 `master` → `ystyle.top` |
| 目标（Hugo，新建） | `/home/ystyle/Code/Nodejs/ystyle` | 本目录。原有一次失败的尝试，已备份到 `_legacy-attempt/` |
| 线上 | https://ystyle.top | GitHub Pages + 华为云 CDN（CI 末尾会刷新） |

**源站是生产环境，迁移期间不要动它**（除了本次已完成的 RSS 修复）。Hugo 版验证通过前，Hexo 保持可发布状态。

---

## 2. 已经做完的事

### 2.1 顺带修复了 Hexo 的 RSS（已上线，与迁移无关但值得知道）

`atom.xml` 原本每条 entry 内嵌**完整正文 HTML**，20 条撑到 **264 KB**，订阅者每次抓取全量下载。

- 改动：`_config.yml` 增加 `feed: {content: false, content_limit: 300}`
- 新增：`scripts/fix-feed-summary.js` —— 插件对正文做**定长硬截断**，会停在标签中间（实测 11/20 条尾部残缺如 `...<hr`、16/20 条开闭标签不匹配），该脚本在 `before_exit` 时清理每条摘要
- 结果：**269,679 → 28,870 字节（-89%）**，标签零残缺
- ⚠️ **踩坑**：清理逻辑**不能挂在 `after_generate`** —— 它在 `hexo.load()` 内部触发，那时文件还没写入 public（写文件在更晚的 `firstGenerate()` 里）。必须用 `before_exit`。

### 2.2 阶段 ①：内容 + URL 对齐（核心成果）

**结果：文章页 96/96 完全一致，缺失 0、新增 0。**

产物（本目录）：

```
hugo.toml                    # 站点配置，见第 3 节
content/posts/*.md           # 96 篇，已从 Hexo 源转换
layouts/                     # 阶段①最简模板（只够验证 URL，不是主题）
  _default/baseof.html
  _default/single.html
  _default/list.html
  404.html
tools/convert.py             # Hexo → Hugo 内容转换（可重复运行）
tools/compare-urls.py        # URL 逐条比对
tools/expected-urls.txt      # 96 条基准 URL（从旧站 public/ 反推）
tools/convert-report.txt     # 逐篇转换明细
```

构建耗时：**约 175 ms**（96 篇，冷启动）。

---

## 3. hugo.toml 的关键配置（每一项都别删）

这些配置的共同特点是：**配错/漏配不报错，但功能减半或行为错误**。

```toml
locale       = "zh-cn"           # 必须 zh-*，否则 Pagefind 静默不做中文分词
                                 # 注意：Hugo v0.158 起 languageCode 已弃用，改用 locale
hasCJKLanguage = true            # 不开则 .WordCount 严重低估 → .Summary 返回全文
                                 # （首页每篇显示全文）、RSS 从 238KB 膨胀到 621KB、阅读时长算错
disablePathToLower = true        # 不开则含大写 slug 的 9 篇文章 URL 直接改变
timeZone     = "Asia/Shanghai"   # 对齐 Hexo（对 URL 非必需，日期显示/比较需要）

[permalinks]
  [permalinks.page]
    posts = '/:year/:month/:day/:slug/'   # 对齐 Hexo 的 :year/:month/:day/:title/

[markup.goldmark.renderer]
  unsafe = true                  # 不开则正文里的裸 HTML 被静默丢弃（本站 7 篇，含 chronomem-oom-hunt.md）

[services.rss]
  limit = 20                     # 对齐 Hexo 现状（Hugo 默认不限条数）

[pagination]
  pagerSize = 10                 # 对齐 Hexo 的 per_page: 10
```

模板里还要输出 `<html lang="{{ site.Language.Locale }}">`（baseof.html 已含）。

⚠️ **`[permalinks]` 别用数组写法**（`[[permalinks]] pattern=...`）：不写 `target` 会匹配所有页面，把分类/标签页也改写成日期路径。

---

## 4. 为什么 `permalink` 能一对一映射成 `slug`

Hexo 源码 `node_modules/hexo/lib/plugins/processor/post.js`：

```js
if (data.permalink) {
  data.slug = data.permalink;   // permalink 被当成 slug
  delete data.permalink;
}
```

然后代入全局 `permalink: :year/:month/:day/:title/` 的 `:title` 令牌。
所以 Hexo 的 `permalink` ≡ Hugo 的 `slug` + `:slug` 占位符，**语义一一对应**。

96 篇里有 95 篇写了 `permalink`，剩 1 篇（`Docker-搭建redis-集群.md`）靠文件名，两边行为也一致。

**另一个冷知识**：Hexo 和 Hugo **都不做中文→拼音转写**。站内那些拼音 slug（`duan-wu-jie-kuai-le`）全是人工写在 front-matter 里的。

---

## 5. 迁移中暴露的真问题（阶段 ① 的价值所在）

| # | 问题 | 影响 | 状态 |
|---|---|---|---|
| 1 | `lastmod: 2020-08-6`（单位数月份） | Hexo 的 moment 能容忍，**Hugo 报 `not a parsable date` 并让该页渲染失败** | ✅ 已在 `convert.py` 里做日期归一化 |
| 2 | `categories: 软件` 是字符串不是列表 | 模板 `range` 报 `range can't iterate over 软件` | ✅ 用 `.GetTerms` 而非 `.Params.categories` |
| 3 | **标签大小写**：Hexo 把 `Cangjie` 与 `cangjie` 当两个独立标签 | Hugo 会**合并**，标签页 160 → 145 | ⚠️ 待决策（接受合并 / 加 alias） |
| 4 | Hugo 额外生成 `/page/1/` 冗余页 | 分类页 17→27、标签页 160→313 | ⚠️ 无害，可后续清理 |
| 5 | `/archives/` 的 80 个年月归档页 | Hugo **不自动生成** | ❌ 需自己写模板 |

---

## 6. 全站路径比对现状

运行 `python3 tools/compare-urls.py` 可复现：

| 类型 | Hexo | Hugo | 说明 |
|---|---|---|---|
| **文章页** | 96 | 96 | ✅ **完全一致** |
| 首页 | 1 | 1 | ✅ |
| 分页 | 9 | 10 | ✅ 基本对齐 |
| 分类页 | 17 | 27 | ⚠️ 多出 `/page/1/` |
| 标签页 | 160 | 313 | ⚠️ 同上 + 大小写合并 |
| 归档页 | 80 | 0 | ❌ 待写模板 |

---

## 7. 待办（按建议顺序）

1. **阶段 ②：811 个标题注入 `{#hexo原id}`**
   - 为什么必须做：Hugo 默认 `autoIDType='github'` 会**强制小写 + 删全角标点**，与 Hexo 的 id 规则不同。实测 811 个标题 / 521 个唯一 id（120 含大写、485 含中文）/ 43 处站内锚点链接。
   - 算法：逐字照抄 `node_modules/hexo-util/lib/slugize.js`
   - 已实测确认 Hugo 会原样保留显式 id（含中文/大写/全角冒号）
   - 注意：**不要指望靠 `autoIDType` 配置对齐**（规则未穷举验证），注入显式 id 才可靠

2. **补齐 `/archives/` 与分类/标签页**，让全站比对也接近 100%

3. **阶段 ③：定主题路线**（工期大头）
   - 路线 A：自己移植 indigo 主题（47 个 EJS / 892 行 → Go template）
     - 好消息：CSS 可直接用已编译的 `style.css`（72 KB）；主题的滚动高亮 JS 用通用选择器（`#post-toc a[href="#id"]`、`li.active`），**换 Hugo 后无需改动即可工作**，只要模板复刻出同样的 class 结构
   - 路线 B：换一个 Material 风格 Hugo 主题（外观会变）
   - ⚠️ 避开同名陷阱：`AngeloStavrow/indigo`（IndieWeb 排版主题）、`blogless/polymer-indigo`（零改动 fork）都与本主题无关

4. **前端搜索**（两个方案都已验证可行，待选）
   - 保真：照抄 `hugo-theme-stack` 的 `assets/ts/search.tsx`（自写正则子串匹配），与现有 Hexo `search.js` **语义完全等价**，零新增依赖
   - 升级：Pagefind（真中文分词 + 相关性排序），但**搜索结果行为会变**（`数据库索引` 会拆词匹配）；且**不省流量**（首载 130–290 KB vs 现状 gzip 128.5 KB，同量级）
   - 前置：必须先有 `<html lang="zh-cn">`

5. **评论**：建议 gitalk → giscus（官方支持把 issues 转 discussions，映射选 `pathname` 即可无缝接管）。⚠️ 评论身份绑定 URL —— **URL 100% 一致正是评论不丢的前提**。

6. **CI**：换 `actions/checkout@v4` + `peaceiris/actions-hugo@v3`，保留华为云 CDN 刷新步骤

---

## 8. 命令速查

```bash
# 内容转换（从 Hexo 源重新生成 content/posts）
python3 tools/convert.py

# 构建
hugo -d public --cleanDestinationDir

# 本地预览
hugo server

# URL 逐条比对（核心验收手段）
python3 tools/compare-urls.py     # 退出码 0 = 文章页完全一致
```

**本地构建 Hexo 源站时注意**：必须用 **Node 12**（`fnm use 12.22.12`）。Node 14+ 会因为 hexo 3.7 的 `pipeStream` 提前 resolve 把**所有产物写成 0 字节**。

---

## 9. 踩坑记录（别重复踩）

1. **`after_generate` filter 拿不到刚生成的文件**（见 2.1）
2. **`languageCode` 在 Hugo v0.158+ 已弃用** → 用 `locale`
3. **`.Params.categories` 可能是字符串** → 用 `.GetTerms`
4. **Hugo 对日期格式严格**（`2020-08-6` 不合法）→ 转换时归一化
5. **不要用 `[permalinks]` 数组写法**（会污染分类/标签页 URL）
6. **`ls -lh a b` 按字母序输出** —— 曾导致把 `sitemap.xml`(16KB) 和 `atom.xml`(264KB) 的体积读反
7. **Pagefind 的输出目录是 `pagefind` 不是 `_pagefind`**（GitHub Pages 默认忽略 `_` 前缀目录，别抄老教程）

---

## 10. 尚未验证的事项（引自调研报告第 9 章，共 16 条）

最需要留意的几条：

- **Hugo 是否遵守语义化版本**（长期 0.x，社区反映小版本有破坏性变更）→ CI 建议**锁定精确版本**而非 `latest`
- **`autoIDType` 对全角标点的完整规则**只测了 8 个代表标题，未穷举 521 个 id（但"注入显式 id"的建议不依赖该规则完整性）
- **Pagefind 分词质量**：引擎能力已由索引内部证据证实，但"是否满足实际检索需求"需用真实查询词人工验证
- **Hugo 带完整主题的真实耗时**（实测 175ms 是纯内容处理，不含主题模板与 CSS）
- **`actions/setup-node@v1` 未指定 node-version 时实际解析成哪个 Node** —— 这关系到"为什么现在还能构建出正确产物"，动迁移前建议先确认

---

## 11. 预览版模板与三条结构约束（做阶段 ③ 时必须遵守）

为了让内容能在主题样式下正常显示，已把 Hexo 主题**编译好的样式**接了过来：

- `static/css/` ← 复制自旧站 `public/css/`（`style.css` 72 KB + 字体 + cloudTie）
- `layouts/_default/baseof.html` 引入样式表并搭出 `#main` / `#header` 骨架
- `layouts/_default/single.html` 复刻文章页结构（banner + 文章卡片 + TOC 侧栏）

启动预览：`hugo server` → http://127.0.0.1:1313/

### 三条隐式契约（都来自主题 CSS，写错就错位）

| 约束 | 原因 | 症状 |
|---|---|---|
| `.fade` / `.fade-scale` 必须同时带 `.in` | CSS 是 `.fade{opacity:0}` / `.fade.in{opacity:1}`，线上靠 `main.js` 在 load 事件里补 `.in` | 整页内容以 `opacity:0` 隐身（正是那篇 OOM 排查文的故障现象） |
| 必须有 `<header class="content-header post-header">` banner | `.post-card` 有 `margin-top:-150px`，是**故意压在 banner 上**的 | 卡片被拉到视口外（实测 `artTop = -120`） |
| `<aside class="post-widget">` 必须排在 `<article>` **之前** | CSS 用的是相邻选择器 `.post-widget + .post-article` | 文章区丢布局（宽度/浮动错乱） |

### 预览版尚缺（都属于阶段 ③）

- `#menu` 侧边抽屉菜单（`.nav` 导航、头像、遮罩层）
- 顶栏的搜索 / 分享图标
- **TOC 编号**：Hexo 是 `list_number: true` → `1.` `1.1.` 层级编号；Hugo 默认无编号，需要用 `.Fragments.Headings` 自建 partial 复刻
- 全部交互 JS（`main.js`：菜单开合、滚动高亮、搜索弹窗、lightbox、分享）
- **代码高亮配色**：Hexo 用 highlight.js 在客户端着色，Hugo 用构建时 Chroma。要复用外部 CSS 得设 `[markup.highlight] noClasses = false` 再 `hugo gen chromastyles`
- 底部的版权 / 标签 / 上下一篇导航 / 评论

> 预览版的意义是**确认内容渲染无误**，不是最终视觉。真正的主题移植见第 7 节待办 3。

---

## 12. 阶段 ② 已完成：标题锚点对齐

**结果：96 篇逐条比对，95 篇完全一致，1 篇属行为差异（见文末）。**

### 做法

`tools/inject-anchor-ids.py` —— 给 markdown 标题追加 `{#id}`。id **不复刻算法**，
而是直接从旧站 `public/**/index.html` 提取真实 id，再按**标题文本**回填。

```bash
python3 tools/inject-anchor-ids.py    # 幂等，可重复运行
python3 tools/verify-anchor-ids.py    # 验收：逐篇对比两边 heading id
```

### 为什么按「标题文本」匹配，而不是按「数量顺序」对应

有三类标题**不该**被注入，按数量对应会让整体错位：

| 情况 | 例子 | 处理 |
|---|---|---|
| 裸 HTML 标题（自带 id） | `<h3 id="1">eclipse</h3>` | Hugo 用 `unsafe=true` 原样保留，无需注入 |
| 位于 `<details>` 等 HTML 块内的 `###` | Quest2 篇的 3 个标题 | Hexo 与 Hugo 都不渲染，跳过 |
| 围栏/缩进代码块里的 `#` | — | 跳过 |

### 踩到的三个坑（都已修）

1. **围栏配对错位**：最初用「首字符相同即闭合」判断，把 ` ```shell ` 这种**开启**当成了闭合，
   后续配对整体错位 —— 《使用Docker快速上手鸿蒙》第 115 行的真标题因此被误判进代码块而漏注入。
   正解：CommonMark 规定**闭合围栏不能带 info string**，且长度不短于开启者。
2. **智能引号**：Hexo 渲染器把 `Let's` 变成 `Let’s`（U+2019），文本比对假性失败。
   正解：`norm()` 里做智能标点 → ASCII 归一化。
3. **畸形 heading 文本**：《windows-10-子系统Archlinux》里 Hexo 把标题渲染成了
   `<h3 id="…">文件夹…zsh.reg">以下存为文件 -> …</h3>`（前缀多了一截）。
   正解：精确匹配失败时允许「站点侧文本以 md 标题结尾」。

### 唯一保留的差异：Quest2 篇

站点 6 个 heading，Hugo 9 个 —— 多出的 3 个来自 `<details>` 折叠块内的 `###`。

根因是 marked（Hexo）与 goldmark（Hugo）对 HTML 块边界的判定不同：**Hugo 遵循 CommonMark，
「空行即结束 HTML 块」**，因此其后的 `###` 被正常解析成标题；Hexo 则把整块当 HTML。
**这是行为差异不是 bug**，且属内容增强（折叠块内的标题也能进 TOC、可跳转），故保留。
副作用：该篇 TOC 会比原站多 3 项。

> 如果哪天真要消除这个差异，只能改文章内容（把 `<details>` 里的 `###` 换成加粗文本），
> 不建议为一个页面动内容。

---

## 13. 页面结构补齐：全站 URL 100% 对齐 ✅

**结果（`python3 tools/compare-urls.py`）：**

| 类型 | Hexo | Hugo |
|---|---|---|
| 文章页 | 96 | 96 |
| 归档页 | 80 | 80 |
| 标签页 | 160 | 160 |
| 分类页 | 17 | 17 |
| 分页 | 9 | 9 |
| 首页 | 1 | 1 |
| 其他 | 2 | 2 |

**差异清单为空。生成 365 个 HTML，与旧站完全一致。**

### 这一轮新增的东西

| 命令 | 作用 |
|---|---|
| `tools/gen-archives.py` | 生成 `content/archives/**/_index.md`（1 总 + 11 年 + 54 年月） |
| `tools/convert-pages.py` | 迁移独立页面：`friends`、`categories/tags` 索引 |
| `tools/gen-tag-aliases.py` | 给大小写变体标签写 alias，让旧 URL 重定向 |
| `layouts/archives/list.html` | 归档页模板（按 front-matter 的 year/month 筛文章 + 分页） |
| `layouts/_default/terms.html` | `/tags/`、`/categories/` 索引页模板 |
| `layouts/404.html` | 复刻原站 404（整页自定义 HTML，不套 baseof） |
| `content/posts/_index.md` | 关掉 Hugo 自动生成的 `/posts/` 列表页（Hexo 没有） |
| `static/images/` | 补上 79 个图片资源（15 MB），之前只迁了 CSS |

### 为什么归档要「生成 content 文件」

Hugo 没有内置的按年月归档。做法是在 `content/archives/` 下生成嵌套的 `_index.md`（branch bundle），
每个文件在 front-matter 标注 `year`/`month`，模板据此筛选并分页。

⚠️ **Go template 的 `where` 无法按 `.Date.Year` 过滤**（那是方法调用，不是字段），
所以模板里用 `range` + `if` 手动筛。

### 又踩到四个坑

1. **Go 把 `"09"` 当八进制**：`int "09"` 报 `strconv.ParseInt: parsing "09": invalid syntax`。
   → front-matter 里 month 必须写成**不带前导零**的整数（`month: 9`）。
2. **`_build` 已改名**：Hugo 0.145 弃用并移除了 `_build`，现在是 **`build`**。
3. **taxonomy 索引页被分页**：`/tags/` 若套用带 `.Paginator` 的 list 模板，会额外生成
   `/tags/page/2/` … `/tags/page/16/`（Hexo 的 `/tags/` 是单页）。
   → 单独写 `layouts/_default/terms.html`，不调 `.Paginator`。
4. **脚本的路径假设失效**：项目从 `ystyle.github.io/hugo-migration/` 搬到 `~/Code/Nodejs/ystyle` 后，
   与 Hexo 仓库从「父子」变成了「兄弟」，`os.path.dirname(BASE)` 不再指向源仓库。
   → `convert.py` / `convert-pages.py` 改为显式配置 `HEXO_REPO`（可用环境变量覆盖）。

### 标签大小写：Hugo 会合并，用 alias 保住旧 URL

原站把 `Cangjie`/`cangjie`、`Docker`/`docker`、`GIT`/`git` 这类写成**两个独立标签**（共 13 组）。
Hugo 的 taxonomy 大小写不敏感，会合并成一个（保留「首次出现」的写法）——这是改进，
但另一半 URL 会 404。`gen-tag-aliases.py` 在合并后的 term 上写 `aliases`，
Hugo 生成 meta refresh + canonical 的跳转页，旧链接照样能用。

> ⚠️ Hugo 保留哪个变体取决于文章处理顺序。若将来新增文章用了另一种写法，可能改变选择。
> 真在意的话就把文章 front-matter 里的 tags 统一大小写（会改动内容，权衡后再定）。

---

## 14. 主题移植：CSS 与 JS 都成功复用 ✅

**结果**：菜单、顶栏、banner、页脚、TOC 编号、文章底部、列表卡片、归档 waterfall、
分页、标签/分类索引页全部复刻完成，**浏览器实测 JS 零错误**。

### 最关键的结论：主题的 CSS 和 JS 几乎不用改

- `static/css/style.css`（72 KB，从旧站 `public/css` 复制）**原样可用** ——
  Go template 只要输出相同的 class，样式就直接生效。
- `static/js/main.min.js`（7.4 KB，主题原版）**一行未改就跑通**：
  菜单开合、滚动高亮、gotop、waterfall 瀑布流、lightbox 全部正常。
  前提是 DOM 的 id/class 严格对齐（第 11 节那三条约束）。

**所以主题移植的真实工作量 = 翻译模板结构，而不是重写样式或交互。**

### 本轮新增的模板

| 文件 | 对应原主题 |
|---|---|
| `layouts/_default/baseof.html` | `layout.ejs` |
| `layouts/partials/menu.html` | `_partial/menu.ejs`（头像/品牌/8 项导航） |
| `layouts/partials/header.html` | `_partial/header.ejs`（顶栏 + 页面 banner） |
| `layouts/partials/footer.html` | `_partial/footer.ejs`（版权 + 备案） |
| `layouts/partials/after-footer.html` | `_partial/after-footer.ejs`（mask + gotop） |
| `layouts/partials/toc.html` + `toc-item.html` | `_partial/post/toc.ejs`（带层级编号） |
| `layouts/partials/paginator.html` | `_partial/paginator.ejs` |
| `layouts/partials/search.html` | `_partial/search.ejs` |
| `layouts/_default/single.html` | `_partial/post.ejs`（含版权/标签/上下篇） |
| `layouts/_default/list.html` | `index.ejs` 的列表卡片 |
| `layouts/archives/list.html` | `archive.ejs`（年月分组 + waterfall） |
| `layouts/_default/terms.html` | `tags.ejs` / `categories.ejs` |

菜单项写在 `hugo.toml` 的 `[[menu.main]]`，`identifier` 同时用作 fontawesome 图标名
（与原主题 `menu:` 配置一一对应）。

### 又踩到四个坑

1. **`.Fragments.Headings` 顶层有个虚拟节点** —— `level-0`、无 ID 无 Title 的包裹节点。
   直接 `range` 会让 TOC 多出一条空的 `1.`。→ 检测 `not (index $headings 0).ID` 后取其 `.Headings`。
2. **Hugo 没有 URL 解码函数** —— `.Fragments` 的 ID 是 percent-encoded（正文 `<h2 id>` 却是原文），
   而 `urls.Unescape` 并不存在（`htmlUnescape` 只解 HTML 实体）。
   → 接受编码：浏览器访问 `#%e4%b8%80…` 会自动解码，跳转正常，仅字面形式与原站不同。
3. **`async` 脚本会抢在 DOM 之前执行** —— 原站 `search.min.js` 用 `async`，本地延迟低时会赶在
   HTML 解析到 `<template id="search-tpl">` 之前运行，`$('#search-tpl').innerHTML` 取到 null。
   → 改成 `defer`。
4. **agent-browser 的 `errors` 不跨页面清空** —— 修好后仍报同样的错，其实是上一次加载累积的。
   → 用全新 session 复测（`close --all` 后重开）才准。

### 与原站的已知差异

| 项 | 说明 |
|---|---|
| TOC 锚点 href | Hugo 输出 percent-encoded，原站是中文原文；**跳转行为一致** |
| 列表页摘要 | Hugo 315 字符 vs 原站 230（`summaryLength` 已从默认 70 调到 30） |
| 代码高亮 | Hugo 用 Chroma 内联样式（monokai），原站是 Hexo highlight + `.highlight` 容器；观感接近、实现不同 |
| 分享弹窗 | **未移植**，故 `BLOG.SHARE` 暂设 `false`（main.js 的 `modal()` 会对不存在的 `#globalShare` 抛错并中断整个脚本） |
| 评论 | gitalk 尚未接入 |
| `#search-tpl` 数据源 | `/content.json` 未生成 → 搜索面板能打开但搜不到结果（属「搜索方案」待办） |

---

## 15. 分享弹窗 + 评论接入完成 → 主题移植收尾 ✅

新增两个 partial，主题的功能面到此完整。

| 文件 | 对应原主题 |
|---|---|
| `layouts/partials/share.html` | `_partial/post/share.ejs`（一个模板两种 scope） |
| `layouts/partials/comment.html` | `_partial/post/comment.ejs` → `plugins/gitalk.ejs` |

### 用法

```go
{{ partial "share.html" (dict "scope" "global" "page" .) }}   {{/* 全站分享弹窗 + 微信二维码 */}}
{{ partial "share.html" (dict "scope" "page"   "page" .) }}   {{/* 文章页浮动分享 */}}
{{ partial "comment.html" . }}                                {{/* gitalk 评论区 */}}
```

`baseof.html` 输出 global 分享，`single.html` 输出 page 分享 + 评论区。

### 关键点：BLOG.SHARE 必须与 DOM 同时存在

`main.js` 的 `share()` 会执行 `new this.modal("#globalShare")`，而 `modal()` 里紧接着
`this.$modal.querySelector(".close")` —— **元素不存在就会抛错并中断整个脚本**
（连 `#loading` 进度条都会卡住，正是第 12 章那个故障的同类现象）。

所以 `hugo.toml` 的 `params.share` 与 `#globalShare` 的 DOM 必须同进同退。

### 微信二维码：Hugo 没有 qrcode helper，改在客户端生成

原站靠 `hexo-helper-qrcode` 在**服务端**生成 data URI；Hugo 无此能力。
方案是把 `qrcode-generator` 下载到 `static/js/qrcode.min.js`（56 KB，UMD 自动挂 `window.qrcode`），
在 `baseof.html` 末尾读 `#wxShareQrcode` 的 `data-url` 现场生成 —— **不引入任何远程依赖**，
失败也只影响二维码本身（整段包在 try 里）。

### 实测结果（干净会话）

```
二维码已生成 : data:image/gif;base64,R0…     ← 本地生成，无外部请求
gitalk 容器  : true
点击 #menuShare → 遮罩 "mask in"、弹窗 "global-share ready in"
JS 错误      : 0 条
```

### 主题移植完成度

| 部分 | 状态 |
|---|---|
| 菜单 / 顶栏 / banner / 页脚 / gotop / mask | ✅ |
| TOC 层级编号 | ✅ |
| 文章页（正文 / 版权 / 标签 / 上下篇 / 分享 / 评论） | ✅ |
| 列表页 / 归档 waterfall / 分页 / 标签分类索引 | ✅ |
| 分享弹窗（含微信二维码） | ✅ |
| 评论（gitalk） | ✅ |
| 代码高亮 | ✅ Chroma |
| **搜索** | ⬜ 面板已就位，缺 `/content.json` 数据源 |
| **RSS 的 `/atom.xml`** | ⬜ 现用 Hugo 默认的 `/index.xml`（菜单里已临时指向它） |

---

## 16. 搜索数据源与 RSS 补齐 → 功能无缺口 ✅

| 数据源 | 实现 | 状态 |
|---|---|---|
| `/content.json` | `layouts/index.content.json` + `[outputFormats.Content]` | ✅ 复刻原站结构（96 篇全文索引） |
| `/atom.xml` | `layouts/index.atom.xml` + `[outputFormats.Atom]` | ✅ 20 条，Atom 1.0 |
| `/index.xml` | 已从 `[outputs] home` 移除 | ✅ 与原站一致（不存在） |

**实测搜索**：输入「容器」→ **16 条结果**，面板正常展开，JS 零错误。

采用的是**保真方案** —— `search.js` 一行未改，仍是纯前端子串匹配，行为与 Hexo 时期完全一致，
没有引入 Pagefind/lunr 之类的分词引擎，也没有新增任何依赖。

### 踩到四个坑

1. **`application/atom+xml` 不是内置媒体类型** —— 必须先声明 `[mediaTypes."application/atom+xml"]`，
   否则报 `media type "application/atom+xml" not found` 并让**整个构建失败**（连 `hugo server` 都起不来）。
2. **`<?xml …?>` 声明被转义** —— `.xml` 模板处于 XML 上下文，硬编码的 `<?xml` 会输出成 `&lt;?xml`，
   整个 feed 直接解析失败。必须走 `safeHTML`。
3. **summary 双重转义** —— `htmlEscape` 转一次，XML 上下文再转一次（得到 `&amp;lt;`）。
   加 `safeHTML` 阻止二次转义。副作用：Go 把 `"` 写成 `&#34;` 而原站是 `&quot;`，XML 语义等价。
4. **`titleCaseStyle` 默认会改标签名** —— Hugo 对 taxonomy 的 term 做 title-case：
   `badger-cj` → `Badger-Cj`、`json-rpc` → `Json-Rpc`，而且 **`.Title` 拿到的也是处理过的值**
   （换成 `.LinkTitle` 没用）。必须配 `titleCaseStyle = "none"`。
   这个坑会同时污染页面标签、`content.json` 的 `name` 字段和 atom 的 `category term`。

### 体积对比（Hugo vs 原站）

| 文件 | Hugo | 原站 |
|---|---|---|
| `atom.xml` | 27,685 | 28,870 |
| `content.json` | 368,616 | 357,447 |

差异来自摘要长度和 JSON 字段顺序，功能等价。

### 至此迁移的功能面已无缺口

内容 · URL · 锚点 · 页面结构 · 主题视觉 · 分享 · 评论 · 搜索 · 订阅，全部就位。
剩下的只有上线流程（CI + DNS）和最后的逐篇 HTML 细节比对。

---

## 17. 首页摘要：Hugo 与 Hexo 的差异及修复 ✅

**现象**：Hugo 首页每篇看起来显示了两次标题，摘要格式也与线上不同。

**根因**：两边对摘要里 HTML 的处理策略正好相反 ——

| | 配置 | 结果 |
|---|---|---|
| Hexo | `excerpt_render: false` | 摘要**不解析 HTML**，输出纯文本 |
| Hugo | `.Summary` 默认 | **保留 HTML** → 正文里的小节标题（如 `## 一条空消息`）被渲染成大标题，看起来就是列表项标题重复 |

**修复两处**：

1. `layouts/_default/list.html` 改用 `{{ .Summary | plainify }}` 去掉标签
2. `hugo.toml` 的 `summaryLength` 从 30 调到 **70** —— plainify 去掉标签后字符数骤减
   （实测 30 词 → 136 字符、50 词 → 165 字符、70 词 → 239 字符，原站 230）

**实测**：首篇摘要 239 字符、纯文本、段落折叠成行、末尾 `Continue reading...`，与线上一致。

> 这个差异提醒了一件事：**Hexo 的 `excerpt_*` 系列配置和 Hugo 的 `.Summary` 不是一一对应的**，
> 迁移时凡是「模板里怎么取摘要」的地方都要重新确认一遍，不能假设同名即同义。

---

## 18. 清理正文里重复的文章标题（7 篇，已上线）✅

**起因**：首页摘要看起来"包含文章标题"，一度以为是 Hugo 独有的问题。

**排查结论**：**Hexo 与 Hugo 行为一致** —— 摘要取自正文，而这些文章的正文开头又写了一遍标题
（`# 标题`），所以两边都会带上它。真正让人误判的是块级标签间空白的处理不同：

```
Hugo : 戴森球与光伏文明：一个被忽略的最优解 引言：悖论的另一面 在关于…
原站 : 戴森球与光伏文明：一个被忽略的最优解引言：悖论的另一面在关于…
```

Hugo 保留了标签间换行（渲染成空格），标题因此显得"独立"；原站粘连在一起，看起来像没有标题。

**处理**：删除 Hexo 源里那 7 行冗余标题，重新转换 + 重新注入锚点 id。

| 项 | 说明 |
|---|---|
| 改动 | `source/_posts/` 7 个文件，19 行删除 |
| 提交 | `b062b01d` → CI 成功 → master `8c9257fe` |
| 线上 | CDN 约 11 分钟后刷新，摘要已不含标题 |

**为什么改源头而不是改 `content/posts/`**：后者由 `tools/convert.py` 生成，
只改那边的话下次重新转换就被覆盖了。

**代价**（预期内）：这 7 篇的 TOC 少一项（正是被删的标题本身）。

**锚点验收仍是 95/96**（唯一不一致的还是 Quest2 的 `<details>` 行为差异）。

> ⚠️ 排查时踩了两个坑，都值得记：
> 1. 统计脚本一开始报"0 篇重复标题"，原因是文章里的标题行带着注入的 `{#id}` 后缀，
>    与 front-matter 的 title 做全等比较自然失败。**比对文本前记得先剥掉注入标记。**
> 2. 改完源头后 `verify-anchor-ids.py` 一度报 88/96 —— 假报警：它比对的"Hexo 侧"是
>    **旧的 public 构建**。必须先重建 Hexo 产物（`hexo clean && hexo generate`）
>    再验收，否则基准本身是过期的。
