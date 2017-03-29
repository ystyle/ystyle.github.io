---
title: '纯css固定表头[表体垂直滚动]'
permalink: chun-cssgu-ding-biao-tou-biao-ti-chui-zhi-gun-dong
id: 46
updated: '2017-02-23 15:46:00'
tags:
---

### HTML
```
<div class="table-container">
    <table>
        <thead>
            <tr>
                <th>head1</th>
                <th>head2</th>
                <th>head3</th>
                <th>head4</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>content1</td>
                <td>content2</td>
                <td>content3</td>
                <td>content4</td>
            </tr>
            <tr>
                <td>content1</td>
                <td>content2</td>
                <td>content3</td>
                <td>content4</td>
            </tr>
            <tr>
                <td>content1</td>
                <td>content2</td>
                <td>content3</td>
                <td>content4</td>
            </tr>
            <tr>
                <td>content1</td>
                <td>content2</td>
                <td>content3</td>
                <td>content4</td>
            </tr>
            <tr>
                <td>content1</td>
                <td>content2</td>
                <td>content3</td>
                <td>content4</td>
            </tr>
            <tr>
                <td>content1</td>
                <td>content2</td>
                <td>content3</td>
                <td>content4</td>
            </tr>
        </tbody>
    </table>
</div>
```

### CSS
```css
.table-container {
    height: 10em;
}
table {
    display: flex;
    flex-flow: column;
    height: 100%;
    width: 100%;
}
table thead {
    flex: 0 0 auto;
    width: calc(100% - 0.9em);
}
table tbody {
    flex: 1 1 auto;
    display: block;
    overflow-y: scroll;
}
table tbody tr {
    width: 100%;
}
table thead,
table tbody tr {
    display: table;
    table-layout: fixed;
}
/* 以下为调整表格显示的样式 */
.table-container {
    border: 1px solid black;
    padding: 0.3em;
}
table {
    border: 1px solid lightgrey;
}
table td, table th {
    padding: 0.3em;
    border: 1px solid lightgrey;
}
table th {
    border: 1px solid grey;
}
```