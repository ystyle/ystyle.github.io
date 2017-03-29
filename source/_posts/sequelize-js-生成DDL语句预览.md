---
title: sequelize.js 生成DDL语句预览
permalink: sequelize-js-sheng-cheng-ddlyu-ju-yu-lan
id: 41
updated: '2016-11-30 17:29:45'
date: 2016-11-27 14:26:26
tags:
  - Nodejs
  - sequelize
---

>因为想做一个直接生成建表语句的工具。 又不想连接到数据库(懒得让数据库一直启动着)
看了下sequelize.js的测试代码， 找到了以下方法可以实现

```javascript
var Sequelize = require('sequelize');
// 因为没有连接到数据库， 用户名什么的可以随意写
var sequelize = new Sequelize('test', 'root', 'root', {
    dialect: "mysql"
});

var User = sequelize.define('User', {
    username: Sequelize.STRING,
    password: Sequelize.STRING
});

var sql = sequelize.dialect.QueryGenerator;

var ddlsql = sql.createTableQuery(User.getTableName(), sql.attributesToSQL(User.rawAttributes), { });

console.log(ddlsql);
```

生成DDL建表语句
```shell
$ node test.js
CREATE TABLE IF NOT EXISTS `Users` (`id` INTEGER NOT NULL auto_increment , `username` VARCHAR(255), `password` VARCHAR
(255), `createdAt` DATETIME NOT NULL, `updatedAt` DATETIME NOT NULL, PRIMARY KEY (`id`)) ENGINE=InnoDB;
```
