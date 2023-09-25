---
title: 使用泛型设计gorm扩展字段
date: 2023-09-25 17:37:26
updated: 2023-09-25 17:37:26
tags:
- go
- gorm
- 泛型
categories: 软件
permalink: design_gorm_extension_fields_using_generics
---

>大型项目经常需要在标准的用户表或员工表加些扩展字段，如果你有一套标准的用户管理系统的话，要么每个项目复制过来改一遍或者添加十几个固定的自定义字段Def1~Def10， 现在可以用在gorm定义模型时使用泛型来解决这个问题

### gorm embeded嵌入字段
使用`gorm:"embedded"`定义嵌入字段

```go
type User struct {
	gorm.Model
	Username string
	Password string
	Extend   UserExtendField `gorm:"embedded"` // 添加embed tag
}

type UserExtendField struct {
	OpenID string
	UnionID string
}
```
上面的model等价于这个, 两个生成的表结构是一致的
```go
type User struct {
	gorm.Model
	Username string
	Password string
	OpenID string
	UnionID string
}
```
上面两个模型都会生成同样的ddl sql, 如下
```sql
create table if not users
(
    id         bigint unsigned auto_increment
        primary key,
    created_at datetime(3) null,
    updated_at datetime(3) null,
    deleted_at datetime(3) null,
	  username   longtext    null,
    password   longtext    null,
    org_id     longtext    null,
    open_id    longtext    null,
    union_id   longtext    null   
)
```

### 使用泛型定义可扩展的模型
```go
type User[ExtendField any] struct {
	gorm.Model
	Username string
	Password string
	Extend   ExtendField `gorm:"embedded"`
}

// 需要自定义表名，否则gorm识别到的泛型的表名是不符合数据库标准的，建表会错误
func (User[Extend, Item]) TableName() string {
	return "ma_users"
}

// 定义扩展字段结构
type ExtendUserField struct {
	OrgID   string
	OpenID  string
	UnionID string
}
```

使用方法
```go
// 生成数据库表结构
db.AutoMigrate(User[ExtendUserField])

// 查找
var list []User[ExtendUserField]
db.model(&User[ExtendUserField]).Find(&list)
```

### 可扩展的子表
```go
type User[ExtendField any,Item any] struct {
	gorm.Model
	Username string
	Password string
	Extend   ExtendField `gorm:"embedded"`
	Items    Item `gorm:"foreignKey:user_id"` // 这里需要写外键
}
// 需要自定义表名，否则gorm识别到的泛型的表名是不符合数据库标准的，建表会错误
func (User[Extend, Item]) TableName() string {
	return "ma_users"
}

type UserItem struct {
	gorm.Model
	UserID  uint
	Product string
}

// 定义扩展字段结构
type ExtendUserField struct {
	OrgID   string
	OpenID  string
	UnionID string
}
```

使用方法
```go
// 查找
var list []User[ExtendUserField, UserItem]
db.model(&User[ExtendUserField, UserItem]).Find(&list)
```

### 使用类型别名简化泛型类型
>使用类型别名， 可以把上面的泛型代码简化
```go
type MyUser = User[ExUserField, UserItem]

var list []MyUser
db.model(&MyUser).Find(&list)
```
