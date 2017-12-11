---
title: oracle生成随机数
date: 2017-12-07 09:53:53
tags:
  - oracle
  - 随机数
categories: 编程
permalink: oracle-generate-random-numbers
---

1. 小数( 0 ~ 1)
  ```sql
  select dbms_random.value from dual;
  ```
2. 指定范围内的小数 ( 0 ~ 100 )
  ```sql
  select dbms_random.value(0,100) from dual;
  ```
3. 指定范围内的整数 ( 0 ~ 100 )
  ```sql
  select trunc(dbms_random.value(0,100)) from dual;
  ```
4. 长度为20的随机数字串
  ```sql
  select substr(cast(dbms_random.value as varchar2(38)),3,20) from dual;
  ```
5. 正态分布的随机数
  ```sql
  select dbms_random.normal from dual;
  ```
6. 随机字符串
  ```sql
  select dbms_random.string(opt, length) from dual;
  ```
  -  opt可取值如下：
  -  'u','U'    :    大写字母
  -  'l','L'    :    小写字母
  -  'a','A'    :    大、小写字母
  -  'x','X'    :    数字、大写字母
  -  'p','P'    :    可打印字符
7. 随机日期
  ```sql
  select to_date(2454084+TRUNC(DBMS_RANDOM.VALUE(0,365)),'J') from dual
  -- 通过下面的语句获得指定日期的基数
  select to_char(sysdate,'J') from dual;
  ```
8. 生成GUID
  ```sql
  select sys_guid() from dual;
  ```
