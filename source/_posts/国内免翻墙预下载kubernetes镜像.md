---
title: 国内免翻墙预下载kubernetes镜像
date: 2018-07-02 15:24:23
tags:
  - linux
  - kubernetes
categories: 系统
permalink: pre-download-kubernetes-image
---

### 当前组件版本信息
组件|变量|版本
:--|:---|:---
k8s版本|K8S_VERSION|v1.11.0
ETCD版本|ETCD_VERSION|3.1.12
Dashboard版本|DASHBOARD_VERSION|v1.8.3
flannel版本|FLANNEL_VERSION|v0.10.0-amd64
DNS版本|DNS_VERSION|1.14.8
PAUSE版本|PAUSE_VERSION|3.1

>需要安装其它版本时，修改这几个变量就好了

### 下载脚本
>把以下内容存为 `pull_k8s_images.sh` 复制到目录机器上执行即可

```shell
### 版本信息
K8S_VERSION=v1.11.0
ETCD_VERSION=3.1.12
DASHBOARD_VERSION=v1.8.3
FLANNEL_VERSION=v0.10.0-amd64
DNS_VERSION=1.14.8
PAUSE_VERSION=3.1
## 基本组件
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kube-apiserver-amd64:$K8S_VERSION
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kube-controller-manager-amd64:$K8S_VERSION
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kube-scheduler-amd64:$K8S_VERSION
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kube-proxy-amd64:$K8S_VERSION
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/etcd-amd64:$ETCD_VERSION
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/pause-amd64:$PAUSE_VERSION
### 网络
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/k8s-dns-sidecar-amd64:$DNS_VERSION
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/k8s-dns-kube-dns-amd64:$DNS_VERSION
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/k8s-dns-dnsmasq-nanny-amd64:$DNS_VERSION
docker pull quay.io/coreos/flannel:$FLANNEL_VERSION
### 前端
docker pull registry.cn-hangzhou.aliyuncs.com/google_containers/kubernetes-dashboard-amd64:$DASHBOARD_VERSION

## 修改tag
docker tag registry.cn-hangzhou.aliyuncs.com/google_containers/kube-apiserver-amd64:$K8S_VERSION k8s.gcr.io/kube-apiserver-amd64:$K8S_VERSION
docker tag registry.cn-hangzhou.aliyuncs.com/google_containers/kube-controller-manager-amd64:$K8S_VERSION k8s.gcr.io/kube-controller-manager-amd64:$K8S_VERSION
docker tag registry.cn-hangzhou.aliyuncs.com/google_containers/kube-scheduler-amd64:$K8S_VERSION k8s.gcr.io/kube-scheduler-amd64:$K8S_VERSION
docker tag registry.cn-hangzhou.aliyuncs.com/google_containers/kube-proxy-amd64:$K8S_VERSION k8s.gcr.io/kube-proxy-amd64:$K8S_VERSION
docker tag registry.cn-hangzhou.aliyuncs.com/google_containers/etcd-amd64:$ETCD_VERSION k8s.gcr.io/etcd-amd64:$ETCD_VERSION
docker tag registry.cn-hangzhou.aliyuncs.com/google_containers/pause-amd64:$PAUSE_VERSION k8s.gcr.io/pause-amd64:$PAUSE_VERSION
docker tag registry.cn-hangzhou.aliyuncs.com/google_containers/k8s-dns-sidecar-amd64:$DNS_VERSION k8s.gcr.io/k8s-dns-sidecar-amd64:$DNS_VERSION
docker tag registry.cn-hangzhou.aliyuncs.com/google_containers/k8s-dns-kube-dns-amd64:$DNS_VERSION k8s.gcr.io/k8s-dns-kube-dns-amd64:$DNS_VERSION
docker tag registry.cn-hangzhou.aliyuncs.com/google_containers/k8s-dns-dnsmasq-nanny-amd64:$DNS_VERSION k8s.gcr.io/k8s-dns-dnsmasq-nanny-amd64:$DNS_VERSION
docker tag registry.cn-hangzhou.aliyuncs.com/google_containers/kubernetes-dashboard-amd64:$DASHBOARD_VERSION k8s.gcr.io/kubernetes-dashboard-amd64:$DASHBOARD_VERSION

## 删除镜像
docker rmi registry.cn-hangzhou.aliyuncs.com/google_containers/kube-apiserver-amd64:$K8S_VERSION
docker rmi registry.cn-hangzhou.aliyuncs.com/google_containers/kube-controller-manager-amd64:$K8S_VERSION
docker rmi registry.cn-hangzhou.aliyuncs.com/google_containers/kube-scheduler-amd64:$K8S_VERSION
docker rmi registry.cn-hangzhou.aliyuncs.com/google_containers/kube-proxy-amd64:$K8S_VERSION
docker rmi registry.cn-hangzhou.aliyuncs.com/google_containers/etcd-amd64:$ETCD_VERSION
docker rmi registry.cn-hangzhou.aliyuncs.com/google_containers/pause-amd64:$PAUSE_VERSION
docker rmi registry.cn-hangzhou.aliyuncs.com/google_containers/k8s-dns-sidecar-amd64:$DNS_VERSION
docker rmi registry.cn-hangzhou.aliyuncs.com/google_containers/k8s-dns-kube-dns-amd64:$DNS_VERSION
docker rmi registry.cn-hangzhou.aliyuncs.com/google_containers/k8s-dns-dnsmasq-nanny-amd64:$DNS_VERSION
docker rmi registry.cn-hangzhou.aliyuncs.com/google_containers/kubernetes-dashboard-amd64:$DASHBOARD_VERSION

```
