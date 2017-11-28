---
title: 用docker搭建ELK
date: 2017-09-27 09:05:31
tags:
  - elk
  - docker
categories: 系统
permalink: use-docker-to-build-ELKStack
---

>1. `logstash-input-tcp` 可用，但log4j会把对象序列化，在kibana看到的会是乱码
2. `logstash-input-log4j` 不可用，官方已废弃该插件， log4j连接不上该插件
3. `logstash-input-redis` 可用，配置简洁，有安全保障

>本篇以 `logstash-input-redis`插件配置elk


### 下载sebp/elk镜像
```shell
docker pull sebp/elk
```

### 启动容器

- 创建docker-compose.yml文件
```yaml
version: '3'
services:
  elk:
    image: sebp/elk
    ports:
    - "5601:5601"
    - "9200:9200"
    - "5044:5044"
    restart: always
```
- 设置主机的虚拟内存
```shell
sysctl -w vm.max_map_count=262144
```

- 启动容器
```shell
docker-compose up -d
```

### 配置Logstash虚拟日志条目
- 进入容器
```shell
docker exec -ti elk_elk_1 bash
```
删除`/etc/logstash/conf.d/`下的文件，并新增`log4j.conf`, 写入以下内容, 然后重启elk
```
input {
  redis {
    host => "127.0.0.1"
    port => 6379
    password => "123456"
    type => "redis-logs"
    data_type => "channel"
    key => "logstash-log"
  }
}
output {
    elasticsearch {
        hosts => ["localhost"]
        index => "logstash-%{type}-%{+YYYY.MM.dd}"
        document_type => "%{type}"
        flush_size => 20000
        idle_flush_time => 10
        sniffing => true
        template_overwrite => true
    }
}
```
>output 说明 Logstash 会努力攒到 20000 条数据一次性发送出去，但是如果 10 秒钟内也没攒够 20000 条，Logstash 还是会以当前攒到的数据量发一次。

### 测试
1. 用任意Redis client连接到redis, 执行 `publish logstash-log "debug message !!!!"`
2. 过10秒后可以在kibana界面上看到,`debug message !!!!`的日志


### kibana设置
进去会让设置一个index ,可以设置为上面Logstash配置文件`log4j.conf` output的elasticsearch中的index前缀就行了，然后在首页就能查询到了
![](http://osloqpukl.bkt.clouddn.com/201717291743-N.png)



### 集成到java web项目
以Jedis为例， 配置redis过程略

- LogEvent日志对象
>toString 方法依赖了fastjson,为了在elk中的日志有结构，如果 没有使用fastjson的可以换成自己在使用的

```java
import com.alibaba.fastjson.JSON;
import com.alibaba.fastjson.annotation.JSONField;

import java.io.Serializable;
import java.util.Date;

public class LogEvent implements Serializable {
    private long timeStamp; //时间戳
    private String level;// 日志级别
    private String threadName;// 线程名
    private String className;// 类名
    private String method;// 方法名
    private String fileName;// 文件名
    private Integer lineNumber;// 行号
    private String title;// 标题
    private String type;// 日志类型
    private String message;// 消息
    private Object params;// 参数
    private String exception;//异常
    @JSONField(format = "yyyy-MM-dd HH:mm:ss")
    private Date logTime;// 记录日志时间

    public LogEvent() {
    }

    public long getTimeStamp() {
        return timeStamp;
    }

    public void setTimeStamp(long timeStamp) {
        this.timeStamp = timeStamp;
    }

    public String getLevel() {
        return level;
    }

    public void setLevel(String level) {
        this.level = level;
    }

    public String getThreadName() {
        return threadName;
    }

    public void setThreadName(String threadName) {
        this.threadName = threadName;
    }

    public String getClassName() {
        return className;
    }

    public void setClassName(String className) {
        this.className = className;
    }

    public String getMethod() {
        return method;
    }

    public void setMethod(String method) {
        this.method = method;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public Object getParams() {
        return params;
    }

    public void setParams(Object params) {
        this.params = params;
    }

    @Override
    public String toString() {
        return JSON.toJSONString(this);
    }

    public String getFileName() {
        return fileName;
    }

    public void setFileName(String fileName) {
        this.fileName = fileName;
    }

    public Integer getLineNumber() {
        return lineNumber;
    }

    public void setLineNumber(Integer lineNumber) {
        this.lineNumber = lineNumber;
    }

    public String getException() {
        return exception;
    }

    public void setException(String exception) {
        this.exception = exception;
    }

    public Date getLogTime() {
        return logTime;
    }

    public void setLogTime(Date logTime) {
        this.logTime = logTime;
    }
}
```

- LogUtils日志工具类
>依赖 Spring core, 为了从JedisPool取出连接，可以用静态类，或单例工具类代替

```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import redis.clients.jedis.Jedis;

import java.util.Date;

/**
 * 打印日志到ELK
 */
public class LogUtils {

    private static JedisPool jedisPool = SpringContextHolder.getBean(JedisPool.class);
    private static int STACKINDEX = 4;
    private static String LOGCHANNEL = "logstash-log";

    /**
     * 日志对象
     */
    private static Logger logger = LoggerFactory.getLogger(LogUtils.class);


    private LogUtils() {
    }

    /**
     * 记录日志
     * @param level 日志级别
     * @param title 标题
     * @param message 消息
     * @param params 参数
     * @param exception 异常
     */
    private static void log(String level, String title, String message, Object params, Exception exception) {
        StackTraceElement stack[] = Thread.currentThread().getStackTrace();
        StackTraceElement stackTraceElement = stack[STACKINDEX];
        LogEvent event = new LogEvent();
        event.setTimeStamp(System.currentTimeMillis());
        event.setLevel(level);
        event.setThreadName(Thread.currentThread().getName());
        event.setClassName(stackTraceElement.getClassName());
        event.setMethod(stackTraceElement.getMethodName());
        event.setFileName(stackTraceElement.getFileName());
        event.setLineNumber(stackTraceElement.getLineNumber());
        event.setTitle(title);
        event.setMessage(message);
        event.setParams(params);
        event.setLogTime(new Date());
        if (exception != null){
            event.setException(Exceptions.getStackTraceAsString(exception));
        }
        publish(event);
    }

    private static void publish(LogEvent event){
        Jedis resource = jedisPool.getResource();
        try {
            resource.publish(LOGCHANNEL,event.toString());
            logger.debug(event.toString());
        } finally {
            resource.close();
        }
    }

    /**
     * 记录日志
     * @param title 标题
     * @param message 消息
     * @param params 参数
     * @param exception 异常
     */
    public static void debug(String title, String message, Object params, Exception exception) {
        log("DEBUG", title, message, params, exception);
    }

    /**
     * 记录日志
     * @param message 消息
     */
    public static void debug(String message) {
        log("DEBUG", null, message, null, null);
    }

    /**
     * 记录日志
     * @param title 标题
     * @param message 消息
     */
    public static void debug(String title,String message) {
        log("DEBUG", title, message, null, null);
    }

    /**
     * 记录日志
     * @param message 消息
     * @param exception 异常
     */
    public static void debug(String message, Exception exception) {
        log("DEBUG", null, message, null, exception);
    }

    /**
     * 记录日志
     * @param title 标题
     * @param message 消息
     * @param params 参数
     * @param exception 异常
     */
    public static void info(String title, String message, Object params, Exception exception) {
        log("INFO", title, message, params, exception);
    }

    /**
     * 记录日志
     * @param message 消息
     */
    public static void info(String message) {
        log("INFO", null, message, null, null);
    }

    /**
     * 记录日志
     * @param title 标题
     * @param message 消息
     */
    public static void info(String title,String message) {
        log("INFO", title, message, null, null);
    }

    public static void info(String message, Exception exception) {
        log("INFO", null, message, null, exception);
    }

    /**
     * 记录日志
     * @param title 标题
     * @param message 消息
     * @param params 参数
     * @param exception 异常
     */
    public static void warn(String title, String message, Object params, Exception exception) {
        log("WARN", title, message, params, exception);
    }

    /**
     * 记录日志
     * @param message 消息
     */
    public static void warn(String message) {
        log("WARN", null, message, null, null);
    }

    /**
     * 记录日志
     * @param title 标题
     * @param message 消息
     */
    public static void warn(String title,String message) {
        log("WARN", title, message, null, null);
    }

    /**
     * 记录日志
     * @param message 消息
     * @param exception 异常
     */
    public static void warn(String message, Exception exception) {
        log("WARN", null, message, null, exception);
    }

    /**
     * 记录日志
     * @param title 标题
     * @param message 消息
     * @param params 参数
     * @param exception 异常
     */
    public static void error(String title, String message, Object params, Exception exception) {
        log("ERROR", title, message, params, exception);
    }

    /**
     * 记录日志
     * @param message 消息
     */
    public static void error(String message) {
        log("ERROR", null, message, null, null);
    }

    /**
     * 记录日志
     * @param title 标题
     * @param message 消息
     */
    public static void error(String title,String message) {
        log("ERROR", title, message, null, null);
    }

    /**
     * 记录日志
     * @param message 消息
     * @param exception 异常
     */
    public static void error(String message, Exception exception) {
        log("ERROR", null, message, null, exception);
    }
}

```

- 使用方法

```java
LogUtils.debug("用户模块","查询异常");
LogUtils.error("用户模块","查询异常",flightSyncLog,new Exception("查询SQL语法错误"));
```

### 预览结果
![](http://osloqpukl.bkt.clouddn.com/201717291744-B.png)

![](http://osloqpukl.bkt.clouddn.com/201717291744-R.png)
