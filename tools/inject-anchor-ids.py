#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段 ②：给文章标题注入显式 id，使 Hugo 生成的锚点与现有站点完全一致。

为什么需要：
  Hugo 默认 autoIDType='github' 会「强制小写 + 删除全角标点」，而 Hexo 的 id
  来自 hexo-util/lib/slugize.js，规则是「特殊 ASCII 字符转 '-'，但保留大小写、
  保留中文、保留全角标点」。同一个标题两边结果不同，例如：

    Hexo: 第二现场：256MB-的-GC-堆与-4MB-的-memtable
    Hugo: 第二现场256mb-的-gc-堆与-4mb-的-memtable

  站内有 43 处锚点链接、站外也可能有，所以必须显式固定 id。

id 从哪来：
  **不复刻算法**，而是直接从现有站点已生成的 public/**/index.html 里提取真实 id，
  再按**标题文本**回填 —— 这是唯一 100% 准确的来源。

为什么按文本匹配而不是按数量顺序对应：
  有些标题不该被注入，例如
    · 裸 HTML 标题 <h3 id="1">eclipse</h3>（自带 id，Hugo 用 unsafe=true 原样保留）
    · 位于 <details> 等 HTML 块内的 ### 标题（Hexo 与 Hugo 都不渲染它）
  纯文本扫描 markdown 会把后者误认成标题，按数量对应就会整体错位。

幂等：已带 {#id} 的标题会在 id 一致时跳过、不一致时纠正。
"""

import os
import re
import glob
import html as html_mod

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(BASE, 'content', 'posts')
TOOLS = os.path.join(BASE, 'tools')
HEXO_PUBLIC = os.environ.get(
    'HEXO_PUBLIC',
    '/home/ystyle/Code/Nodejs/ystyle.github.io/public')

FM_RE = re.compile(r'^---\r?\n(.*?)\r?\n---\r?\n?', re.S)
TITLE_RE = re.compile(r'^title:\s*(.+?)\s*$', re.M)
ATX_RE = re.compile(r'^ {0,3}(#{1,6})\s+(.*?)\s*$')
EXIST_ID_RE = re.compile(r'\s*\{#([^}]*)\}\s*$')


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8') as f:
        f.write(t)


# 智能标点归一化：Hexo 的渲染器会把 ASCII 引号/连字符转成排版引号，
# 例如 `Let's` → `Let’s`（U+2019），导致两侧文本比对假性失败。
SMART = str.maketrans({
    '\u2019': "'", '\u2018': "'",
    '\u201c': '"', '\u201d': '"',
    '\u2013': '-', '\u2014': '-',
    '\u00a0': ' ', '\u3000': ' ',
})


def norm(s):
    """归一化标题文本，用于两侧比对"""
    s = html_mod.unescape(s)
    s = re.sub(r'<[^>]+>', '', s)      # HTML 侧：去标签
    s = re.sub(r'[`*_~]', '', s)       # markdown 侧：去强调符/反引号
    s = s.translate(SMART)             # 智能标点 → ASCII
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


# ---------- 现有站点：{(标题文本, id)} ----------
def collect_live():
    """返回 {文章标题: [(heading文本(归一化), id), ...]}"""
    out = {}
    page_title_re = re.compile(r'<h1 class="post-card-title">(.*?)</h1>', re.S)
    head_re = re.compile(r'<h([1-6])([^>]*)>(.*?)</h\1>', re.S)
    for dirpath, _dn, filenames in os.walk(HEXO_PUBLIC):
        if 'index.html' not in filenames:
            continue
        parts = os.path.relpath(dirpath, HEXO_PUBLIC).split(os.sep)
        if not (len(parts) == 4 and parts[0].isdigit()):
            continue
        text = read(os.path.join(dirpath, 'index.html'))
        pt = page_title_re.search(text)
        if not pt:
            continue
        items = []
        for m in head_re.finditer(text):
            idm = re.search(r'\bid="([^"]*)"', m.group(2))
            if idm:
                items.append((norm(m.group(3)), html_mod.unescape(idm.group(1))))
        out[html_mod.unescape(pt.group(1)).strip()] = items
    return out


# ---------- markdown：ATX 标题 ----------
def find_headings(md):
    """返回 [(行号, 级别, 标题文本, 已存在的id or None)]，跳过 front-matter 与围栏代码块"""
    fm = FM_RE.match(md)
    start = md[:fm.end()].count('\n') if fm else 0
    lines = md.split('\n')
    out, in_fence, fence, fence_len = [], False, None, 0

    for i in range(start, len(lines)):
        line = lines[i]
        # CommonMark：闭合围栏不能带 info string，且长度不短于开启者。
        # 只看首字符会把 ```shell 这种「开启」误判成「闭合」，使后续配对整体错位
        # （实测：《使用Docker快速上手鸿蒙》第 78 行的 ```shell 被当成闭合，
        #   结果第 115 行的真标题被误判进代码块、漏注入）。
        mf = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if mf:
            marker, rest = mf.group(1), mf.group(2)
            if not in_fence:
                in_fence, fence, fence_len = True, marker[0], len(marker)
            elif marker[0] == fence and len(marker) >= fence_len and rest.strip() == '':
                in_fence, fence, fence_len = False, None, 0
            continue
        if in_fence:
            continue

        m = ATX_RE.match(line)
        if not m:
            continue
        raw = m.group(2)
        existed = None
        me = EXIST_ID_RE.search(raw)
        if me:
            existed = me.group(1)
            raw = raw[:me.start()]
        raw = re.sub(r'\s*#+\s*$', '', raw)   # 闭合式尾部 #
        out.append((i, len(m.group(1)), raw.strip(), existed))
    return out


def main():
    live = collect_live()
    files = sorted(glob.glob(os.path.join(POSTS, '*.md')))

    stat = {'injected': 0, 'fixed': 0, 'kept': 0}
    unmatched, no_page = [], []
    detail = []

    for path in files:
        name = os.path.basename(path)
        md = read(path)
        t = TITLE_RE.search(md[:900])
        title = t.group(1).strip().strip('"').strip("'") if t else None
        entries = live.get(title)
        if entries is None and title:
            # 站点侧的文章标题可能被渲染成智能引号（Let's → Let’s），
            # 用原文直接查不到，回退到归一化比较。
            nt = norm(title)
            for k, v in live.items():
                if norm(k) == nt:
                    entries = v
                    break

        heads = find_headings(md)
        if entries is None:
            no_page.append(name)
            continue

        used = set()
        lines = md.split('\n')
        changed = 0

        for (ln, _lvl, txt, existed) in heads:
            key = norm(txt)
            hit = None
            for i, (ltxt, lid) in enumerate(entries):
                if i in used:
                    continue
                # 精确匹配优先；退一步允许站点侧文本以 md 标题结尾 ——
                # 有些 heading 被 Hexo 的 toc helper 重新序列化成了畸形 HTML
                # （实测：《windows-10-子系统Archlinux》里
                #   <h3 id="...">文件夹…zsh.reg">以下存为文件 -> …</h3>），
                # 其文本前多了一截，但尾部仍是原标题。
                if ltxt == key or (len(key) > 6 and ltxt.endswith(key)):
                    hit = (i, lid)
                    break
            if hit is None:
                unmatched.append((name, txt))
                continue
            used.add(hit[0])
            want = hit[1]

            if existed is not None:
                if existed == want:
                    stat['kept'] += 1
                    continue
                lines[ln] = re.sub(EXIST_ID_RE, '', lines[ln]).rstrip() + ' {#' + want + '}'
                stat['fixed'] += 1
            else:
                lines[ln] = lines[ln].rstrip() + ' {#' + want + '}'
                stat['injected'] += 1
            changed += 1

        if changed:
            write(path, '\n'.join(lines))
        detail.append('%-56s 标题%2d  改动%2d' % (name, len(heads), changed))

    rep = [
        '现有站点文章          : %d 篇' % len(live),
        '本地文章              : %d 篇' % len(files),
        '本次新注入            : %d' % stat['injected'],
        '修正了错误 id         : %d' % stat['fixed'],
        '已正确、跳过          : %d' % stat['kept'],
        '文本匹配不到（应属 HTML 块内，无需注入）: %d' % len(unmatched),
        '找不到对应站点页面的文章: %d %s' % (len(no_page), no_page[:5]),
        '',
        '--- 未匹配明细（前 30）---',
    ]
    for n, t in unmatched[:30]:
        rep.append('  %-46s %s' % (n[:46], t[:50]))
    rep += ['', '--- 逐篇 ---'] + detail
    os.makedirs(TOOLS, exist_ok=True)
    write(os.path.join(TOOLS, 'inject-report.txt'), '\n'.join(rep) + '\n')

    print('新注入 %d，修正 %d，跳过 %d' % (stat['injected'], stat['fixed'], stat['kept']))
    print('文本匹配不到 %d 条，无对应页面 %d 篇' % (len(unmatched), len(no_page)))
    for n, t in unmatched[:6]:
        print('   ? %-40s %s' % (n[:40], t[:40]))


if __name__ == '__main__':
    main()
