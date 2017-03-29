---
title: Webpack 项目中使用fetch.js
tags:
  - nodejs
  - webpack
  - fetch
categories: 编程
permalink: webpack-xiang-mu-zhong-shi-yong-fetch-js
id: 28
updated: '2016-02-22 17:58:49'
date: 2016-02-01 11:36:09
---

### 安装依赖
```shell
npm i imports-loader exports-loader --save-dev
npm i whatwg-fetch --save
```

### 方法一: webpack配置

修改`webpack.config.js` 文件
```javascript
 plugins: [
        new webpack.ProvidePlugin({
            'fetch': 'imports?this=>global!exports?global.fetch!whatwg-fetch'
        }),
    ],
```

### 方法二: import
在需要使用的文件中import
```javascript
import 'imports?this=>global!exports?global.fetch!whatwg-fetch';
```
