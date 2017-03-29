---
title: ActiveMQ 入门
tags: nodejs
categories: 编程
permalink: activemq-ru-men
id: 16
updated: '2015-09-24 18:11:51'
date: 2015-07-30 23:34:38
---

## ActiveMQ 入门

###  下载与安装

[`官方下载地址`](http://activemq.apache.org/download-archives.html)

解压，运行bin/win[32|64]/activemq[.bat] 启动服务

###  环境信息

控制台: `http://localhost:8161` 默认端口:`8161`  
服务地址:   
>host: `localhost`  
>port: `61613`

### 代码例子

基本信息：

> 语言：Node.js  
> 客户端：[stompjs](https://github.com/jmesnil/stomp-websocket)

消息发布者:

```javascript
// Publisher.js
var Stomp = require('stompjs');

// Use raw TCP sockets
var client = Stomp.overTCP('localhost', 61613);
// uncomment to print out the STOMP frames

//client.debug = console.log;

var connectCallback = function(frame) {
  console.log ('Connected! sending some message');
  setInterval(function(){
      var date = new Date().toLocaleString();
      console.log("sending:"+date);
      client.send('/queue/FirstQueue', {}, "queue:" + date);
      client.send('/topic/FirstQueue', {}, "topic:" + date);
  },10000)
};

var errorCallback = function(error){
    console.log(error.headers.message);
};

client.connect('admin', 'admin', connectCallback,connectCallback);
```

Queue消息消费者

```javascript
// Consumer_queue.js
var Stomp = require('stompjs');

// Use raw TCP sockets
var client = Stomp.overTCP('localhost', 61613);
// uncomment to print out the STOMP frames
// client.debug = console.log;

var connectCallback = function(frame) {
    var subscription = client.subscribe('/queue/FirstQueue', onMessage);
    //subscription.unsubscribe();
};

var onMessage = function(message){
    if (message.body) {
      console.log("got message with body " + message.body)
    } else {
      console.log("got empty message");
    }
};

var errorCallback = function(error){
    console.log(error.headers.message);
};

client.connect('admin', 'admin', connectCallback,connectCallback);
```

Topic消息消费者

```javascript
// Consumer_topics.js
var Stomp = require('stompjs');

// Use raw TCP sockets
var client = Stomp.overTCP('localhost', 61613);
// uncomment to print out the STOMP frames
// client.debug = console.log;

var connectCallback = function(frame) {
    var subscription = client.subscribe('/topic/FirstQueue', onMessage);
    //subscription.unsubscribe();
};

var onMessage = function(message){
    if (message.body) {
      console.log("got message with body " + message.body)
    } else {
      console.log("got empty message");
    }
};

var errorCallback = function(error){
    console.log(error.headers.message);
};

client.connect('admin', 'admin', connectCallback,connectCallback);
```

注： Queue、Topic消息消费者分别启动两个，再启动消息发布者，观察Queue、Topic消息消费者接收到的消息有什么区别  


### Queue与Topic的比较

1、JMS Queue执行load balancer语义：  
一条消息仅能被一个consumer收到。如果在message发送的时候没有可用的consumer，那么它将被保存一直到能处理该message的consumer可用。如果一个consumer收到一条message后却不响应它，那么这条消息将被转到另一个consumer那儿。一个Queue可以有很多consumer，并且在多个可用的consumer中负载均衡。


2、Topic实现publish和subscribe语义：  
一条消息被publish时，它将发到所有感兴趣的订阅者，所以零到多个subscriber将接收到消息的一个拷贝。但是在消息代理接收到消息时，只有激活订阅的subscriber能够获得消息的一个拷贝。


3、分别对应两种消息模式：  
Point-to-Point (点对点),Publisher/Subscriber Model (发布/订阅者)  
其中在Publicher/Subscriber 模式下又有Nondurable subscription（非持久订阅）和durable subscription (持久化订阅)2种消息处理方式。


总结：Topic就是游戏里的日常任务，只要在线都能接。Queue是小说里的神位传承，只有通过了测试的唯一一个 人才能得到
