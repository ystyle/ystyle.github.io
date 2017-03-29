---
title: 使用hadoop+中文分词统计小说里的用词频率
tags:
  - hadoop
  - JAVA
categories: 编程
permalink: shi-yong-hadoop-zhong-wen-fen-ci-tong-ji-xiao-shuo-li-de-yong-ci-pin-lu
id: 29
updated: '2016-04-24 12:04:32'
date: 2016-02-22 14:24:16
---

## 使用hadoop+中文分词统计小说里的用词频率
>事情是这样的, 某小说贴吧吧友开玩笑说 某作者最常使用的词语是xxxx , 然后就突发奇想地想用工具分析一下

### 环境
系统: ArchLinux  

软件: hadoop 2.7

### 准备
下载hadoop: [下载地址](http://hadoop.apache.org/releases.html)

下载分词插件: [下载地址](http://www.oschina.net/p/ikanalyzer)

1.解压hadoop-2.7.0.tar.gz: `tar cxf hadoop-2.7.0.tar.gz`
>我的解压到`/home/ystyle/Applications/hadoop-2.7.0`下面了(我下载时是hadoop-2.7.0.tar.gz)

2.设置环境变量
vim ~/.bashrc
```
export HADOOP_INSTALL=/home/ystyle/Applications/hadoop-2.7.0
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
```
然后再执行 `source ~/.bashrc`

PS: 这里使用hadoop的单机模式

### 代码
```java
package net.ystyle.hadoop;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.util.GenericOptionsParser;
import org.wltea.analyzer.core.IKSegmenter;
import org.wltea.analyzer.core.Lexeme;

import java.io.IOException;
import java.io.StringReader;

public class WordCount {

  public static class TokenizerMapper
       extends Mapper<Object, Text, Text, IntWritable>{

    private final static IntWritable one = new IntWritable(1);
    private Text word = new Text();

    public void map(Object key, Text value, Context context
                    ) throws IOException, InterruptedException {
        IKSegmenter iks = new IKSegmenter(new StringReader(value.toString()), true);
        Lexeme t;
        while ((t = iks.next()) != null) {
            word.set(t.getLexemeText());
            context.write(word, one);
        }
    }
  }

  public static class IntSumReducer
       extends Reducer<Text,IntWritable,Text,IntWritable> {
    private IntWritable result = new IntWritable();

    public void reduce(Text key, Iterable<IntWritable> values,
                       Context context
                       ) throws IOException, InterruptedException {
      int sum = 0;
      for (IntWritable val : values) {
        sum += val.get();
      }
      result.set(sum);
      context.write(key, result);
    }
  }

  public static void main(String[] args) throws Exception {
    Configuration conf = new Configuration();
    String[] otherArgs = new GenericOptionsParser(conf, args).getRemainingArgs();
    if (otherArgs.length < 2) {
      System.err.println("Usage: wordcount <in> [<in>...] <out>");
      System.exit(2);
    }
    Job job = Job.getInstance(conf, "word count");
    job.setJarByClass(WordCount.class);
    job.setMapperClass(TokenizerMapper.class);
    job.setCombinerClass(IntSumReducer.class);
    job.setReducerClass(IntSumReducer.class);
    job.setOutputKeyClass(Text.class);
    job.setOutputValueClass(IntWritable.class);
    for (int i = 0; i < otherArgs.length - 1; ++i) {
      FileInputFormat.addInputPath(job, new Path(otherArgs[i]));
    }
    FileOutputFormat.setOutputPath(job,
      new Path(otherArgs[otherArgs.length - 1]));
    System.exit(job.waitForCompletion(true) ? 0 : 1);
  }
}

```
> 本代码改自hadoop自带的wordcount: 源码在`hadoop/share/hadoop/mapreduce/sources/hadoop-mapreduce-examples-2.7.2-sources.jar` 类名为`org.apache.hadoop.examples.WordCount` 这里只改了map方法添加了IK分词

### 在IDEA里创建项目
1. 创建普通项目
2. 按 `shift + alt + ctrl + s` 进入项目设置, 选择`Modules-Dependencies`添加`hadoop/share/hadoop/`目录下的`common` `hdfs` `mapreduce` `yarn` `common/lib` 到Dependencies下
3. 把下载的ik分词jar放`hadoop/share/hadoop/mapreduce`目录下

如图:
![](/images/2016/02/----20160222171610.png)

![](/images/2016/02/----20160222171633.png)

### 运行
1. 把下载的小说放 `/home/ystyle/hadoop/input` 下面
2. 在IDEA的`Run/Debug Configurations`里的`Program arguments` 里填上
`/home/ystyle/hadoop/input /home/ystyle/hadoop/output`
3. 近按`Shift + F10` 运行, 等待结果

### 结果分析
我分析的小说为<<我欲封天>>

1. `cd /home/ystyle/hadoop/output` 结果在文件`part-r-00000`里
2. 先把结果按使用次数排序并存在`0.txt`里: `sort -k2rn part-r-00000> 0.txt`
3. 分析两字词语的使用次数: `awk '{if(length($1)==2) print $0}' 0.txt > 2.txt`
4. 分析四字词语的使用次数: `awk '{if(length($1)==4) print $0}' 0.txt > 4.txt`

### 部分结果如下
两字词语
```
在这	9889
此刻	9000
一个	8819
立刻	8676
身体	8338
到了	7906
出现	7504
他们	7382
修士	7350
四周	7104
```

四字词语
```
与此同时	1443
中年男子	1089
轰的一声	1048
未完待续	893
惊天动地	853
面色苍白	752
前所未有	481
兄弟姐妹	421
无法形容	408
毫不迟疑	390
```
