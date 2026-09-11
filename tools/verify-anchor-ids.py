#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段 ② 验收：逐篇对比 Hugo 生成的 heading id 与现有站点是否一致。

对比范围限定在 post-content 区域内（用 div 深度计数切出来），
避免 banner、TOC 侧栏、页脚里的 heading 干扰。

退出码 0 = 完全一致。
"""

import os
import re
import sys
import html as html_mod

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUGO_PUBLIC = os.path.join(BASE, 'public')
HEXO_PUBLIC = os.environ.get(
    'HEXO_PUBLIC',
    '/home/ystyle/Code/Nodejs/ystyle.github.io/public')

CONTENT_START_RE = re.compile(r'id="post-content"[^>]*>')
DIV_RE = re.compile(r'<(/?)div\b[^>]*>')
HEAD_RE = re.compile(r'<h([1-6])([^>]*)>')


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()


def slice_content(text):
    """切出 post-content 区域（按 div 深度配对）"""
    m = CONTENT_START_RE.search(text)
    if not m:
        return None
    start = m.end()
    depth = 1
    for t in DIV_RE.finditer(text, start):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            return text[start:t.start()]
    return text[start:]


def ids_of(text):
    """返回 [(level, id 或 None)]"""
    zone = slice_content(text)
    if zone is None:
        return None
    out = []
    for m in HEAD_RE.finditer(zone):
        idm = re.search(r'\bid="([^"]*)"', m.group(2))
        out.append((int(m.group(1)), html_mod.unescape(idm.group(1)) if idm else None))
    return out


def article_urls(root):
    urls = set()
    for dirpath, _dn, filenames in os.walk(root):
        if 'index.html' not in filenames:
            continue
        parts = os.path.relpath(dirpath, root).split(os.sep)
        if len(parts) == 4 and parts[0].isdigit():
            urls.add('/'.join(parts))
    return urls


def main():
    hexo_urls = article_urls(HEXO_PUBLIC)
    hugo_urls = article_urls(HUGO_PUBLIC)

    only_hexo = hexo_urls - hugo_urls
    if only_hexo:
        print('!! Hugo 缺少文章页 %d 个: %s' % (len(only_hexo), sorted(only_hexo)[:5]))

    same = diff = no_id_h = no_id_u = 0
    problems = []

    for u in sorted(hexo_urls & hugo_urls):
        h = ids_of(read(os.path.join(HEXO_PUBLIC, u, 'index.html')))
        g = ids_of(read(os.path.join(HUGO_PUBLIC, u, 'index.html')))
        if h is None or g is None:
            problems.append((u, 'post-content 区域未找到', h is not None, g is not None))
            continue

        hl = [x[1] for x in h]
        gl = [x[1] for x in g]

        # 只比较两边都带 id 的（Hugo 的裸 HTML 标题同样不带 id）
        if hl == gl:
            same += 1
        else:
            # 统计无 id 的情况
            hn = sum(1 for x in hl if x is None)
            gn = sum(1 for x in gl if x is None)
            if hn != gn:
                if hn == 0 and gn > 0:
                    no_id_u += 1
                elif gn == 0 and hn > 0:
                    no_id_h += 1
            diff += 1
            if len(problems) < 12:
                problems.append((u, 'id 列表不一致', hl[:6], gl[:6]))

    total = len(hexo_urls & hugo_urls)
    print('=' * 66)
    print('heading id 逐篇比对（post-content 区域内）')
    print('=' * 66)
    print('  比对文章数    : %d' % total)
    print('  完全一致      : %d' % same)
    print('  不一致        : %d' % diff)
    print('    · 仅站点有 id: %d' % no_id_h)
    print('    · 仅 Hugo 有 id: %d' % no_id_u)
    print()
    for p in problems:
        print('  ! %s' % (p[0],))
        print('      %s' % (p[1],))
        if len(p) == 4 and isinstance(p[2], list):
            print('      站点: %s' % (p[2],))
            print('      Hugo: %s' % (p[3],))
        elif len(p) == 4:
            print('      站点有区域=%s  Hugo有区域=%s' % (p[2], p[3]))

    return 0 if (diff == 0 and not only_hexo) else 1


if __name__ == '__main__':
    sys.exit(main())
