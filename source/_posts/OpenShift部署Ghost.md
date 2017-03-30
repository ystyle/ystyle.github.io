---
title: OpenShift部署Ghost
tags:
  - Ghost
categories: 系统
permalink: openshiftbu-shu-ghost
id: 4
updated: '2016-09-09 10:41:04'
date: 2015-06-17 07:45:20
---

### 简介：

利用免费云服务部署个人博客

-------------------------------------------

###一、注册openshift

[`点击注册 `](https://www.openshift.com/app/account/new?then=%2fapp%2fconsole)
___________________________________

###二、安装Ghost

点 [`Applications`](https://openshift.redhat.com/app/console/applications) - `Add Applications`

找到 `Ghost x.x.x` 点进去` Public URL` 随便写如：`ghost `

拉到下面点 `Create Application`

____________________________________

###三、配置域名

点 [`Applications`](https://openshift.redhat.com/app/console/applications) - 进入自己的应用

点`Change`添加个人域名，`Add alia`进入新页面填入自己的域名就行了如：[`www.lxy520.net`](http://www.lxy520.net)

进入域名解析如：`万网`  添加CNAME 指向 应用地址类似： `xxx-xxxx.rhcloud.com`

打开`Git bash`

执行
```shell
 cd ~/.ssh
 cat id_rsa.pub # 没有的话选运行 ssh-keygen -t rsa -C “您的邮箱地址”
```
到 [`Settings`](https://openshift.redhat.com/app/console/settings)  - `Add a new key...`

复制`id_rsa.pub`里的内容到大的编辑框，第一行名称可以随便写，然后保存

然后复制应用页面的 `Source Code` 类似： `xxxx@xxx-xxxx.rhcloud.com` 的地址

在`Git bash` 执行:

```shell
ssh xxxx@xxx-xxxx.rhcloud.com #如： ssh 5581340d50044601a3000167@ghost-ystyle.rhcloud.com
```

远程到openshift后(可以用其它工具连接如`xshell`)

```shell
#安装主题 其它主题下载：http://marketplace.ghost.org/
cd ${OPENSHIFT_REPO_DIR}/themes/
git clone https://github.com/fabienwang/Ghost-Flat.git
```
```shell
#配置Ghost博客
cd ${OPENSHIFT_REPO_DIR}
vim  config.js #按i进入编辑模式，修改第一页和下几页的production下的url为自己的域名 如：http://www.lxy520.net 然后按Esc输入:wq 按回车退出
```

```shell
#实现openshift自动重启
cd ${OPENSHIFT_REPO_DIR}.openshift/cron/hourly
wget http://dl-cystc.qiniudn.com/openshift/restart.sh
chmod 711 restart.sh
```
```shell
#重启应用, 安装主题与修改config.js 时需要重启应用
ctl_all restart
```
________________________________________________

###四、初始化博客

用自己的域名进入博客，在地址栏加上`/ghost `

输入用户名，邮箱，密码初始化博客

完成之后, 后台页面 `content` 管理文章，`New post`发布博客， `Setting`设置博客基本信息
