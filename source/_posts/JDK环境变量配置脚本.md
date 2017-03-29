---
title: JDK环境变量配置脚本
tags:
  - JAVA
categories: 系统
permalink: jdkhuan-jing-bian-liang-pei-zhi-jiao-ben
id: 11
updated: '2015-11-02 16:40:22'
date: 2015-06-21 21:16:17
---

复制到jdk安装目录,右键以powershell运行

```powershell
#region 强制以管理员权限运行
$currentWi = [Security.Principal.WindowsIdentity]::GetCurrent()
$currentWp = [Security.Principal.WindowsPrincipal]$currentWi
if( -not $currentWp.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))
{
    $boundPara = ($MyInvocation.BoundParameters.Keys | foreach{'-{0} {1}' -f  $_ ,$MyInvocation.BoundParameters[$_]} ) -join ' '
    $currentFile = $MyInvocation.MyCommand.Definition
    $fullPara = $boundPara + ' ' + $args -join ' '
    Start-Process "$psHome\powershell.exe"   -ArgumentList "$currentFile $fullPara" -verb runas
    return
}
#endregion

#region 初始化应用
$currPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
cd $currPath
$isJDKJavac = Test-Path "./bin/javac.exe"
$isJREJava = Test-Path "./bin/java.exe"
$path = [environment]::GetEnvironmentvariable("path", "Machine")
if($path.Length>0){
    $temp = ";"
}else{
    $temp = ""
}
#endregion

#region 配置环境变量
if($isJDKJavac){
    echo "检测到./bin/javac编译器..."
    echo "设置环境变量：JAVA_HOME = $currPath"
    [environment]::SetEnvironmentvariable("JAVA_HOME", $currPath, "Machine")
    echo "设置环境变量：PATH = %JAVA_HOME%\bin;"
    [environment]::SetEnvironmentvariable("path", $path + $temp + "%JAVA_HOME%\bin;", "Machine")
}elseif($isJREJava){
    echo "检测到./jre/java运行环境..."
    echo "设置环境变量：PATH = $currPath\bin"
    [environment]::SetEnvironmentvariable("path", $path + $temp + $currPath+"\bin;", "Machine")
}else{
    echo "没有检测到JAVA环境"
}
#endregion
pause
```

复制到文件另存为run.sp1

网盘下载：[`链接`](http://pan.baidu.com/s/1jG07KFk) 密码：`27uj`
