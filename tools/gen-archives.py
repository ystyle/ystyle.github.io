#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 Hugo 的年月归档页结构，对应 Hexo 的
  /archives/                （总归档，按 per_page=10 分页）
  /archives/YYYY/           （年归档）
  /archives/YYYY/MM/        （月归档）

Hugo 没有内置「按年月归档」，做法是在 content/archives/ 下生成嵌套的 _index.md
（branch bundle），每个文件在 front-matter 里标注 year / month，
再由 layouts/archives/list.html 据此筛选文章并分页。

幂等：可重复运行（会覆盖自己生成的 _index.md）。
"""

import os
import re
import glob

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(BASE, 'content', 'posts')
ARCH = os.path.join(BASE, 'content', 'archives')

FM_RE = re.compile(r'^---\r?\n(.*?)\r?\n---', re.S)
DATE_RE = re.compile(r'^date:\s*[\'"]?(\d{4})-(\d{2})', re.M)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()


def write(p, t):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(t)


def main():
    years, months, n = set(), set(), 0
    for f in glob.glob(os.path.join(POSTS, '*.md')):
        m = FM_RE.match(read(f))
        if not m:
            continue
        d = DATE_RE.search(m.group(1))
        if not d:
            continue
        y, mo = d.group(1), d.group(2)
        years.add(y)
        months.add((y, mo))
        n += 1

    write(os.path.join(ARCH, '_index.md'),
          '---\ntitle: "归档"\n---\n')
    for y in sorted(years):
        write(os.path.join(ARCH, y, '_index.md'),
              '---\ntitle: "%s"\nyear: %s\n---\n' % (y, y))
    for y, mo in sorted(months):
        # month 必须写成不带前导零的整数：Go template 的 int 转换会把 "09" 当八进制，
        # 报 strconv.ParseInt: parsing "09": invalid syntax。
        write(os.path.join(ARCH, y, mo, '_index.md'),
              '---\ntitle: "%s-%s"\nyear: %s\nmonth: %d\n---\n' % (y, mo, y, int(mo)))

    print('文章 %d 篇 → 年份 %d 个，年月 %d 个' % (n, len(years), len(months)))
    print('生成 _index.md 共 %d 个' % (1 + len(years) + len(months)))


if __name__ == '__main__':
    main()
