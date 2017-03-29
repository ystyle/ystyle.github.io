---
title: Ghost-flat主题优化
tags:
  - Ghost
categories: 编程
permalink: ghost-flatzhu-ti-you-hua
id: 10
updated: '2015-06-21 23:11:15'
date: 2015-06-21 10:51:05
---

###图片自适应(包括手机上)
文件名`assets/css/app.css`
```css
section.posts  img {
    max-width: 100%;
    height: auto;
    width: auto\9;
}
```

###文章里的链接新页面打开
文件名`assets/js/ghost-blog.js
```javascript
// 放19行后面
$('section.posts a[href^="http"]').each(function(){
      $(this).attr('target', '_blank');
});
```

###多说评论
