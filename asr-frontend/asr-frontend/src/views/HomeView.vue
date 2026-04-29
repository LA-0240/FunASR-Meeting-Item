<template>
  <div class="home-container">
    <!-- 顶部导航栏 -->
    <header class="navbar">
      <div class="navbar-left">
        <h1>基于FunASR和LLM的智能会议系统</h1>
      </div>
      <div class="navbar-right">
        <div v-if="isStaff || isSuperuser" class="admin-section">
          <button class="btn-admin" @click="openAdminPanel">
            <span class="admin-icon">🔐</span>
            管理后台
          </button>
        </div>
        <div class="user-info">
          <div class="user-dropdown" @click="navigateTo('/home/user')">
            <div class="user-avatar">
              <img 
                v-if="user?.avatar_url" 
                :src="user.avatar_url.startsWith('http') ? user.avatar_url : `${API_BASE_URL}${user.avatar_url}`"
                alt="头像"
                class="avatar-img"
              />
              <span v-else class="avatar-icon">👤</span>
            </div>
            <span class="username">用户名：{{ user?.username || '用户' }}</span>
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
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { userApi } from '../api/userApi';
import { API_BASE_URL } from '../api/index';

export default {
  name: 'HomeView',
  setup() {
    const router = useRouter();
    const route = useRoute();
    const user = ref(null);

    // 从 localStorage 读取管理员状态
    const isStaff = computed(() => localStorage.getItem('is_staff') === 'true');
    const isSuperuser = computed(() => localStorage.getItem('is_superuser') === 'true');

    const menuItems = [
      { path: '/home/conference', icon: '📅', label: '会议' },
      { path: '/home/voiceprint', icon: '📢', label: '声纹库' },
      { path: '/home/template', icon: '📄', label: '模板库' },
      { path: '/home/user', icon: '👤', label: '用户' }
    ];

    const currentPath = computed(() => {
      return route.path;
    });

    const loadUserInfo = async () => {
      try {
        const response = await userApi.getProfile();
        console.log('用户信息响应:', response);
        
        // 支持多种响应格式
        let userData = null;
        if (response.user_id !== undefined) {
          userData = {
            user_id: response.user_id,
            username: response.username,
            email: response.email,
            created_at: response.created_at,
            avatar_url: response.avatar_url
          };
        } else if (response.user) {
          userData = response.user;
        } else if (response.data?.user) {
          userData = response.data.user;
        } else if (response.data) {
          userData = response.data;
        }
        
        if (userData) {
          user.value = userData;
          // 保存完整用户信息到 localStorage，便于同步
          localStorage.setItem('userInfo', JSON.stringify(userData));
          // 保存最新的管理员状态
          if (response.is_staff !== undefined) {
            localStorage.setItem('is_staff', response.is_staff);
          }
          if (response.is_superuser !== undefined) {
            localStorage.setItem('is_superuser', response.is_superuser);
          }
        }
      } catch (error) {
        console.error('获取用户信息失败:', error);
      }
    };
    
    // 尝试从 localStorage 加载已有用户信息
    const loadUserFromStorage = () => {
      const userInfoStr = localStorage.getItem('userInfo');
      if (userInfoStr) {
        try {
          const userInfo = JSON.parse(userInfoStr);
          user.value = userInfo;
        } catch (e) {
          console.warn('解析用户信息失败', e);
        }
      }
    };

    const navigateTo = (path) => {
      router.push(path);
    };

    const openAdminPanel = () => {
      // 在新标签页打开管理后台
      window.open('http://localhost:8000/admin/', '_blank');
    };

    const logout = async () => {
      try {
        await userApi.logout();
      } catch (error) {
        console.warn('退出登录请求失败');
      } finally {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        localStorage.removeItem('is_staff');
        localStorage.removeItem('is_superuser');
        localStorage.removeItem('userInfo');
        user.value = null;
        router.push('/');
      }
    };

    onMounted(() => {
      // 先从 localStorage 快速加载用户信息
      loadUserFromStorage();
      // 然后从 API 刷新最新信息
      loadUserInfo();
      
      // 监听用户信息更新事件
      const handleUserInfoUpdate = () => {
        // 从 localStorage 加载最新用户信息
        loadUserFromStorage();
        // 同时从 API 刷新
        loadUserInfo();
      };
      window.addEventListener('userInfoUpdated', handleUserInfoUpdate);
      
      // 保存引用以便清理
      window._handleUserInfoUpdate = handleUserInfoUpdate;
    });
    
    // 组件卸载时清理事件监听
    onUnmounted(() => {
      if (window._handleUserInfoUpdate) {
        window.removeEventListener('userInfoUpdated', window._handleUserInfoUpdate);
      }
    });

    return {
      user,
      isStaff,
      isSuperuser,
      menuItems,
      currentPath,
      navigateTo,
      openAdminPanel,
      logout,
      API_BASE_URL
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

.admin-section {
  display: flex;
  align-items: center;
}

.btn-admin {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  background: linear-gradient(135deg, #e6a23c 0%, #f0b442 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(230, 162, 60, 0.3);
}

.btn-admin:hover {
  background: linear-gradient(135deg, #f0b442 0%, #e6a23c 100%);
  box-shadow: 0 4px 12px rgba(230, 162, 60, 0.4);
  transform: translateY(-2px);
}

.admin-icon {
  font-size: 16px;
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
  overflow: hidden;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
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
