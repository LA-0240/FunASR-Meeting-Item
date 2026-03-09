import { createRouter, createWebHistory } from 'vue-router'
// 修复：组件名改为HomeView，对应重命名后的文件
import HomeView from '../views/HomeView.vue'

const routes = [
  {
    path: '/',
    name: 'HomeView',  // 路由名也建议同步修改
    component: HomeView
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router