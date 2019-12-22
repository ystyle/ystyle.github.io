---
title: 嵌入式数据库storm的使用
date: 2019-12-22 14:46:26
tags:
- BoltDB
- storm
- go
categories: 软件
permalink: how-to-use-storm-db
---

>storm是一个使用BoltDB的上层orm框架

### 地址:
- [数据查看工具]: https://github.com/br0xen/boltbrowser
- [驱动]: https://github.com/asdine/storm

### 初始化
```go
db, err := storm.Open("my.db")
defer db.Close()
```
### 定义对象模型
```go
type User struct {
  ID int // primary key
  Group string `storm:"index"` // this field will be indexed
  Email string `storm:"unique"` // this field will be indexed with a unique constraint
  Name string // this field will not be indexed
  Age int `storm:"index"`
}
```
>自增可以在主键上添加tag: `storm:"id,increment=2"` =2是自增步长

### 保存数据
```go
user := User{
  ID: 10,
  Group: "staff",
  Email: "john@provider.com",
  Name: "John",
  Age: 21,
  CreatedAt: time.Now(),
}

err := db.Save(&user)
// err == nil

user.ID++
err = db.Save(&user)
// err == storm.ErrAlreadyExists
```
### 修改
```go
// Update multiple fields
err := db.Update(&User{ID: 10, Name: "Jack", Age: 45})

// Update a single field
err := db.UpdateField(&User{ID: 10}, "Age", 0)
```

### 删除数据
```go
err := db.DeleteStruct(&user)
```


### 表管理操作
- 初始化索引 `err := db.Init(&User{})`
- 重建索引: `err := db.ReIndex(&User{})`
- 删表: `err := db.Drop(&User)` 或 `err := db.Drop("User")`

### 简单查询
```go
var user User
err := db.One("Email", "john@provider.com", &user)
// err == nil

err = db.One("Name", "John", &user)
// err == nil

err = db.One("Name", "Jack", &user)
// err == storm.ErrNotFound

// Fetch multiple objects
var users []User
err := db.Find("Group", "staff", &users)

// Fetch all objects
var users []User
err := db.All(&users)

// Fetch all objects sorted by index
var users []User
err := db.AllByIndex("CreatedAt", &users)

// Fetch a range of objects
var users []User
err := db.Range("Age", 10, 21, &users)

// Fetch objects by prefix
var users []User
err := db.Prefix("Name", "Jo", &users)

// Skip, Limit and Reverse
var users []User
err := db.Find("Group", "staff", &users, storm.Skip(10))
err = db.Find("Group", "staff", &users, storm.Limit(10))
err = db.Find("Group", "staff", &users, storm.Reverse())
err = db.Find("Group", "staff", &users, storm.Limit(10), storm.Skip(10), storm.Reverse())

err = db.All(&users, storm.Limit(10), storm.Skip(10), storm.Reverse())
err = db.AllByIndex("CreatedAt", &users, storm.Limit(10), storm.Skip(10), storm.Reverse())
err = db.Range("Age", 10, 21, &users, storm.Limit(10), storm.Skip(10), storm.Reverse())
```

### 高级查询
```go
// Equality
q.Eq("Name", John)

// Strictly greater than
q.Gt("Age", 7)

// Lesser than or equal to
q.Lte("Age", 77)

// Regex with name that starts with the letter D
q.Re("Name", "^D")

// In the given slice of values
q.In("Group", []string{"Staff", "Admin"})

// Comparing fields
q.EqF("FieldName", "SecondFieldName")
q.LtF("FieldName", "SecondFieldName")
q.GtF("FieldName", "SecondFieldName")
q.LteF("FieldName", "SecondFieldName")
q.GteF("FieldName", "SecondFieldName")

// Match if all match
q.And(
  q.Gt("Age", 7),
  q.Re("Name", "^D")
)

// Matchers can also be combined with And, Or and Not:
// Match if one matches
q.Or(
  q.Re("Name", "^A"),
  q.Not(
    q.Re("Name", "^B")
  ),
  q.Re("Name", "^C"),
  q.In("Group", []string{"Staff", "Admin"}),
  q.And(
    q.StrictEq("Password", []byte(password)),
    q.Eq("Registered", true)
  )
)

query := db.Select(q.Gte("Age", 7), q.Lte("Age", 77))
// Calls can also be chained
query = query.Limit(10).Skip(20).OrderBy("Age").Reverse()

// But also to specify how to fetch them.
var users []User
err = query.Find(&users)

var user User
err = query.First(&user)


// demo
// Examples with Select:

/ Find all users with an ID between 10 and 100
err = db.Select(q.Gte("ID", 10), q.Lte("ID", 100)).Find(&users)

// Nested matchers
err = db.Select(q.Or(
  q.Gt("ID", 50),
  q.Lt("Age", 21),
  q.And(
    q.Eq("Group", "admin"),
    q.Gte("Age", 21),
  ),
)).Find(&users)

query := db.Select(q.Gte("ID", 10), q.Lte("ID", 100)).Limit(10).Skip(5).Reverse().OrderBy("Age", "Name")

// Find multiple records
err = query.Find(&users)
// or
err = db.Select(q.Gte("ID", 10), q.Lte("ID", 100)).Limit(10).Skip(5).Reverse().OrderBy("Age", "Name").Find(&users)

// Find first record
err = query.First(&user)
// or
err = db.Select(q.Gte("ID", 10), q.Lte("ID", 100)).Limit(10).Skip(5).Reverse().OrderBy("Age", "Name").First(&user)

// Delete all matching records
err = query.Delete(new(User))

// Fetching records one by one (useful when the bucket contains a lot of records)
query = db.Select(q.Gte("ID", 10),q.Lte("ID", 100)).OrderBy("Age", "Name")

err = query.Each(new(User), func(record interface{}) error) {
  u := record.(*User)
  ...
  return nil
}
```

### 事务
```go
tx, err := db.Begin(true)
if err != nil {
  return err
}
defer tx.Rollback()

accountA.Amount -= 100
accountB.Amount += 100

err = tx.Save(accountA)
if err != nil {
  return err
}

err = tx.Save(accountB)
if err != nil {
  return err
}

return tx.Commit()
```

### 不同的数据编码方式
```go
import (
  "github.com/asdine/storm/v3"
  "github.com/asdine/storm/v3/codec/gob"
  "github.com/asdine/storm/v3/codec/json"
  "github.com/asdine/storm/v3/codec/sereal"
  "github.com/asdine/storm/v3/codec/protobuf"
  "github.com/asdine/storm/v3/codec/msgpack"
)

var gobDb, _ = storm.Open("gob.db", storm.Codec(gob.Codec))
var jsonDb, _ = storm.Open("json.db", storm.Codec(json.Codec))
var serealDb, _ = storm.Open("sereal.db", storm.Codec(sereal.Codec))
var protobufDb, _ = storm.Open("protobuf.db", storm.Codec(protobuf.Codec))
var msgpackDb, _ = storm.Open("msgpack.db", storm.Codec(msgpack.Codec))
```
