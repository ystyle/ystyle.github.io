#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL 逐条比对：Hexo 现有站点(../public) vs Hugo 新站(./public)

按路径类型分类统计，重点看「文章页」是否 100% 对齐；
归档/分类/标签/分页的缺失另行列出（这些属于已知需要自己写的部分）。
"""

import os
import re
import sys
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # 本项目根目录
HUGO = os.path.join(BASE, 'public')

# Hexo 源站的 public/ 基准目录。
# 本项目搬离 Hexo 仓库后，相对路径不再成立，所以用绝对路径 + 环境变量覆盖：
#   HEXO_PUBLIC=/path/to/ystyle.github.io/public python3 tools/compare-urls.py
HEXO = os.environ.get(
    'HEXO_PUBLIC',
    '/home/ystyle/Code/Nodejs/ystyle.github.io/public')

ARTICLE_RE = re.compile(r'^/\d{4}/\d{2}/\d{2}/[^/]+/$')


def collect(root):
    """返回该站点所有 HTML 的 URL 集合"""
    urls = set()
    for dirpath, _dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        prefix = '' if rel == '.' else '/' + rel.replace(os.sep, '/')
        if 'index.html' in filenames:
            urls.add(prefix + '/' if prefix else '/')
        for f in filenames:
            if f.endswith('.html') and f != 'index.html':
                urls.add(prefix + '/' + f)
    return urls


def kind(u):
    if ARTICLE_RE.match(u):
        return '文章页'
    for k, p in (('归档页', '/archives'), ('分类页', '/categories'),
                 ('标签页', '/tags'), ('分页', '/page/')):
        if u.startswith(p):
            return k
    if u == '/':
        return '首页'
    return '其他'


def main():
    hexo = collect(HEXO)
    hugo = collect(HUGO)

    ha = {u for u in hexo if kind(u) == '文章页'}
    ua = {u for u in hugo if kind(u) == '文章页'}

    print('=' * 68)
    print('文章页比对（stage ① 的核心目标）')
    print('=' * 68)
    print('  Hexo  : %d' % len(ha))
    print('  Hugo  : %d' % len(ua))
    missing = sorted(ha - ua)
    extra = sorted(ua - ha)
    print('  缺失  : %d' % len(missing))
    print('  新增  : %d' % len(extra))
    for u in missing[:15]:
        print('     - 缺失 %s' % u)
    for u in extra[:15]:
        print('     + 新增 %s' % u)
    print()
    print('  >>> 文章页一致性: %s (%d/%d)' % (
        'PASS' if not missing and not extra else 'FAIL',
        len(ha & ua), len(ha)))

    print()
    print('=' * 68)
    print('全站路径分类对比')
    print('=' * 68)
    ch, cu = Counter(kind(u) for u in hexo), Counter(kind(u) for u in hugo)
    print('  %-8s %8s %8s' % ('类型', 'Hexo', 'Hugo'))
    for k in sorted(set(ch) | set(cu)):
        print('  %-8s %8d %8d' % (k, ch.get(k, 0), cu.get(k, 0)))

    print()
    print('=' * 68)
    print('非文章页的具体差异（前 20 条）')
    print('=' * 68)
    hn = {u for u in hexo if kind(u) != '文章页'}
    un = {u for u in hugo if kind(u) != '文章页'}
    for u in sorted(hn - un)[:20]:
        print('     - 仅 Hexo 有 %s' % u)
    for u in sorted(un - hn)[:10]:
        print('     + 仅 Hugo 有 %s' % u)

    # 文章页一致只是底线；页面结构补齐后，全站也要求一致
    full_ok = not (hexo - hugo) and not (hugo - hexo)
    print()
    print('=' * 68)
    print('全站 %d 个路径一致性: %s' % (len(hexo), 'PASS' if full_ok else 'FAIL'))
    print('=' * 68)

    return 0 if (not missing and not extra and full_ok) else 1


if __name__ == '__main__':
    sys.exit(main())
