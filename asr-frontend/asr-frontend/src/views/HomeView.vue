<template>
  <div class="home-container">
    <!-- 顶部导航栏 -->
    <header class="navbar">
      <div class="navbar-left">
        <h1>基于FunASR和LLM的智能会议系统</h1>
      </div>
      <div class="navbar-right">
        <div class="user-info">
          <div class="user-dropdown" @click="navigateTo('/home/user')">
            <div class="user-avatar">
              <span class="avatar-icon">👤</span>
            </div>
            <span class="username">{{ user?.username || '用户' }}</span>
          </div>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 侧边栏 -->
      <aside class="sidebar">
        <ul>
          <li
            v-for="item in menuItems"
            :key="item.path"
            :class="{ active: currentPath === item.path }"
            @click="navigateTo(item.path)"
          >
            <span class="icon">{{ item.icon }}</span>
            <span>{{ item.label }}</span>
          </li>
        </ul>
      </aside>

      <!-- 内容区域 -->
      <div class="content-area">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { userApi } from '../api/userApi';

export default {
  name: 'HomeView',
  setup() {
    const router = useRouter();
    const route = useRoute();
    const user = ref(null);

    const menuItems = [
      { path: '/home/conference', icon: '📅', label: '会议' },
      { path: '/home/voiceprint', icon: '👤', label: '声纹库' },
      { path: '/home/template', icon: '📄', label: '模板库' },
      { path: '/home/user', icon: '👥', label: '用户' }
    ];

    const currentPath = computed(() => {
      return route.path;
    });

    const loadUserInfo = async () => {
      try {
        const response = await userApi.getProfile();
        console.log('用户信息响应:', response);
        
        // 支持多种响应格式
        if (response.user) {
          user.value = response.user;
        } else if (response.data?.user) {
          user.value = response.data.user;
        } else if (response.data) {
          user.value = response.data;
        }
      } catch (error) {
        console.error('获取用户信息失败:', error);
      }
    };

    const navigateTo = (path) => {
      router.push(path);
    };

    const logout = async () => {
      try {
        await userApi.logout();
      } catch (error) {
        console.warn('退出登录请求失败');
      } finally {
        localStorage.removeItem('token');
        router.push('/');
      }
    };

    onMounted(() => {
      loadUserInfo();
    });

    return {
      user,
      menuItems,
      currentPath,
      navigateTo,
      logout
    };
  }
};
</script>

<style scoped>
.home-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100vh;
  background-color: #f5f7fa;
}

/* 导航栏 */
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 64px;
  background-color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  flex-shrink: 0;
}

.navbar-left h1 {
  font-size: 18px;
  color: #333;
  margin: 0;
  font-weight: 600;
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}



.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.user-dropdown:hover {
  background-color: #f5f7fa;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #66b1ff 0%, #409eff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-icon {
  font-size: 18px;
}

.username {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.btn-logout {
  padding: 6px 16px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  background-color: white;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.btn-logout:hover {
  border-color: #f56c6c;
  color: #f56c6c;
}

/* 主内容区 */
.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* 侧边栏 */
.sidebar {
  width: 96px;
  background-color: white;
  border-right: 1px solid #e4e7ed;
  padding: 16px 0;
  flex-shrink: 0;
}

.sidebar ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.sidebar li {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 8px;
  margin: 4px 8px;
  cursor: pointer;
  color: #909399;
  border-radius: 8px;
  transition: all 0.2s;
}

.sidebar li:hover {
  color: #409eff;
  background-color: #f5f7fa;
}

.sidebar li.active {
  color: #409eff;
  background-color: #ecf5ff;
}

.sidebar .icon {
  font-size: 24px;
  margin-bottom: 4px;
}

.sidebar li span:nth-child(2) {
  font-size: 13px;
}

/* 内容区域 */
.content-area {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
