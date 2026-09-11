#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hexo → Hugo 内容转换（阶段 ①：只保证「内容 + URL」与现有站点一致）

做三件事：
  1. 从现有 public/ 反推出 96 篇文章的**真实 URL**，作为比对基准
     （不能信 front-matter 里的 permalink —— Hexo 把它当 slug 用，
      真正的路径是全局 permalink 模式 :year/:month/:day/:title/ 代入后的结果）
  2. 把 source/_posts/*.md 的 front-matter 做字段映射，写入 content/posts/
       permalink: → slug:        （Hugo 的 :slug 与 Hexo 的 :title 令牌语义一致）
       updated:   → lastmod:     （Hugo 对应字段）
       其余字段原样保留
  3. 输出 expected-urls.txt（基准清单）和 convert-report.txt（转换报告）

刻意采用「逐行正则改写」而不是 YAML 解析后重新序列化：
后者会改变引号风格与列表缩进，制造大量无意义的 diff。
"""

import os
import re
import glob
import html

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 本项目根目录
# Hexo 源仓库与本项目是兄弟目录（不再是父目录），显式配置，可用环境变量覆盖
REPO = os.environ.get('HEXO_REPO', '/home/ystyle/Code/Nodejs/ystyle.github.io')
SRC_DIR = os.path.join(REPO, 'source', '_posts')
PUB_DIR = os.path.join(REPO, 'public')
DST_DIR = os.path.join(BASE, 'content', 'posts')
TOOLS_DIR = os.path.join(BASE, 'tools')


def read(path):
    with open(path, encoding='utf-8', errors='replace') as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


# ---------- 1) 从已生成的站点反推真实 URL ----------
def collect_live_urls():
    """返回 {文章标题: 现有URL}"""
    out = {}
    title_re = re.compile(r'<h1 class="post-card-title">(.*?)</h1>', re.S)
    for dirpath, _dirnames, filenames in os.walk(PUB_DIR):
        if 'index.html' not in filenames:
            continue
        rel = os.path.relpath(dirpath, PUB_DIR)
        parts = rel.split(os.sep)
        if len(parts) == 4 and parts[0].isdigit():
            text = read(os.path.join(dirpath, 'index.html'))
            m = title_re.search(text)
            if m:
                out[html.unescape(m.group(1)).strip()] = '/' + rel.replace(os.sep, '/') + '/'
    return out


# ---------- 2) front-matter 字段映射 ----------
FM_RE = re.compile(r'^---\r?\n(.*?)\r?\n---\r?\n?', re.S)
DATE_LINE_RE = re.compile(r'^(date|updated):\s*(.*)$', re.M)


def fix_dates(fm):
    """把 YYYY-M-D 归一化成 YYYY-MM-DD。

    Hexo 用 moment 解析，能容忍 `2020-08-6 15:08:26`；Hugo 要求严格格式，
    否则报 "not a parsable date" 并让该页渲染失败（实测全站只有 1 篇命中）。
    """
    def repl(m):
        key, raw = m.group(1), m.group(2).rstrip()
        quote, val = '', raw
        if len(raw) >= 2 and raw[0] in ('"', "'") and raw[-1] == raw[0]:
            quote, val = raw[0], raw[1:-1]
        mm = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})(.*)$', val)
        if mm:
            val = '%s-%02d-%02d%s' % (mm.group(1), int(mm.group(2)),
                                      int(mm.group(3)), mm.group(4))
        return '%s: %s%s%s' % (key, quote, val, quote)

    return DATE_LINE_RE.sub(repl, fm)


def convert(text):
    """返回 (新文本, 状态) —— 状态用于统计"""
    m = FM_RE.match(text)
    if not m:
        return text, 'no-front-matter'

    fm, body = m.group(1), text[m.end():]
    fm = fix_dates(fm)
    status = []

    if re.search(r'^permalink:', fm, re.M):
        fm = re.sub(r'^permalink:', 'slug:', fm, count=1, flags=re.M)
        status.append('permalink->slug')

    if re.search(r'^updated:', fm, re.M):
        fm = re.sub(r'^updated:', 'lastmod:', fm, count=1, flags=re.M)
        status.append('updated->lastmod')

    has_slug = bool(re.search(r'^slug:', fm, re.M))
    if not has_slug:
        status.append('no-slug(靠文件名)')

    return '---\n' + fm + '\n---\n' + body, ','.join(status) if status else 'unchanged'


def main():
    live = collect_live_urls()
    os.makedirs(TOOLS_DIR, exist_ok=True)
    write(os.path.join(TOOLS_DIR, 'expected-urls.txt'),
          '\n'.join(sorted(live.values())) + '\n')

    srcs = sorted(glob.glob(os.path.join(SRC_DIR, '*.md')))
    if os.path.isdir(DST_DIR):
        for f in glob.glob(os.path.join(DST_DIR, '*.md')):
            os.remove(f)
    os.makedirs(DST_DIR, exist_ok=True)

    report = []
    stats = {}
    for src in srcs:
        name = os.path.basename(src)
        new_text, status = convert(read(src))
        write(os.path.join(DST_DIR, name), new_text)
        stats[status] = stats.get(status, 0) + 1
        report.append('%-58s %s' % (name, status))

    lines = [
        '基准（从 public/ 反推的现有 URL）: %d 条' % len(live),
        '源文章                            : %d 篇' % len(srcs),
        '',
        '--- 字段映射统计 ---',
    ]
    for k in sorted(stats):
        lines.append('  %-22s %d' % (k, stats[k]))
    lines += ['', '--- 逐篇明细 ---'] + report

    write(os.path.join(TOOLS_DIR, 'convert-report.txt'), '\n'.join(lines) + '\n')

    print('基准 URL  : %d 条' % len(live))
    print('已转换    : %d 篇' % len(srcs))
    for k in sorted(stats):
        print('  %-22s %d' % (k, stats[k]))


if __name__ == '__main__':
    main()
