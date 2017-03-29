---
title: maven deploy 部署jar到私服
tags:
  - Maven
  - Nexus
  - Deploy
categories: 系统
permalink: maven-deploy-bu-shu-jardao-si-fu
id: 40
updated: '2016-11-21 18:53:04'
date: 2016-10-27 17:11:51
---

### 修改maven settings.xml文件
```xml
<servers>  
    <server>    
        <id>private-nexus-library-releases</id>    
        <username>username</username>    
        <password>password</password>    
        <!---nexus私服的用户名和密码 ---->
    </server>  
    <server>  
        <id>private-nexus-library-snapshots</id>  
        <username>username</username>    
        <password>password</password>    
    </server>  
</servers>  
```

### 修改项目pom文件
```xml
<!--发布-->  
<distributionManagement>  
    <repository>  
        <id>private-nexus-library-releases</id>  
        <name>private-nexus-library-releases</name>  
        <url>http://host:port/maven-web/repositories/releases/</url>  
        <!--- url可以在nexus私服repositories列表看到 ---->
    </repository>    
    <snapshotRepository>  
        <id>private-nexus-library-snapshots</id>  
        <name>private-nexus-library-snapshots</name>  
        <url>http://host:port/maven-web/repositories/snapshots/</url>  
    </snapshotRepository>  
</distributionManagement>
```

### 注意事项
1. server 的 id 要与 repository 的 id 保持一致。
2. nexus私用不能解析`parent.version` 中的`${}`表达式, 要写常量. 否则会导致deploy失败.
