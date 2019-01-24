---
title: ShareX使用七牛文件上传
date: 2017-07-05 14:06:26
permalink: share-the-use-of-qiniu-file-upload
tags:
  - ShareX
  - 软件
categories:
  - 软件
---
- ShareX界面

![](https://dl.ystyle.top/qiniu//201717051546-t.png)


### 配置文件
- token字段得自己在七牛的其它工具生成， 本文后面提供一个[我制作的小工具](/2017/07/05/share-the-use-of-qiniu-file-upload/#qiniu-token-获取工具)
- 上传的文件名格式为 `20171705/1546-t.png`,  `-`后面的为随机数字或字母。
- URL字段在七牛存储空间的内容管理页面的`外链默认域名` 下拉菜单能找到
- [在线配置生成工具](https://91p7joo70y.codesandbox.io/)
- 在配置页面填写好`存储区域、token、域名` 下载配置导入ShareX
- ~~文件保存为 `qiniu.sxcu` 然后在上图所示界面导入~~
- ~~`RequestURL` 可能因为每个对象存储的区域不一样， 华东，华北，华南，北美 的地址分别为 `http://up-z0.qiniu.com/` `http://up-z1.qiniu.com/` `http://up-z2.qiniu.com/` `http://up-na0.qiniu.com/`~~

配置文件示例：

```json
{
  "Name": "qiniu",
  "DestinationType": "ImageUploader, FileUploader",
  "RequestType": "POST",
  "RequestURL": "http://up-z2.qiniu.com/",
  "FileFormName": "file",
  "Arguments": {
    "token": "这个填写自己的",
    "key": "%y%yy%d%h%mi-%ra.png",
    "file": "$input$"
  },
  "ResponseType": "Text",
  "URL": "https://dl.ystyle.top/qiniu//$json:key$"
}
```

### qiniu token 获取工具
本工具支持 windows, linux, osx , 使用方法如下

参数说明：
- ak ACCESS_KEY 在七牛个人中心密钥管理界面获取
- sk SECRET_KEY 在七牛个人中心密钥管理界面获取
- bk bucket name 存储空间的免名称
- ex Expires time , token过期时间 默认 `3600 * 24 * 180 `(180天)

```shell
$ qiniutoken -h
Usage of qiniutoken:
  -ak string
        ACCESS_KEY
  -bk string
        bucket name
  -ex uint
        Expires (default 15552000)
  -sk string
        SECRET_KEY

# windows使用示例: 按着shift 右键文件夹空白打开命令行，输入以下命令， 把ak sk bk换成自己的
qiniutoken.exe -ak=lPNn5sBYjqUhn_DhMOkHzoznYM3KwUt2sE1W21F1 -sk=E45Ox_RlUdrz0YOtasiuerLtKZxALiX9-7NduzHT -bk=images
```
下载地址：链接：http://pan.baidu.com/s/1pKIo0R5 密码：`wfew`
