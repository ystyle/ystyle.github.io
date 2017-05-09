---
title: leanote添探索功能
permalink: leanote-Add-the-search-function
date: 2017-04-07 16:39:19
tags:
  - golang
  - leanote
  - 探索
categories: 编程
---
### leanote 编译打包

- 配置本地环境

设置`GOPATH`环境变量为工作区目录
然后执行:
```shell
go get github.com/revel/cmd/revel
go get github.com/ystyle/leanote/app
mv $GOPATH/src/github.com/ystyle $GOPATH/src/github.com/leanote
```
>注:源码在`$GOPATH/src/github.com/leanote/leanote/`目录

- 编译文件
```
revel run github.com/leanote/leanote dev 9000
### 访问http://localhost:9000 触发build
bin/release.sh
```

### 添加功能

- 替换`conf/routes`文件

- 新建文件`leanote/public/js/exporer.js`

```javascript
var totalPage,
    count,
    curPage;

var initLea = function (page) {

    $.ajax({
        type: "GET",
        url: "/blog/listAllUserBlogs",
        data:{page:page},
        dataType: "json",
        success: function(res){
            if (res.List){
                var lis = res.List.map(function(article,i) {
                    article.Tags = article.Tags ? article.Tags :[];
                    var tags = article.Tags.map(function(tag) {
                        return '<a class="label label-default label-post" href="/blog/tag/'+article.User.Username+'/'+encodeURIComponent(tag)+'">'+tag+'</a>'
                    }).join(" ");
                    return '<li id="'+ i +"-" + article.UserId +'">'+
        				'<div class="article">'+
        					'<a class="title" href="/blog/post/'+article.User.Username+'/'+article.UrlTitle+'" title="'+article.Title+'" target="_blank">'+
        						article.Title +
        					'</a>'+
        					'<div class="user-card" title="'+article.User.Username+'">'+
        					    '<a class="avatar " href="/blog/'+article.User.Username+'" target="_blank" >'+
        								'<img src="'+article.User.Logo+'">'+
        					    '</a>'+
        					    '<div class="dropdown-menu user-card-content">'+
        					    '</div>'+
        					'</div>'+
        					'<div class="content">'+
        						article.Desc +
        					'</div>'+
        					'<div class="article-info">'+
        							'<span class="fa fa-bookmark-o"></span>'+
        							tags +
        							'&nbsp;&nbsp;'+
        						'<span class="fa fa-eye"></span> '+ article.ReadNum+
        						'&nbsp;&nbsp;'+
        						'<span class="fa fa-thumbs-o-up"></span> '+ article.LikeNum+
        						'&nbsp;&nbsp;'+
        						'<span class="fa fa-comments-o"></span> '+ article.CommentNum+
        					'</div>'+
        				'</div>'+
        			'</li>';
                }).join(" ");
                $(".thumbnails").empty();
                $(".thumbnails").append(lis);
                totalPage =  res.Item.TotalPage ;
                if(totalPage > 1) {
                    count =  res.Item.Count ;
                    curPage =  res.Item.CurPage -1;
                    $(".pagination").pagination(count, {
                        items_per_page:  res.Item.PerPageSize,
                        prev_text:"上一页",
                        next_text:"下一页",
                        current_page: curPage,
                        callback: function(pageNum) {
                            pageNum++;
                            initLea(pageNum);
                        }
                    });
                }
            }
        }
    });
}

if (location.pathname == "/blog/single/admin/lea"){
    $("#posts")
        .empty()
        .append('<ul class="thumbnails"></ul>')
        .append('<div id="pagination" class="clearfix"><ul class="pagination pagination-sm m-t-none m-b-none"></ul></div>');
    initLea();
}

```

- 在主题的`header.html`里`<!-- 字体必须同一域 -->`下添加
```html
<link href="https://dn-leanote.qbox.me/css/blog/p.css?i=2" rel="stylesheet">
```
- 在`footer.html`里添加
```html
<script src="/js/jquery.pagination.js"></script>
<script src="/js/exporer.js"></script>
```
