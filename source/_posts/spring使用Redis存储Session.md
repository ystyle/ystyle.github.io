---
title: spring使用Redis存储Session
tags:
  - JAVA
  - redis
categories: 编程
permalink: springshi-yong-rediscun-chu-session
id: 26
updated: '2015-10-29 23:49:37'
date: 2015-10-29 22:46:05
---

## spring使用Redis存储Session

### 准备
spring web的maven项目

### 配置

pom.xml添加依赖

```xml
<!-- pom.xml -->
<dependency>
    <groupId>org.springframework.session</groupId>
    <artifactId>spring-session</artifactId>
    <version>1.0.2.RELEASE</version>
</dependency>
<dependency>
    <groupId>org.springframework.data</groupId>
    <artifactId>spring-data-redis</artifactId>
    <version>1.4.1.RELEASE</version>
</dependency>
<dependency>
    <groupId>redis.clients</groupId>
    <artifactId>jedis</artifactId>
    <version>2.5.2</version>
</dependency>
```

web.xml 添加过滤器

```xml
<!-- web.xml -->
<filter>
    <filter-name>springSessionRepositoryFilter</filter-name>
    <filter-class>org.springframework.web.filter.DelegatingFilterProxy</filter-class>
</filter>
<filter-mapping>
    <filter-name>springSessionRepositoryFilter</filter-name>
    <url-pattern>/*</url-pattern>
</filter-mapping>
```

spring 配置文件添加redis配置

```xml

<context:annotation-config/><!-- 自动扫描必需 -->
<bean class="org.springframework.session.data.redis.config.annotation.web.http.RedisHttpSessionConfiguration"/>
<bean class="org.springframework.data.redis.connection.jedis.JedisConnectionFactory">
    <!-- redis 配置 -->
    <property name="hostName" value="localhost"/>
    <property name="port" value="6379"/>
</bean>
```

### 使用

```java
@ResponseBody
@RequestMapping("/get")
public String index(Model model,HttpServletRequest request,String action,String msg,String key){
    HttpSession session=request.getSession();
    String message = "ok";
    if ("set".equals(action)){
        session.setAttribute(key, msg);
    }else if ("get".equals(action)){
        message=(String)session.getAttribute(key);
    }
    return message;
}
```
