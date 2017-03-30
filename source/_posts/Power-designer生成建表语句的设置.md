---
title: Power designer生成建表语句的设置
permalink: power-designersheng-cheng-jian-biao-yu-ju-de-she-zhi
id: 42
updated: '2016-12-14 12:16:50'
date: 2016-12-12 18:46:13
tags: 建模
categories: 编程
---

### oracle去年字段的引号
DataBase - Edit Current DBMS

修改 `ORA11GR1::Script\Sql\Format\CaseSensitivityUsingQuote`改为`No`

### oracle生成的字段注释不换行
DataBase - Edit Current DBMS

修改`ORA11GR1::Script\Objects\Column\ColumnComment` 的值为 `comment on column [%QUALIFIER%]%TABLE%.%COLUMN% is %.q:COMMENT%`

### oracle生成的表名注释不换行
DataBase - Edit Current DBMS

修改`ORA11GR1::Script\Objects\Table\TableComment` 的值为`comment on table [%QUALIFIER%]%TABLE% is %.q:COMMENT%`

### mysql生成的字段去掉national
修改`MYSQL50::Script\Objects\Column\Add` 去掉值里的` [%National%?national ]`
