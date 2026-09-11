#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移 Hexo 的独立页面（非 _posts）到 Hugo。

对应关系：
  source/friends/index.md     -> content/friends/index.md     （普通页面，URL /friends/）
  source/categories/index.md  -> content/categories/_index.md （taxonomy 列表页，只需标题）
  source/tags/index.md        -> content/tags/_index.md       （taxonomy 列表页，只需标题）
  source/404.md               -> 不生成 content 文件；由 layouts/404.html 承载
                                 （原页面 layout:false，是整页自定义 HTML，模板里已复刻）
  source/_drafts/**           -> 跳过（草稿，Hexo 的 render_drafts: false）
  source/README.md            -> 跳过（Hexo 的 skip_render: README.md）

与 convert.py 一样采用「逐行正则改写」而非 YAML 重序列化，避免格式漂移。
"""

import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Hexo 源仓库与本项目是兄弟目录（不再是父目录），显式配置，可用环境变量覆盖
REPO = os.environ.get('HEXO_REPO', '/home/ystyle/Code/Nodejs/ystyle.github.io')
SRC = os.path.join(REPO, 'source')
DST = os.path.join(BASE, 'content')

FM_RE = re.compile(r'^---\r?\n(.*?)\r?\n---\r?\n?', re.S)
DATE_LINE_RE = re.compile(r'^(date|updated):\s*(.*)$', re.M)

# (源文件, 目标文件, 是否只取 front-matter)
MAP = [
    ('friends/index.md',    'friends/index.md',    False),
    ('categories/index.md', 'categories/_index.md', True),
    ('tags/index.md',       'tags/_index.md',       True),
]


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()


def write(p, t):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(t)


def fix_dates(fm):
    """YYYY-M-D → YYYY-MM-DD（Hugo 对日期格式严格）"""
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


def main():
    done = []
    for src_rel, dst_rel, fm_only in MAP:
        src = os.path.join(SRC, src_rel)
        if not os.path.exists(src):
            print('  跳过（源文件不存在）:', src_rel)
            continue

        text = read(src)
        m = FM_RE.match(text)
        if not m:
            print('  跳过（无 front-matter）:', src_rel)
            continue

        fm = fix_dates(m.group(1)).rstrip()
        body = '' if fm_only else '\n' + text[m.end():].lstrip('\n')
        out = '---\n' + fm + '\n---\n' + body

        write(os.path.join(DST, dst_rel), out)
        done.append('%s  ->  content/%s%s' % (src_rel, dst_rel, '  （仅标题）' if fm_only else ''))

    print('已迁移页面 %d 个:' % len(done))
    for d in done:
        print('  ', d)
    print()
    print('未迁移（有意）:')
    print('   source/404.md        -> layouts/404.html（整页自定义 HTML，模板承载）')
    print('   source/_drafts/**    -> 草稿，不发布')
    print('   source/README.md     -> Hexo skip_render')


if __name__ == '__main__':
    main()
