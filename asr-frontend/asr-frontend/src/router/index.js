import { createRouter, createWebHistory } from 'vue-router';

// 路由配置
const routes = [
  {
    path: '/',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('../views/HomeView.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/home/conference'
      },
      {
        path: 'conference',
        name: 'Conference',
        component: () => import('../views/ConferenceView.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'voiceprint',
        name: 'Voiceprint',
        component: () => import('../views/VoiceprintView.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'template',
        name: 'Template',
        component: () => import('../views/TemplateView.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'user',
        name: 'User',
        component: () => import('../views/UserView.vue'),
        meta: { requiresAuth: true }
      },
      {
        path: 'meeting/:id',
        name: 'MeetingDetail',
        component: () => import('../views/MeetingDetailView.vue'),
        meta: { requiresAuth: true }
      }
    ]
  }
];

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes
});

// 路由守卫
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