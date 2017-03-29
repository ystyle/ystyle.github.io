---
title: docker + jenkins + git + maven自动化构建与部署
tags:
  - docker
  - GIT
  - Jenkins
  - Maven
categories: 系统
permalink: docker-jenkins-git-mavenzi-dong-hua-gou-jian-yu-bu-shu
id: 33
updated: '2016-07-03 13:11:13'
date: 2016-04-16 18:37:15
---

## docker + jenkins + git + maven自动化构建与部署

### 准备工作
1. 安装好最新docker
1. docker 分别pull 以下镜像 `jenkins:2.0-beta-1` `tomcat` `mysql`(mysql只用来做测试项目的数据库,有其它数据库服务器的可以不下载)
1. 下载[`maven`](http://mirrors.cnnic.cn/apache/maven/maven-3/3.3.9/binaries/apache-maven-3.3.9-bin.tar.gz) 解压`mkdir -p /dockerworkspace/maven && tar zxf apache-maven-3.3.9-bin.tar.gz -C /dockerworkspace/maven`    
1. 下载[`jdk`](http://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html) `tar zxf jdk*.tar.gz -C /dockerworkspace/java/ && mv /dockerworkspace/java/jdk* /dockerworkspace/java/jdk`

>本教程所有工具和数据目录存放于`/dockerworkspace`目录下

### 安装jenkins

```shell
docker run -d --name jenkins
    -p 8080:8080
    -p 50000:50000
    -v /dockerworkspace/jenkins:/var/jenkins_home
    -v /dockerworkspace/maven/apache-maven-3.3.9:/usr/local/maven
    -v /dockerworkspace/java/jdk:/usr/local/jdk
    jenkins:2.0-beta-1
```

访问jenkins:8080(jenkins改成服务器地址) ,然后输入以下查看到的密码Unlock Jenkins
```shell
cat /dockerworkspace/jenkins/secrets/initialAdminPassword
```
![](/images/2016/04/----20160416195200.png)

`Customize Jenkins`步骤时选择左边的`Install suggested plugins`
![](/images/2016/04/----20160416195403.png)

等待插件安装完成, 然后填写管理员信息

### 配置Jenkins
1. 登陆jenkins, 进入`系统管理-插件管理-可选插件` 搜索`ssh plugin` 然后安装, 安装界面选择安装好后重启jenkins

1. 进入`系统管理-系统管理-可选插件 - SSH remote hosts` 填写部署tomcat项目的host信息
   ![](/images/2016/04/----20160416200122.png)

1. 设置邮件发送服务器
    1. 进入`系统管理-系统管理-Jenkins Location` 中 `系统管理员邮件地址`
    2. `邮件通知` 中QQ企业邮箱设置如下(发件人的邮箱地址要和上面`系统管理员邮件地址一致`不然会报错)
    ![](/images/2016/04/----20160416200505.png)

1. JDK配置
     1. 进入`系统管理-Global Tool Configuration - jdk`
     1. 点新增JDK,别名:`jdk` `JAVA_HOME`填写`/usr/local/jdk`(我截图里用的是ibm家的jdk)
     ![](/images/2016/04/----20160416200756.png)

1. Maven配置
    1. 进入`系统管理-Global Tool Configuration - Maven`
    1. 点新增Maven,别名:`maven` `MAVEN_HOME`填写`/usr/local/maven`
    ![](/images/2016/04/----20160416200935.png)

### 新建测试项目
本教程中git管理端用的是`gogs`

1. 创建jenkins中的maven 项目
   1. 在jenkins首页点击新建选择`构建一个maven项目` 填写项目名称`test_tomcat`
    >(如果没有这项请安装插件`Maven Integration plugin`)

   2. 源码管理中选择git, 填写项目的git信息(Credentials点新增可以添加git的认证信息,支持`帐户名密码`,`ssh key` 等方式. `源码浏览器`在构建项目时的`修改记录`可以直接连接到git平台)
   ![](/images/2016/04/11111.png)
   ![](/images/2016/04/----20160416202529.png)
1. 构建触发器
    1. `身份验证令牌` 可以随意填写一个任意长度的字符串, 也可以填写uuid之类的, 并记录下来, 以后会用到

1. Post Steps (部署部份配合主机上的一人脚本使用,脚本内容往下看)
    1. 选择`Run only if build succeeds`只在构建成功时运行
    1. `Add post-build step` 选择`Execute shell script on remote host using ssh` 然后选择服务器和执行脚本信息
    ![](/images/2016/04/----20160416214719.png)
1. 在gogs上创建git hook (这一步在gitlab或github应该也有相应的方法)
    1. 进入上面构建的git项目`首页-仓库设置-管理git钩子-post-update`
    2. 填写以下脚本 (请把环境变量改为自己相应的服务器信息)
    ![](/images/2016/04/----20160416214926.png)
```shell
#!/bin/sh
# 请修改以下环境变量

SERVER=http://127.0.0.1:8080 #jenkins服务器地址
TOKEN=jenkins1270018080hosttesttomcat #jenkins项目的 身份验证令牌
JENKINS_USER=admin #jenkins用户
JENKINS_PWD=admin # jenkins用户密码
JENKINS_PROJECT=test_tomcat # jenkins项目名

echo "Startting Build War File On  Jenkins's Server"
echo "Setting Token On The Jenkins's Server......"
CRUMB=$(curl -s --user $JENKINS_USER:$JENKINS_PWD \
    $SERVER/crumbIssuer/api/xml?xpath=concat\(//crumbRequestField,%22:%22,//crumb\))
echo "Trigger Jenkins's Server Start Building......"
curl -s --user $JENKINS_USER:$JENKINS_PWD -H "$CRUMB" $SERVER/job/$JENKINS_PROJECT/build?token=$TOKEN
echo "Jenkins's Server Build Success!"
```

### tomcat 服务器配置
```shell
docker run -d
    --name test_tomcat
    -p 8888:8080
    -v /dockerworkspace/tomcat/webapps:/usr/local/tomcat/webapps
    -v /dockerworkspace/java/jdk:/usr/local/jdk
    -e "JAVA_HOME=/usr/local/jdk"
    tomcat
```
测试用mysql服务器
```shell
 docker run -p 3306:3306 --name mysql -e MYSQL_ROOT_PASSWORD=admin -d mysql
```

创建一个脚本文件`vim /dockerworkspace/tomcat/deploy.sh` 内容如下

```shell
#!/bin/sh
SERVER=http://127.0.0.1:8080 #jenkins服务器地址
TOKEN=jenkins1270018080hosttesttomcat #jenkins项目的 身份验证令牌
JENKINS_USER=admin #jenkins用户
JENKINS_PWD=admin # jenkins用户密码
JENKINS_PROJECT=test_tomcat # jenkins项目名
MAVEN_GROUPID=net.lxy520.test_tomcat #maven项目pom.xml的groupId
MAVEN_NAME=ROOT #maven项目pom.xml的groupId
MAVEN_VERSION=1.2.6 #maven项目pom.xml的groupId
CONTAINER=test_tomcat #tomcat docker 的容器id或名称

echo "设置Jenkins服务器为$SERVER"
echo "向服务器请求token"
CRUMB=$(curl -s --user $JENKINS_USER:$JENKINS_PWD \
    $SERVER/crumbIssuer/api/xml?xpath=concat\(//crumbRequestField,%22:%22,//crumb\))
echo "下载war文件......"
curl -s --user $JENKINS_USER:$JENKINS_PWD -H "$CRUMB" "$SERVER/job/$JENKINS_PROJECT/lastStableBuild/${MAVEN_GROUPID}\$${MAVEN_NAME}/artifact/$MAVEN_GROUPID/$MAVEN_NAME/$MAVEN_VERSION/${MAVEN_NAME}-${MAVEN_VERSION}.war" -o ${MAVEN_NAME}-${MAVEN_VERSION}.war
echo "下载完成!"
CURRENT=`pwd`
echo "临时存放路径:$CURRENT/${MAVEN_NAME}-${MAVEN_VERSION}.war"
echo "暂停Tomcat服务..."
docker stop $CONTAINER
echo "覆盖项目..."
rm -rf /dockerworkspace/tomcat/webapps/ROOT.war /dockerworkspace/tomcat/webapps/ROOT
mv ${MAVEN_NAME}-${MAVEN_VERSION}.war /dockerworkspace/tomcat/webapps/ROOT.war
echo "重启Tomcat服务..."
docker start $CONTAINER
echo "Tomcat启动成功."
```

### 测试
在本地项目中git push, 查看jenkins会不会自动构建,然后检查docker中的容器是否正确部署
![](/images/2016/04/----20160416215408.png)
