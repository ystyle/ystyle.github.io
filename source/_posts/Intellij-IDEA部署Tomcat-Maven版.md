---
title: 'Intellij IDEA部署Tomcat[Maven版]'
tags:
  - JAVA
  - IDEA
categories: 系统
permalink: intellij-ideabu-shu-tomcat
id: 20
updated: '2015-09-24 18:09:11'
date: 2015-09-19 12:42:24
---

## Intellij IDEA部署Tomcat[Maven版]

### 准备

1. IDEA的`Maven`项目

1. Tomcat  

### 部署

点运行旁边的下拉框，选择`Edit Configurations... `

![](/images/2015/09/----20150920012529.png)

在窗体左边点`+`加号 选择`Tomcat Server - Local`

![](/images/2015/09/----20150920012545.png)

如果还没有配置好Tomcat,点`Configure...`按钮 ，点 左边的`+`加号添加Tomcat，在`Tomcat Home`选择Tomcat的安装位置，然后`OK`完成配置 ，不需要填其它的了

![](/images/2015/09/----20150920012633.png)

然后选择Deployment页签，点`+`加号选择`Artifact...`添加项目

![](/images/2015/09/----20150920012703.png)

选择第二个带`exploded`的`War`包 [如果没看到war包请看](#1)

![](/images/2015/09/----20150920012812.png)

如图两个下拉都选择`Update class and resources`      

![](/images/2015/09/----20150920012841.png)

然后运行项目启动完成是这样的   

![](/images/2015/09/----20150920013126.png)

<h3 id="1">打包设置</h3>

>Maven项目这个一般默认就有了的不需要设置

点右上或`shift + ctrl + alt + S `进入项目设置

选择`Artifacts` 选择`+`加号添加一个web项目的war包 一般默认就设置好了

![](/images/2015/09/----20150920014245.png)

如果中间没有war expploded 包的话，在右边Artifacts里选择项目的war右键`put into output root`

![](/images/2015/09/----20150920014647.png)
