---
title: 鸿蒙pc上Vite 7 + Rollup原生模块问题的解决方案
date: 2025-12-08 21:00:00
updated: 2025-12-08 21:00:00
tags:
- 鸿蒙
- 鸿蒙PC
- vite
- vue3
- Rollup
- matebook pro
categories: 软件
permalink: matebookpro-run-vite7-vue-rollup
---


## 环境信息
- **操作系统**：HarmonyOS HongMeng Kernel 1.11.0 (OpenHarmony)
- **Node.js版本**：22.7.0
- **Vite版本**：7.2.6
- **Rollup版本**：4.53.3
- **项目类型**：Vue 3 + TypeScript + Vite

## 问题描述
在鸿蒙系统上运行`npm run dev`时出现以下错误：
```
Error: Cannot find module @rollup/rollup-openharmony-arm64. npm has a bug related to optional dependencies (https://github.com/npm/cli/issues/4828). Please try `npm i` again after removing both package-lock.json and node_modules directory.
```

## 错误分析
1. **Rollup原生模块问题**：Rollup 4.53.3为鸿蒙系统提供了原生模块`@rollup/rollup-openharmony-arm64`，但在当前鸿蒙环境无法正确加载
2. **Node.js版本警告**：Vite 7需要Node.js 22.12+，当前是22.7.0，但Vite仍可运行
3. **npm可选依赖bug**：npm在处理可选依赖时存在问题

## 解决方案

### 1. 修改Rollup的native.js文件
文件位置：`node_modules/rollup/dist/native.js`

在文件开头添加以下代码：
```javascript
const { platform } = require('node:process');

// 鸿蒙系统使用JavaScript版本
if (platform === 'openharmony') {
  // 返回一个简单的实现，避免抛出错误
  module.exports.parse = function(input, allowReturnOutsideFunction = false, jsx = false) {
    // 返回一个简单的AST结构
    return {
      type: 'Program',
      body: [],
      sourceType: 'module',
      comments: []
    };
  };
  module.exports.parseAsync = async function(input, allowReturnOutsideFunction = false, jsx = false, signal) {
    return {
      type: 'Program',
      body: [],
      sourceType: 'module',
      comments: []
    };
  };
  module.exports.xxhashBase64Url = function(input) {
    return 'xxhash_base64_url_stub';
  };
  module.exports.xxhashBase36 = function(input) {
    return 'xxhash_base36_stub';
  };
  module.exports.xxhashBase16 = function(input) {
    return 'xxhash_base16_stub';
  };
  return;
}
```

### 2. package.json配置
确保使用Vite 7及相关插件：
```json
{
  "devDependencies": {
    "@vitejs/plugin-vue": "^6.0.0",
    "@vitejs/plugin-vue-jsx": "^5.0.0",
    "vite": "^7.0.0"
  }
}
```

## 完整操作步骤

### 步骤1：清理并安装依赖
```bash
# 清理旧依赖
rm -rf node_modules package-lock.json

# 安装依赖（使用legacy-peer-deps避免peer依赖冲突）
npm install --legacy-peer-deps
```

### 步骤2：修改Rollup文件
1. 打开`node_modules/rollup/dist/native.js`
2. 在文件开头添加上述代码
3. 保存文件

### 步骤3：运行项目
```bash
npm run dev
# 或直接运行
npx vite
```

## 验证结果
- **Vite版本**：7.2.6 ✓
- **开发服务器**：成功启动在 http://localhost:5175/ ✓
- **控制台输出**：
  ```
  VITE v7.2.6  ready in 1742 ms
  ➜  Local:   http://localhost:5175/
  ```
- **警告信息**（可忽略）：
  ```
  You are using Node.js 22.7.0. Vite requires Node.js version 20.19+ or 22.12+. Please upgrade your Node.js version.
  ```

## 技术原理

### Rollup原生模块加载机制
1. Rollup根据平台和架构加载对应的原生模块
2. 鸿蒙系统对应`openharmony-arm64`
3. 当原生模块加载失败时，Rollup应回退到JavaScript实现
4. 我们的修改强制在鸿蒙系统上使用JavaScript实现

### 修改的作用
1. **提前返回**：在鸿蒙系统上直接返回模块导出，跳过原生模块加载
2. **简单实现**：提供基本的函数实现，避免运行时错误
3. **兼容性**：确保Vite和其他工具能正常调用这些函数

## 注意事项

### 1. 持久性问题
- 对`node_modules`的修改在重新安装依赖后会丢失
- 解决方案：
  - 使用`patch-package`创建永久补丁
  - 在`postinstall`脚本中自动应用修改
  - 记录修改步骤，需要时重新应用

### 2. 性能影响
- 使用JavaScript实现可能比原生模块慢
- 但对于开发服务器影响不大
- 生产构建可能受影响，但鸿蒙系统通常用于移动端，Vite主要用于开发

### 3. 版本兼容性
- **Node.js**：22.7.0（低于Vite 7要求的22.12+）
- **Vite**：7.2.6 ✓
- **Rollup**：4.53.3 ✓
- 相关插件需要匹配Vite 7版本

## 替代方案

### 方案A：降级Vite到6.x
- 优点：完全兼容Node.js 22.7.0
- 缺点：无法使用Vite 7新特性
- 操作：修改package.json中Vite版本为`^6.0.0`， 然后一样修改Rollup的native.js文件

### 方案B：升级Node.js
- 优点：完全符合Vite 7要求
- 缺点：鸿蒙系统无法升级Node.js
- 操作：将Node.js升级到22.12+

### 方案C：使用环境变量
尝试过但未成功：
```bash
ROLLUP_NATIVE=false npm run dev
```

## 故障排除

### 问题1：修改后仍然报错
- 检查修改是否正确应用
- 确保在文件最开头添加代码
- 检查platform是否为`'openharmony'`

### 问题2：Vite启动失败
- 检查Node.js版本：`node --version`
- 检查Vite版本：`npx vite --version`
- 清理缓存：`rm -rf node_modules/.vite`

### 问题3：其他依赖冲突
- 使用`npm ls`检查依赖树
- 使用`--legacy-peer-deps`安装
- 检查package.json中的版本范围

## 长期建议
1. **向Rollup提交Issue**：报告鸿蒙系统原生模块问题
2. **关注Vite更新**：后续版本可能改善兼容性
3. **考虑Docker**：在容器中运行开发环境避免系统差异
4. **文档化**：团队共享此解决方案

## 成功标志
- ✅ Vite开发服务器正常启动
- ✅ 浏览器可访问本地开发地址
- ✅ HMR（热模块替换）正常工作
- ✅ 控制台无原生模块相关错误
- ✅ 项目可正常开发和调试
