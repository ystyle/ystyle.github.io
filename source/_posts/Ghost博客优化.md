---
title: Ghost博客优化
tags:
  - Ghost
categories: 编程
permalink: ghostbo-ke-you-hua
id: 9
updated: '2015-06-24 14:52:35'
date: 2015-06-21 10:00:45
---

###修改标题不显示页数

文件名:`node_modules/ghost/core/server/helpers/meta_title.js`

```javascript
//    if (pagination && pagination.total > 1) {
//        pageString = ' - Page ' + pagination.page;
//    }
```

###修改时区与汉化时间显示
到openshift的源码目录，安装`moment-timezone`模块：

```shell
cd ${OPENSHIFT_REPO_DIR}/
npm install moment-timezone --save
```
文件名`node_modules/ghost/core/server/helpers/date.js`
```javascript
var moment          = require('moment-timezone'),
    date;
moment.locale('zh-cn');
moment.tz.setDefault("Asia/Shanghai");
```
