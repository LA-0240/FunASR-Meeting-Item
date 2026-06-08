
<!--
 * @Description: 用户个人中心组件
 * 包含用户信息展示、头像上传/删除、统计数据展示、
 * 快速操作、用户信息编辑、退出登录等功能
 * @Author: Trae AI
 * @Date: 2026
-->
<template>
  <div class="user-container">
    <div class="user-card">
      <div class="user-avatar-wrapper">
        <div class="user-avatar" @click="triggerAvatarUpload">
          <img 
            v-if="user?.avatar_url" 
            :src="user.avatar_url.startsWith('http') ? user.avatar_url : `${API_BASE_URL}${user.avatar_url}`"
            alt="头像"
            class="avatar-img"
          />
          <span v-else class="avatar-icon">👤</span>
        </div>
        <div class="avatar-actions">
          <button class="avatar-btn" @click="triggerAvatarUpload">
            更换头像
          </button>
          <button v-if="user?.avatar_url" class="avatar-btn avatar-btn-delete" @click="handleDeleteAvatar">
            删除头像
          </button>
        </div>
        <input 
          ref="avatarInput" 
          type="file" 
          accept="image/jpeg,image/png,image/gif" 
          style="display: none" 
          @change="handleAvatarChange"
        />
      </div>
      <div class="user-info" @click="openEditModal">
        <h2 class="user-name">{{ user?.username || '用户' }}</h2>
        <p class="user-email">邮箱：{{ user?.email || '未设置邮箱' }}</p>
        <p class="user-created">注册时间：{{ formatDate(user?.created_at) }}</p>
      </div>
      <div class="edit-icon" @click="openEditModal">✏️</div>
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
        <div class="stat-icon">📢</div>
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

    <!-- 编辑用户信息弹窗 -->
    <div class="modal-overlay" v-if="showEditModal" @click.self="closeEditModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>编辑用户信息</h3>
          <button class="close-btn" @click="closeEditModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>用户名</label>
            <input 
              type="text" 
              v-model="editForm.username" 
              placeholder="请输入用户名"
            />
          </div>
          <div class="form-group">
            <label>邮箱</label>
            <input 
              type="email" 
              v-model="editForm.email" 
              placeholder="请输入邮箱"
            />
          </div>
          <div class="form-group">
            <label>修改密码（留空则不修改）</label>
            <input 
              type="password" 
              v-model="editForm.password" 
              placeholder="请输入新密码"
            />
          </div>
          <div class="form-group" v-if="editForm.password">
            <label>确认密码</label>
            <input 
              type="password" 
              v-model="editForm.confirmPassword" 
              placeholder="请再次输入密码"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="closeEditModal">取消</button>
          <button class="confirm-btn" @click="handleSave" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>


  </div>
</template>

<script>
/**
 * UserView 组件 - 用户个人中心
 * 展示用户信息、统计数据,支持头像管理、信息编辑、快速导航等功能
 */
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { userApi } from '../api/userApi';
import { fileApi } from '../api/fileApi';
import { voiceprintApi } from '../api/voiceprintApi';
import { promptApi } from '../api/promptApi';
import { API_BASE_URL } from '../api/index';

export default {
  name: 'UserView',
  setup() {
    const router = useRouter();
    // 用户信息
    const user = ref(null);
    // 统计数据
    const fileCount = ref(0);
    const voiceprintCount = ref(0);
    const templateCount = ref(0);
    const loading = ref(true);
    
    // 头像上传相关
    const avatarInput = ref(null);
    const uploadingAvatar = ref(false);
    
    // 编辑弹窗相关
    const showEditModal = ref(false);
    const editForm = ref({
      username: '',
      email: '',
      password: '',
      confirmPassword: ''
    });
    const saving = ref(false);

    /**
     * 显示Toast提示消息
     * @param {string} msg - 提示消息内容
     * @param {string} type - 提示类型 (success/error)
     */
    const showToastMsg = (msg, type = 'success') => {
      console.log('🎯 显示提示弹窗:', msg, type);
      
      const toast = document.createElement('div');
      toast.className = `toast toast-${type}`;
      toast.textContent = msg;
      document.body.appendChild(toast);
      
      // 显示动画
      setTimeout(() => {
        toast.classList.add('show');
      }, 10);
      
      // 自动消失（2秒）
      setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
          if (document.body.contains(toast)) {
            document.body.removeChild(toast);
          }
        }, 300);
      }, 2000);
    };

    /**
     * 触发头像上传
     * 点击隐藏的文件输入框
     */
    const triggerAvatarUpload = () => {
      avatarInput.value?.click();
    };

    /**
     * 处理头像文件选择和上传
     * @param {Event} e - 文件选择事件
     */
    const handleAvatarChange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      
      // 验证文件类型
      const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
      if (!allowedTypes.includes(file.type)) {
        showToastMsg('只支持 JPG、PNG、GIF 格式的图片', 'error');
        return;
      }
      
      // 验证文件大小（5MB）
      if (file.size > 5 * 1024 * 1024) {
        showToastMsg('图片大小不能超过 5MB', 'error');
        return;
      }
      
      uploadingAvatar.value = true;
      try {
        const response = await userApi.uploadAvatar(file);
        if (response.status === 'success') {
          showToastMsg('头像上传成功', 'success');
          // 重新加载用户信息
          await loadData();
          // 发送事件通知其他组件刷新用户信息
          window.dispatchEvent(new CustomEvent('userInfoUpdated'));
        } else {
          showToastMsg(response.detail || '头像上传失败', 'error');
        }
      } catch (error) {
        console.error('头像上传失败:', error);
        showToastMsg(error.detail || '头像上传失败，请稍后重试', 'error');
      } finally {
        uploadingAvatar.value = false;
        // 清空文件输入
        if (avatarInput.value) {
          avatarInput.value.value = '';
        }
      }
    };

    /**
     * 删除用户头像
     */
    const handleDeleteAvatar = async () => {
      if (!confirm('确定要删除头像吗？')) return;
      
      try {
        const response = await userApi.deleteAvatar();
        if (response.status === 'success') {
          showToastMsg('头像删除成功', 'success');
          // 重新加载用户信息
          await loadData();
          // 发送事件通知其他组件刷新用户信息
          window.dispatchEvent(new CustomEvent('userInfoUpdated'));
        } else {
          showToastMsg(response.detail || '头像删除失败', 'error');
        }
      } catch (error) {
        console.error('头像删除失败:', error);
        showToastMsg(error.detail || '头像删除失败，请稍后重试', 'error');
      }
    };

    /**
     * 加载用户数据
     * 包括用户信息、文件数量、声纹数量、模板数量
     */
    const loadData = async () => {
      loading.value = true;
      try {
        // 加载用户信息
        try {
          const userResponse = await userApi.getProfile();
          console.log('用户信息响应:', userResponse);
          
          let userData = null;
          if (userResponse.user_id !== undefined) {
            userData = {
              user_id: userResponse.user_id,
              username: userResponse.username,
              email: userResponse.email,
              created_at: userResponse.created_at,
              avatar_url: userResponse.avatar_url
            };
          } else if (userResponse.data?.user) {
            userData = userResponse.data.user;
          } else if (userResponse.data) {
            userData = userResponse.data;
          } else if (userResponse.user) {
            userData = userResponse.user;
          }
          
          if (userData) {
            user.value = userData;
            // 保存完整用户信息到 localStorage，便于同步
            localStorage.setItem('userInfo', JSON.stringify(userData));
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

    /**
     * 退出登录
     */
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

    /**
     * 导航到指定页面
     * @param {string} path - 路径标识 (voiceprint/template/home)
     */
    const goTo = (path) => {
      const pathMap = {
        voiceprint: '/home/voiceprint',
        template: '/home/template',
        home: '/home'
      };
      router.push(pathMap[path] || '/home');
    };

    /**
     * 格式化日期
     * @param {string} dateStr - 日期字符串
     * @returns {string} 格式化后的日期
     */
    const formatDate = (dateStr) => {
      if (!dateStr) return '未知';
      const date = new Date(dateStr);
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      });
    };

    /**
     * 打开编辑用户信息弹窗
     */
    const openEditModal = () => {
      editForm.value = {
        username: user.value?.username || '',
        email: user.value?.email || '',
        password: '',
        confirmPassword: ''
      };
      showEditModal.value = true;
    };

    /**
     * 关闭编辑用户信息弹窗
     */
    const closeEditModal = () => {
      showEditModal.value = false;
      editForm.value = {
        username: '',
        email: '',
        password: '',
        confirmPassword: ''
      };
    };

    /**
     * 保存用户信息
     * 验证表单并调用更新API
     */
    const handleSave = async () => {
      // 验证密码
      if (editForm.value.password && editForm.value.password !== editForm.value.confirmPassword) {
        showToastMsg('两次输入的密码不一致', 'error');
        return;
      }
      
      if (editForm.value.password && editForm.value.password.length < 6) {
        showToastMsg('密码长度不能少于6位', 'error');
        return;
      }

      saving.value = true;
      try {
        const updateData = {};
        if (editForm.value.username && editForm.value.username !== user.value?.username) {
          updateData.username = editForm.value.username;
        }
        if (editForm.value.email && editForm.value.email !== user.value?.email) {
          updateData.email = editForm.value.email;
        }
        if (editForm.value.password) {
          updateData.password = editForm.value.password;
        }

        const response = await userApi.updateProfile(updateData);
        console.log('更新响应:', response);
        
        if (response.status === 'success') {
          showToastMsg('用户信息更新成功', 'success');
          // 更新本地用户数据
          if (updateData.username) user.value.username = updateData.username;
          if (updateData.email) user.value.email = updateData.email;
          closeEditModal();
        } else {
          showToastMsg(response.detail || '更新失败', 'error');
        }
      } catch (error) {
        console.error('更新失败:', error);
        showToastMsg(error.detail || '更新失败，请稍后重试', 'error');
      } finally {
        saving.value = false;
      }
    };

    /**
     * 组件挂载时加载数据
     */
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
      handleLogout,
      showEditModal,
      editForm,
      saving,
      openEditModal,
      closeEditModal,
      handleSave,
      // 头像相关
      avatarInput,
      uploadingAvatar,
      triggerAvatarUpload,
      handleAvatarChange,
      handleDeleteAvatar,
      API_BASE_URL
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
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
}

.user-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.user-avatar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
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
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
}

.user-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-icon {
  font-size: 48px;
}

.avatar-actions {
  display: flex;
  gap: 8px;
}

.avatar-btn {
  padding: 6px 16px;
  border: 1px solid #409eff;
  border-radius: 6px;
  background: white;
  color: #409eff;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.avatar-btn:hover {
  background: #409eff;
  color: white;
}

.avatar-btn-delete {
  border-color: #f56c6c;
  color: #f56c6c;
}

.avatar-btn-delete:hover {
  background: #f56c6c;
  color: white;
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
  color: #666;
}

.user-created {
  margin: 0;
  font-size: 13px;
  color: #999;
}

.edit-icon {
  font-size: 20px;
  color: #409eff;
  opacity: 0.6;
}

.user-card:hover .edit-icon {
  opacity: 1;
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

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 16px;
  width: 480px;
  max-width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: #999;
  line-height: 1;
}

.modal-body {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.form-group input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  box-sizing: border-box;
  transition: all 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #409eff;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #eee;
}

.cancel-btn,
.confirm-btn {
  padding: 12px 32px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn {
  background: #f5f7fa;
  color: #666;
}

.cancel-btn:hover {
  background: #e8eaed;
}

.confirm-btn {
  background: linear-gradient(135deg, #66b1ff 0%, #409eff 100%);
  color: white;
}

.confirm-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
}

.confirm-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Toast 样式 */
:global(.toast) {
  position: fixed;
  top: 100px;
  left: 50%;
  transform: translate(-50%, -20px);
  padding: 16px 32px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 500;
  z-index: 9999;
  opacity: 0;
  transition: all 0.3s ease;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  text-align: center;
  min-width: 200px;
  max-width: 80%;
}

:global(.toast.show) {
  opacity: 1;
  transform: translate(-50%, 0);
}

:global(.toast-success) {
  background: #f0f9ff;
  color: #409eff;
  border: 1px solid #b3d8ff;
}

:global(.toast-error) {
  background: #fef0f0;
  color: #f56c6c;
  border: 1px solid #fde2e2;
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
