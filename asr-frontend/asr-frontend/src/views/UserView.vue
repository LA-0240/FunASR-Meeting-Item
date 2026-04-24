<template>
  <div class="user-container">
    <div class="user-card">
      <div class="user-avatar">
        <span class="avatar-icon">👤</span>
      </div>
      <div class="user-info">
        <h2 class="user-name">{{ user?.username || '用户' }}</h2>
        <p class="user-email">{{ user?.email || '未设置邮箱' }}</p>
        <p class="user-created">注册时间：{{ formatDate(user?.created_at) }}</p>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📁</div>
        <div class="stat-content">
          <div class="stat-value">{{ fileCount }}</div>
          <div class="stat-label">文件数量</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">👤</div>
        <div class="stat-content">
          <div class="stat-value">{{ voiceprintCount }}</div>
          <div class="stat-label">声纹数量</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📄</div>
        <div class="stat-content">
          <div class="stat-value">{{ templateCount }}</div>
          <div class="stat-label">模板数量</div>
        </div>
      </div>
    </div>

    <div class="actions-section">
      <h3>快速操作</h3>
      <div class="action-buttons">
        <button class="action-btn" @click="goTo('voiceprint')">
          <span class="icon">👤</span>
          <span>管理声纹库</span>
        </button>
        <button class="action-btn" @click="goTo('template')">
          <span class="icon">📄</span>
          <span>管理模板库</span>
        </button>
        <button class="action-btn" @click="goTo('home')">
          <span class="icon">📅</span>
          <span>查看会议文件</span>
        </button>
      </div>
    </div>

    <div class="logout-section">
      <button class="btn-logout" @click="handleLogout">
        <span class="logout-icon">🚪</span>
        <span>退出登录</span>
      </button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { userApi } from '../api/userApi';
import { fileApi } from '../api/fileApi';
import { voiceprintApi } from '../api/voiceprintApi';
import { promptApi } from '../api/promptApi';

export default {
  name: 'UserView',
  setup() {
    const router = useRouter();
    const user = ref(null);
    const fileCount = ref(0);
    const voiceprintCount = ref(0);
    const templateCount = ref(0);
    const loading = ref(true);

    const loadData = async () => {
      loading.value = true;
      try {
        // 加载用户信息
        try {
          const userResponse = await userApi.getProfile();
          console.log('用户信息响应:', userResponse);
          if (userResponse.user) {
            user.value = userResponse.user;
          } else if (userResponse.data?.user) {
            user.value = userResponse.data.user;
          } else if (userResponse.data) {
            user.value = userResponse.data;
          }
        } catch (e) {
          console.warn('获取用户信息失败');
        }

        // 加载文件数量
        try {
          const fileResponse = await fileApi.getList();
          console.log('文件列表响应:', fileResponse);
          if (fileResponse.files && Array.isArray(fileResponse.files)) {
            fileCount.value = fileResponse.files.length;
          } else if (fileResponse.data?.files && Array.isArray(fileResponse.data.files)) {
            fileCount.value = fileResponse.data.files.length;
          } else if (Array.isArray(fileResponse.data)) {
            fileCount.value = fileResponse.data.length;
          } else if (Array.isArray(fileResponse)) {
            fileCount.value = fileResponse.length;
          }
        } catch (e) {
          console.warn('获取文件列表失败');
        }

        // 加载声纹数量
        try {
          const vpResponse = await voiceprintApi.getList();
          console.log('声纹列表响应:', vpResponse);
          if (vpResponse.voiceprints && Array.isArray(vpResponse.voiceprints)) {
            voiceprintCount.value = vpResponse.voiceprints.length;
          } else if (vpResponse.data?.voiceprints && Array.isArray(vpResponse.data.voiceprints)) {
            voiceprintCount.value = vpResponse.data.voiceprints.length;
          } else if (Array.isArray(vpResponse.data)) {
            voiceprintCount.value = vpResponse.data.length;
          } else if (Array.isArray(vpResponse)) {
            voiceprintCount.value = vpResponse.length;
          }
        } catch (e) {
          console.warn('获取声纹列表失败');
        }

        // 加载模板数量
        try {
          const promptResponse = await promptApi.getList();
          console.log('模板列表响应:', promptResponse);
          if (promptResponse.prompts && Array.isArray(promptResponse.prompts)) {
            templateCount.value = promptResponse.prompts.length;
          } else if (promptResponse.data?.prompts && Array.isArray(promptResponse.data.prompts)) {
            templateCount.value = promptResponse.data.prompts.length;
          } else if (Array.isArray(promptResponse.data)) {
            templateCount.value = promptResponse.data.length;
          } else if (Array.isArray(promptResponse)) {
            templateCount.value = promptResponse.length;
          }
        } catch (e) {
          console.warn('获取模板列表失败');
        }
      } finally {
        loading.value = false;
      }
    };

    const handleLogout = async () => {
      try {
        await userApi.logout();
      } catch (error) {
        console.warn('退出登录请求失败');
      } finally {
        localStorage.removeItem('token');
        router.push('/');
      }
    };

    const goTo = (path) => {
      const pathMap = {
        voiceprint: '/home/voiceprint',
        template: '/home/template',
        home: '/home'
      };
      router.push(pathMap[path] || '/home');
    };

    const formatDate = (dateStr) => {
      if (!dateStr) return '未知';
      const date = new Date(dateStr);
      return date.toLocaleDateString('zh-CN');
    };

    onMounted(() => {
      loadData();
    });

    return {
      user,
      fileCount,
      voiceprintCount,
      templateCount,
      loading,
      goTo,
      formatDate,
      handleLogout
    };
  }
};
</script>

<style scoped>
.user-container {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.user-card {
  background: white;
  border-radius: 16px;
  padding: 32px;
  display: flex;
  align-items: center;
  gap: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  margin-bottom: 24px;
}

.user-avatar {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: linear-gradient(135deg, #66b1ff 0%, #409eff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-icon {
  font-size: 48px;
}

.user-info {
  flex: 1;
}

.user-name {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.user-email {
  margin: 0 0 8px;
  font-size: 14px;
  color: #999;
}

.user-created {
  margin: 0;
  font-size: 13px;
  color: #999;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  transition: all 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: #f0f9ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #999;
}

.actions-section {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.actions-section h3 {
  margin: 0 0 20px;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.action-buttons {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px 16px;
  background: #f5f7fa;
  border: 2px solid transparent;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  color: #666;
}

.action-btn:hover {
  background: #e6f7ff;
  border-color: #409eff;
  color: #409eff;
}

.action-btn .icon {
  font-size: 32px;
}

.logout-section {
  margin-top: 32px;
  text-align: center;
}

.btn-logout {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 14px 48px;
  background: linear-gradient(135deg, #f56c6c 0%, #e64343 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(245, 108, 108, 0.3);
}

.btn-logout:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(245, 108, 108, 0.4);
}

.btn-logout:active {
  transform: translateY(0);
}

.logout-icon {
  font-size: 18px;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .action-buttons {
    grid-template-columns: 1fr;
  }

  .user-card {
    flex-direction: column;
    text-align: center;
  }
}
</style>
