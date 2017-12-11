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

- log4j to redis Appender
>依赖 Jedis, 为了从JedisPool取出连接

```java

import org.apache.log4j.AppenderSkeleton;
import org.apache.log4j.helpers.LogLog;
import org.apache.log4j.spi.LoggingEvent;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.JedisPoolConfig;

public class RedisAppender extends AppenderSkeleton{
    private static final String DEFAULT_KEYTYPE = "channel";
    private static final String DEFAULT_KEY = "logstash-log";
    String host = "127.0.0.1";
    int port = 6379;
    String password;
    String keyType = DEFAULT_KEYTYPE;
    String key = DEFAULT_KEY;
    int timeout = 2000;

    // 连接池设置
    private long minEvictableIdleTimeMillis = 60000L;
    private long timeBetweenEvictionRunsMillis = 30000L;
    private int numTestsPerEvictionRun = -1;
    private int maxTotal = 8;
    private int maxIdle = 0;
    private int minIdle = 0;
    private boolean blockWhenExhaused = false;
    private String evictionPolicyClassName;
    private boolean lifo = false;
    private boolean testOnBorrow = false;
    private boolean testWhileIdle = false;
    private boolean testOnReturn = false;

    static private JedisPool jedisPool;

    @Override
    public void activateOptions() {
        super.activateOptions();
        JedisPoolConfig poolConfig = new JedisPoolConfig();
        if (lifo) {
            poolConfig.setLifo(lifo);
        }
        if (testOnBorrow) {
            poolConfig.setTestOnBorrow(testOnBorrow);
        }
        if (testWhileIdle) {
            poolConfig.setTestWhileIdle(testWhileIdle);
        }
        if (testOnReturn) {
            poolConfig.setTestOnReturn(testOnReturn);
        }
        if (timeBetweenEvictionRunsMillis > 0) {
            poolConfig.setTimeBetweenEvictionRunsMillis(timeBetweenEvictionRunsMillis);
        }
        if (evictionPolicyClassName != null && evictionPolicyClassName.length() > 0) {
            poolConfig.setEvictionPolicyClassName(evictionPolicyClassName);
        }
        if (blockWhenExhaused) {
            poolConfig.setBlockWhenExhausted(blockWhenExhaused);
        }
        if (minIdle > 0) {
            poolConfig.setMinIdle(minIdle);
        }
        if (maxIdle > 0) {
            poolConfig.setMaxIdle(maxIdle);
        }
        if (numTestsPerEvictionRun > 0) {
            poolConfig.setNumTestsPerEvictionRun(numTestsPerEvictionRun);
        }
        if (maxTotal != 8) {
            poolConfig.setMaxTotal(maxTotal);
        }
        if (minEvictableIdleTimeMillis > 0) {
            poolConfig.setMinEvictableIdleTimeMillis(minEvictableIdleTimeMillis);
        }

        if (password != null && password.length() > 0) {
            jedisPool = new JedisPool(poolConfig, host, port, timeout, password);
        } else {
            jedisPool = new JedisPool(poolConfig, host, port, timeout);
        }
        // 配置连接实验
        try {
            Jedis jedis = jedisPool.getResource();
            jedis.ping();
        } catch (Exception e) {
            LogLog.error("Redis is can not connected: " +  e.getMessage());
        }
    }

    @Override
    protected void append(LoggingEvent event) {
        Jedis resource = null;
        try {
            if (jedisPool == null){
                return;
            }
            resource = jedisPool.getResource();
            String format = getLayout().format(event);
            if (DEFAULT_KEYTYPE.equals(keyType)){
                resource.publish(key,format);
            }else {
                resource.lpush(key,format);
            }
        }catch (Exception e){

        }finally {
            if (resource != null){
                resource.close();
            }
        }
    }

    @Override
    public void close() {
        if (jedisPool!=null){
            jedisPool.destroy();
        }
    }

    @Override
    public boolean requiresLayout() {
        return true;
    }

    public String getHost() {
        return host;
    }

    public void setHost(String host) {
        this.host = host;
    }

    public int getPort() {
        return port;
    }

    public void setPort(int port) {
        this.port = port;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getKeyType() {
        return keyType;
    }

    public void setKeyType(String keyType) {
        this.keyType = keyType;
    }

    public String getKey() {
        return key;
    }

    public void setKey(String key) {
        this.key = key;
    }

    public int getTimeout() {
        return timeout;
    }

    public void setTimeout(int timeout) {
        this.timeout = timeout;
    }

    public long getMinEvictableIdleTimeMillis() {
        return minEvictableIdleTimeMillis;
    }

    public void setMinEvictableIdleTimeMillis(long minEvictableIdleTimeMillis) {
        this.minEvictableIdleTimeMillis = minEvictableIdleTimeMillis;
    }

    public long getTimeBetweenEvictionRunsMillis() {
        return timeBetweenEvictionRunsMillis;
    }

    public void setTimeBetweenEvictionRunsMillis(long timeBetweenEvictionRunsMillis) {
        this.timeBetweenEvictionRunsMillis = timeBetweenEvictionRunsMillis;
    }

    public int getNumTestsPerEvictionRun() {
        return numTestsPerEvictionRun;
    }

    public void setNumTestsPerEvictionRun(int numTestsPerEvictionRun) {
        this.numTestsPerEvictionRun = numTestsPerEvictionRun;
    }

    public int getMaxTotal() {
        return maxTotal;
    }

    public void setMaxTotal(int maxTotal) {
        this.maxTotal = maxTotal;
    }

    public int getMaxIdle() {
        return maxIdle;
    }

    public void setMaxIdle(int maxIdle) {
        this.maxIdle = maxIdle;
    }

    public int getMinIdle() {
        return minIdle;
    }

    public void setMinIdle(int minIdle) {
        this.minIdle = minIdle;
    }

    public boolean isBlockWhenExhaused() {
        return blockWhenExhaused;
    }

    public void setBlockWhenExhaused(boolean blockWhenExhaused) {
        this.blockWhenExhaused = blockWhenExhaused;
    }

    public String getEvictionPolicyClassName() {
        return evictionPolicyClassName;
    }

    public void setEvictionPolicyClassName(String evictionPolicyClassName) {
        this.evictionPolicyClassName = evictionPolicyClassName;
    }

    public boolean isLifo() {
        return lifo;
    }

    public void setLifo(boolean lifo) {
        this.lifo = lifo;
    }

    public boolean isTestOnBorrow() {
        return testOnBorrow;
    }

    public void setTestOnBorrow(boolean testOnBorrow) {
        this.testOnBorrow = testOnBorrow;
    }

    public boolean isTestWhileIdle() {
        return testWhileIdle;
    }

    public void setTestWhileIdle(boolean testWhileIdle) {
        this.testWhileIdle = testWhileIdle;
    }

    public boolean isTestOnReturn() {
        return testOnReturn;
    }

    public void setTestOnReturn(boolean testOnReturn) {
        this.testOnReturn = testOnReturn;
    }
}
```

- 使用方法

```properties
# 在log4j.rootLogger添加logstash
log4j.rootLogger=WARN, Console, RollingFile, logstash

# log4j to redis 配置
log4j.appender.logstash=RedisAppender #上面RedisAppender的类名
log4j.appender.logstash.host=127.0.0.1
log4j.appender.logstash.port=6379
log4j.appender.logstash.password=123456
log4j.appender.logstash.keyType=channel #支持 channe与list
log4j.appender.logstash.key=logstash-log
log4j.appender.logstash.layout=net.logstash.log4j.JSONEventLayoutV1
log4j.appender.logstash.layout.locationInfo=true
```

- 官方的json layout, 在pom文件添加以下内容
```xml
<dependency>
    <groupId>net.logstash.log4j</groupId>
    <artifactId>jsonevent-layout</artifactId>
    <version>1.7</version>
</dependency>
```

```java
Logger logger = LoggerFactory.getLogger(getClass());
MDC.put("title","用户验证模块"); // 让后续log带上入口信息，详情百度搜索 log4j mdc
logger.debug("用户名验证失败！");
```

### 预览结果
![](http://osloqpukl.bkt.clouddn.com/201717291744-B.png)

![](http://osloqpukl.bkt.clouddn.com/201717291744-R.png)
