---
title: hypyland实现alt + tab切换到任意工作区的窗口
date: 2020-07-21 10:46:26
updated: 2020-08-6 15:08:26
tags:
- hyprland
- wayland
categories: 系统
permalink: hyprland-alt-tab-switch-to-any-widnow
---

>hypyland使用过程中，遇到开了很多工作区和很多窗口时，找指定的窗口会比较麻烦，

### 依赖
- jq
- rofi

### 脚本
把以下脚本存放到`~/.config/hypr/scripts/switch_windows`
```shell
#!/usr/bin/env bash
NAME=`hyprctl clients -j | jq -r '.[] | select(.title != "") | .title' | rofi -dmenu`
WINDOW=`hyprctl clients -j | jq -r ".[] | select(.title == \"${NAME}\") | .address"`
hyprctl dispatch focuswindow address:${WINDOW}
```

添加快捷键
```conf
bind = ALT, Tab, exec, ${HOME}/.config/hypr/scripts/switch_windows
```

### 效果
![截图_2023-10-13_160749](https://github.com/ystyle/ystyle.github.io/assets/4478635/bf28c244-a9ad-4463-92a6-d06b5329c749)
