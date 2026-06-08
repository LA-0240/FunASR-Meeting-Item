/**
 * 应用路由配置模块
 * 
 * 基于 Vue Router 4 的路由管理文件
 * 负责配置应用的所有页面路由和导航守卫
 * 
 * 主要功能：
 * - 定义应用的路由配置
 * - 配置路由嵌套和子路由
 * - 实现基于 Token 的认证守卫
 * - 管理页面跳转和权限控制
 * 
 * @module router
 */
import { createRouter, createWebHistory } from 'vue-router';

/**
 * 路由配置数组
 * 
 * 定义应用的所有路由规则，包含：
 * - 登录页路由（无需认证）
 * - 主页路由及其子路由（需要认证）
 * - 路由元信息（用于认证控制）
 * 
 * @type {Array<import('vue-router').RouteRecordRaw>}
 */
const routes = [
  // 登录页路由
  {
    path: '/',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  // 主页面路由（包含子路由）
  {
    path: '/home',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
    meta: { requiresAuth: true },
    children: [
      // 默认重定向到会议列表
      {
        path: '',
        redirect: '/home/conference'
      },
      // 会议列表页
      {
        path: 'conference',
        name: 'Conference',
        component: () => import('../views/ConferenceView.vue'),
        meta: { requiresAuth: true }
      },
      // 声纹管理页
      {
        path: 'voiceprint',
        name: 'Voiceprint',
        component: () => import('../views/VoiceprintView.vue'),
        meta: { requiresAuth: true }
      },
      // 模板管理页
      {
        path: 'template',
        name: 'Template',
        component: () => import('../views/TemplateView.vue'),
        meta: { requiresAuth: true }
      },
      // 用户个人中心页
      {
        path: 'user',
        name: 'User',
        component: () => import('../views/UserView.vue'),
        meta: { requiresAuth: true }
      },
      // 会议详情页（带参数）
      {
        path: 'meeting/:id',
        name: 'MeetingDetail',
        component: () => import('../views/MeetingDetailView.vue'),
        meta: { requiresAuth: true }
      }
    ]
  }
];

/**
 * 创建路由实例
 * 
 * 使用 HTML5 History 模式的路由模式
 * 
 * @type {import('vue-router').Router}
 */
const router = createRouter({
  history: createWebHistory(),
  routes
});

/**
 * 全局前置路由守卫
 * 
 * 在每次路由跳转前执行，负责：
 * - 检查目标路由是否需要认证
 * - 验证 localStorage 中是否存在 Token
 * - 根据认证状态进行相应的重定向
 * 
 * @param {import('vue-router').RouteLocationNormalized} to - 目标路由对象
 * @param {import('vue-router').RouteLocationNormalized} from - 来源路由对象
 * @param {import('vue-router').NavigationGuardNext} next - 导航回调函数
 */
router.beforeEach((to, from, next) => {
  // 检查路由是否需要认证
  const requiresAuth = to.meta.requiresAuth;
  // 检查是否有token
  const token = localStorage.getItem('token');
  
  if (requiresAuth && !token) {
    // 需要认证但没有token，重定向到登录页
    next('/');
  } else if (!requiresAuth && token) {
    // 不需要认证但有token，重定向到主页
    next('/home');
  } else {
    // 其他情况正常导航
    next();
  }
});

export default router;
