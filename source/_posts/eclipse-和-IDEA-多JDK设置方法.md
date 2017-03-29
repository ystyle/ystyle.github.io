---
title: eclipse 和 IDEA 多JDK设置方法
tags: JAVA
categories: 编程
permalink: eclipse-he-idea-duo-jdkshe-zhi-fang-fa
id: 19
updated: '2015-09-24 18:10:02'
date: 2015-09-19 19:48:45
---

##  eclipse 和 IDEA 多JDK设置方法

1. [eclipse](#1)
   * [已有项目切换JDK](#11)
2. [Intellij IDEA](#2)
   * [已有项目切换JDK](#21)

<h3 id="1">eclipse</h3>
>打开设置 `window - preferences - java - installed jres - add` 把需要的JDK全放里边

![](/images/2015/09/----20150919212931.png)

>新建项目时用 `Use a preject specific JRE` 随便选择就行了

![](/images/2015/09/----20150919213005.png)

<h3 id="11">eclipse已有项目切换JDK</h3>
右键项目`properties - java build path - libraries`选中JDK然后`edit` 切换JDK `finish`就行了

![](/images/2015/09/----20150919213745.png)

<h3 id="2">Intellij IDEA</h3>
新建项目时直接new一个新的JDK

![](/images/2015/09/----20150919213249.png)

选择JDK目录

![](/images/2015/09/----20150919213308.png)

要什么版本的自己选择

![](/images/2015/09/----20150919213236.png)

<h3 id="21">Intellij IDEA已有项目切换JDK</h3>

右边或`ctrl + shift + alt + s` 直接切

![](/images/2015/09/----20150919213900.png)
