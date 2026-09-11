#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逐篇比对 Hugo 与原站的正文 HTML（#post-content 区域），找出渲染差异。

为什么要先屏蔽代码块和图片：
  · 代码高亮：Hexo 用 highlight.js 生成 <figure class="highlight"><table>…，
    Hugo 用 Chroma 生成 <div class="highlight"><pre style="…">…，结构天生不同，
    会把其他差异淹没。
  · 图片：原站主题会把图片包进 <figure class="image-bubble"> 做 lightbox，
    Hugo 目前输出裸 <img>。
  这两类先替换成占位符，剩下的差异才是真正值得看的渲染问题。

模式：
  --strict 不做任何屏蔽/归一化，纯字符比对（用于看总量）
  默认     屏蔽代码块/图片 + 归一化空白后比对
"""

import os
import re
import sys
import html as html_mod
import difflib

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUGO_PUBLIC = os.path.join(BASE, 'public')
HEXO_PUBLIC = os.environ.get(
    'HEXO_PUBLIC',
    '/home/ystyle/Code/Nodejs/ystyle.github.io/public')

CONTENT_START = re.compile(r'id="post-content"[^>]*>')
DIV_RE = re.compile(r'<(/?)div\b[^>]*>')

CODE_PATTERNS = [
    re.compile(r'<figure class="highlight.*?</figure>', re.S),
    re.compile(r'<div class="highlight">.*?</div>\s*</div>', re.S),
    re.compile(r'<div class="highlight">.*?</div>', re.S),
    # Chroma 有时直接输出裸 <pre>（例如围栏外或 hook 之外的情况）
    re.compile(r'<pre[^>]*>.*?</pre>', re.S),
]
IMG_PATTERNS = [
    re.compile(r'<figure class="image-bubble">.*?</figure>', re.S),
    re.compile(r'<img[^>]*>'),
]


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()


def slice_content(text):
    """切出 #post-content 区域（按 div 深度配对）"""
    m = CONTENT_START.search(text)
    if not m:
        return None
    start = m.end()
    depth = 1
    for t in DIV_RE.finditer(text, start):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            return text[start:t.start()]
    return text[start:]


def mask(s):
    for p in CODE_PATTERNS:
        s = p.sub('[CODE]', s)
    for p in IMG_PATTERNS:
        s = p.sub('[IMG]', s)
    return s


def norm(s):
    s = mask(s)
    s = re.sub(r'\s+', ' ', s)
    # 忽略「标签边界空白」：Hexo 输出 </h3><ol>，Hugo 输出 </h3>\n<ol>，
    # 归一化后会多出一个空格，浏览器渲染毫无区别，属于格式噪声。
    s = re.sub(r'>\s+', '>', s)
    s = re.sub(r'\s+<', '<', s)
    s = re.sub(r'<br\s*/?>', '<br>', s)
    return s.strip()


def article_urls(root):
    out = set()
    for dirpath, _dn, filenames in os.walk(root):
        if 'index.html' not in filenames:
            continue
        parts = os.path.relpath(dirpath, root).split(os.sep)
        if len(parts) == 4 and parts[0].isdigit():
            out.add('/'.join(parts))
    return out


def main():
    strict = '--strict' in sys.argv
    urls = sorted(article_urls(HEXO_PUBLIC) & article_urls(HUGO_PUBLIC))

    same = diff = missing = 0
    diffs = []

    for u in urls:
        a = slice_content(read(os.path.join(HEXO_PUBLIC, u, 'index.html')))
        b = slice_content(read(os.path.join(HUGO_PUBLIC, u, 'index.html')))
        if a is None or b is None:
            missing += 1
            continue
        na, nb = (a, b) if strict else (norm(a), norm(b))
        if na == nb:
            same += 1
        else:
            diff += 1
            diffs.append((u, na, nb))

    print('=' * 70)
    print('正文 HTML 逐篇比对  %s' % ('【严格模式】' if strict else '【屏蔽代码块/图片 + 归一化空白】'))
    print('=' * 70)
    print('  比对文章数  : %d' % len(urls))
    print('  完全一致    : %d' % same)
    print('  有差异      : %d' % diff)
    print('  区域未找到  : %d' % missing)
    print()

    if diffs:
        print('=' * 70)
        print('差异样例（前 6 篇，展示首个不同片段）')
        print('=' * 70)
        for u, na, nb in diffs[:6]:
            print('\n--- %s' % u)
            sm = difflib.SequenceMatcher(None, na, nb)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag == 'equal':
                    continue
                print('    %-8s 站点: %r' % (tag, na[max(0, i1 - 40):i2 + 40][:160]))
                print('    %-8s Hugo: %r' % ('', nb[max(0, j1 - 40):j2 + 40][:160]))
                break

    print()
    print('  差异篇目清单:')
    for u, _a, _b in diffs[:40]:
        print('    ', u)
    if len(diffs) > 40:
        print('     … 另有 %d 篇' % (len(diffs) - 40))

    return 0 if diff == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
