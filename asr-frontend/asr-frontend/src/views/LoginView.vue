<template>
  <div class="login-container">
    <div class="login-form" 
         @mousemove="handleMouseMove" 
         @mouseleave="handleMouseLeave"
         ref="cardRef"
         :style="cardStyle">
      <div class="logo">🎤</div>
      <h1>基于FunASR和LLM的智能会议系统</h1>
      <div class="form-group">
        <label for="username">用户名</label>
        <div class="input-container">
          <span class="input-icon">👤</span>
          <input type="text" id="username" v-model="form.username" placeholder="请输入用户名" />
        </div>
      </div>
      <div class="form-group">
        <label for="password">密码</label>
        <div class="input-container">
          <span class="input-icon">🔒</span>
          <input type="password" id="password" v-model="form.password" placeholder="请输入密码" />
        </div>
      </div>
      <button @click="login" :disabled="loading" class="login-btn">
        <span v-if="loading" class="loading-spinner"></span>
        {{ loading ? '登录中...' : '登录' }}
      </button>
      <p v-if="error" class="error-message">{{ error }}</p>
    </div>
  </div>
</template>

<script>
import { ref, computed, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { userApi } from '../api/userApi';

export default {
  name: 'LoginView',
  setup() {
    const router = useRouter();
    const form = ref({ username: '', password: '' });
    const loading = ref(false);
    const error = ref('');
    const cardRef = ref(null);
    const transform = reactive({
      rotateX: 0,
      rotateY: 0,
      scale: 1
    });

    const cardStyle = computed(() => {
      return {
        transform: `perspective(1000px) rotateX(${transform.rotateX}deg) rotateY(${transform.rotateY}deg) scale(${transform.scale})`
      };
    });

    const handleMouseMove = (e) => {
      if (!cardRef.value) return;
      
      const rect = cardRef.value.getBoundingClientRect();
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;
      
      const percentX = (mouseX - centerX) / centerX;
      const percentY = (mouseY - centerY) / centerY;
      
      const maxRotate = 8;
      
      transform.rotateX = -percentY * maxRotate;
      transform.rotateY = percentX * maxRotate;
      transform.scale = 0.98;
    };

    const handleMouseLeave = () => {
      transform.rotateX = 0;
      transform.rotateY = 0;
      transform.scale = 1;
    };

    const login = async () => {
      if (!form.value.username || !form.value.password) {
        error.value = '请输入用户名和密码';
        return;
      }

      loading.value = true;
      error.value = '';

      try {
        const response = await userApi.login({
          username: form.value.username,
          password: form.value.password
        });

        // 检查是否有token，有token就表示登录成功
        if (localStorage.getItem('token')) {
          router.push('/home');
        } else {
          error.value = response.detail || '登录失败';
        }
      } catch (err) {
        error.value = '登录失败，请检查网络连接或后端服务';
        console.error('登录错误:', err);
      } finally {
        loading.value = false;
      }
    };

    return {
      form,
      loading,
      error,
      login,
      cardRef,
      cardStyle,
      handleMouseMove,
      handleMouseLeave
    };
  }
};
</script>

<style scoped>
.login-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  background-image: url('/windows-login.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  overflow: hidden;
  z-index: 1;
  perspective: 1000px;
  transform-style: preserve-3d;
}

.login-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.2);
  z-index: 0;
}

.login-form {
  position: relative;
  z-index: 10;
  background: rgba(255, 255, 255, 0.2);
  padding: 40px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  width: 480px;
  transition: transform 0.15s ease-out, box-shadow 0.3s ease;
  transform-style: preserve-3d;
}

.login-form:hover {
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.logo {
  font-size: 48px;
  text-align: center;
  margin-bottom: 20px;
  animation: bounce 2s ease infinite;
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-10px); }
  60% { transform: translateY(-5px); }
}

.login-form h1 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
  font-size: 20px;
  font-weight: 600;
}

.form-group {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 15px;
}

.form-group label {
  width: 80px;
  font-size: 14px;
  color: #999;
  font-weight: 500;
  white-space: nowrap;
}

.form-group .input-container {
  flex: 1;
}

.input-container {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 15px;
  font-size: 16px;
  color: #909399;
}

.form-group input {
  width: 100%;
  padding: 14px 15px 14px 45px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  font-size: 16px;
  transition: all 0.3s ease;
  background-color: #f9f9f9;
}

.form-group input:focus {
  outline: none;
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
  background-color: white;
}

.login-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  margin-top: 20px;
  transition: all 0.3s ease;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
}

.login-btn:hover {
  background: linear-gradient(135deg, #66b1ff 0%, #409eff 100%);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  transform: translateY(-2px);
}

.login-btn:disabled {
  background: linear-gradient(135deg, #c6e2ff 0%, #b3d9ff 100%);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  color: #f56c6c;
  text-align: center;
  margin-top: 15px;
  font-size: 14px;
  background-color: #fef0f0;
  padding: 10px;
  border-radius: 4px;
  border-left: 4px solid #f56c6c;
}
</style>