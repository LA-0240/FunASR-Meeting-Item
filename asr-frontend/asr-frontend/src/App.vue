<template>
  <!-- 路由出口：所有路由匹配的组件都会渲染在这里 -->
  <router-view />
</template>

<script setup>
// 无需额外代码，仅作为路由容器
</script>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: "Microsoft YaHei", sans-serif;
  background-color: #f5f5f5;
}
</style>