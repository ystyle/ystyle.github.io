#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
给标签页补 alias，让 Hexo 那些「大小写变体」URL 重定向到 Hugo 合并后的页面。

背景：
  原站把 Cangjie / cangjie、Docker / docker、GIT / git 这类大小写不同的写法
  当成了**两个独立标签**，各有一个页面（共 13 组）。Hugo 的 taxonomy 大小写
  不敏感，会合并成一个 —— 这本身是改进，但会让另一半 URL 变成 404。

做法：
  对比两侧实际生成的 /tags/<term>/ 目录，对「仅 Hexo 有」的那些，
  在 Hugo 对应 term 的 content/tags/<term>/_index.md 里写 aliases，
  Hugo 便会生成跳转页（meta refresh + canonical）。

幂等：重复运行会合并 aliases 而不是覆盖。
"""

import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUGO_PUBLIC = os.path.join(BASE, 'public')
HEXO_PUBLIC = os.environ.get(
    'HEXO_PUBLIC',
    '/home/ystyle/Code/Nodejs/ystyle.github.io/public')
CONTENT_TAGS = os.path.join(BASE, 'content', 'tags')


def terms(root, taxonomy):
    d = os.path.join(root, taxonomy)
    if not os.path.isdir(d):
        return set()
    return {n for n in os.listdir(d)
            if os.path.isdir(os.path.join(d, n)) and n != 'page'}


def main():
    hexo = terms(HEXO_PUBLIC, 'tags')
    hugo = terms(HUGO_PUBLIC, 'tags')

    missing = sorted(hexo - hugo)
    plan = {}      # hugo term -> [需要重定向过来的 hexo 变体]
    unresolved = []

    for m in missing:
        cand = [h for h in hugo if h.lower() == m.lower()]
        if cand:
            plan.setdefault(cand[0], []).append(m)
        else:
            unresolved.append(m)

    written = 0
    for target, sources in sorted(plan.items()):
        path = os.path.join(CONTENT_TAGS, target, '_index.md')
        aliases = ['/tags/%s/' % s for s in sorted(sources)]

        existing = ''
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                existing = f.read()

        # 合并已有 aliases（幂等）
        old = set(re.findall(r'^\s*-\s*(\S+)\s*$', existing, re.M))
        merged = sorted(old | set(aliases))

        out = ['---', 'title: "%s"' % target, 'aliases:']
        out += ['  - %s' % a for a in merged]
        out += ['---', '']
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(out))
        written += 1
        print('  %-18s <- %s' % (target, ', '.join(sources)))

    print()
    print('Hexo 标签 %d 个 / Hugo 标签 %d 个' % (len(hexo), len(hugo)))
    print('仅 Hexo 有（大小写变体）: %d' % len(missing))
    print('已写 alias 的 term 文件: %d' % written)
    if unresolved:
        print('无法对应（需人工看）: %d %s' % (len(unresolved), unresolved[:5]))


if __name__ == '__main__':
    main()
