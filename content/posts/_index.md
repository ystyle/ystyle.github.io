---
title: 文章
# Hexo 没有 /posts/ 这个列表页，而 Hugo 会为每个 section 自动生成一个
# （还会带上 /posts/page/2/ … 共 10 个分页）。关掉该 section 自身的渲染与列表收录；
# 文章页面本身不受影响。
#
# ⚠️ 键名是 build 而不是 _build —— 后者在 Hugo 0.145 已弃用并移除。
# ⚠️ tools/convert.py 会清空 content/posts/*.md 后重建，已特意跳过本文件；
#    若哪天它又不见了，就是这个跳过逻辑被改坏了。
build:
  render: false
  list: false
---
