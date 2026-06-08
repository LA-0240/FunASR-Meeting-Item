
<!--
 * @Description: 登录/注册页面组件
 * 使用翻转卡片效果实现登录和注册界面的切换,
 * 包含用户登录、注册功能,支持表单验证、加载状态等
 * @Author: Trae AI
 * @Date: 2026
-->
<template>
  <div class="login-container">
    <div class="flip-card" :class="{ 'flipped': isFlipped }">
      <div class="flip-card-inner">
        <!-- 登录卡片（正面） -->
        <div class="card-front">
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
                <input type="text" id="username" v-model="loginForm.username" placeholder="请输入用户名" />
              </div>
            </div>
            <div class="form-group">
              <label for="password">密码</label>
              <div class="input-container">
                <span class="input-icon">🔒</span>
                <input type="password" id="password" v-model="loginForm.password" placeholder="请输入密码" />
              </div>
            </div>
            <button @click="login" :disabled="loginLoading" class="login-btn">
              <span v-if="loginLoading" class="loading-spinner"></span>
              {{ loginLoading ? '登录中...' : '登录' }}
            </button>
            <p v-if="loginError" class="error-message">{{ loginError }}</p>
          </div>
          <!-- 右侧翻转箭头 -->
          <div class="flip-arrow arrow-right" @click="toggleFlip">
            <span class="arrow-icon">→</span>
          </div>
        </div>

        <!-- 注册卡片（背面） -->
        <div class="card-back">
          <div class="login-form register-form" 
               @mousemove="handleMouseMove" 
               @mouseleave="handleMouseLeave"
               ref="cardRef"
               :style="cardStyle">
            <div class="logo">🎤</div>
            <h1>用户注册</h1>
            <div class="form-group">
              <label for="reg-username">用户名</label>
              <div class="input-container">
                <span class="input-icon">👤</span>
                <input type="text" id="reg-username" v-model="registerForm.username" placeholder="请输入用户名" />
              </div>
            </div>
            <div class="form-group">
              <label for="reg-email">邮箱</label>
              <div class="input-container">
                <span class="input-icon">📧</span>
                <input type="email" id="reg-email" v-model="registerForm.email" placeholder="请输入邮箱" />
              </div>
            </div>
            <div class="form-group">
              <label for="reg-password">密码</label>
              <div class="input-container">
                <span class="input-icon">🔒</span>
                <input type="password" id="reg-password" v-model="registerForm.password" placeholder="请输入密码" />
              </div>
            </div>
            <div class="form-group">
              <label for="reg-password2">确认密码</label>
              <div class="input-container">
                <span class="input-icon">🔒</span>
                <input type="password" id="reg-password2" v-model="registerForm.password2" placeholder="请再次输入密码" />
              </div>
            </div>
            <button @click="register" :disabled="registerLoading" class="register-btn">
              <span v-if="registerLoading" class="loading-spinner"></span>
              {{ registerLoading ? '注册中...' : '注册' }}
            </button>
            <p v-if="registerError" class="error-message">{{ registerError }}</p>
            <p v-if="registerSuccess" class="success-message">{{ registerSuccess }}</p>
          </div>
          <!-- 左侧翻转箭头 -->
          <div class="flip-arrow arrow-left" @click="toggleFlip">
            <span class="arrow-icon">←</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * LoginView 组件 - 登录/注册页面
 * 提供用户登录和注册功能,使用翻转动画切换表单
 */
import { ref, computed, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { userApi } from '../api/userApi';

export default {
  name: 'LoginView',
  setup() {
    const router = useRouter();
    
    // 登录表单数据
    const loginForm = ref({ username: '', password: '' });
    // 注册表单数据
    const registerForm = ref({ username: '', email: '', password: '', password2: '' });
    // 加载状态
    const loginLoading = ref(false);
    const registerLoading = ref(false);
    // 错误提示
    const loginError = ref('');
    const registerError = ref('');
    const registerSuccess = ref('');
    // 卡片翻转状态
    const isFlipped = ref(false);
    // 卡片DOM引用
    const cardRef = ref(null);
    // 卡片变换参数
    const transform = reactive({
      rotateX: 0,
      rotateY: 0,
      scale: 1
    });

    /**
     * 计算卡片样式 - 实现3D变换效果
     */
    const cardStyle = computed(() => {
      return {
        transform: `perspective(1000px) rotateX(${transform.rotateX}deg) rotateY(${transform.rotateY}deg) scale(${transform.scale})`
      };
    });

    /**
     * 切换登录/注册卡片
     */
    const toggleFlip = () => {
      isFlipped.value = !isFlipped.value;
      loginError.value = '';
      registerError.value = '';
      registerSuccess.value = '';
    };

    /**
     * 处理鼠标移动 - 实现卡片跟随鼠标倾斜的3D效果
     * @param {Event} e - 鼠标事件
     */
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

    /**
     * 处理鼠标离开 - 重置卡片变换
     */
    const handleMouseLeave = () => {
      transform.rotateX = 0;
      transform.rotateY = 0;
      transform.scale = 1;
    };

    /**
     * 用户登录
     * 验证表单,调用登录API,成功后跳转到首页
     */
    const login = async () => {
      if (!loginForm.value.username || !loginForm.value.password) {
        loginError.value = '请输入用户名和密码';
        return;
      }

      loginLoading.value = true;
      loginError.value = '';

      try {
        const response = await userApi.login({
          username: loginForm.value.username,
          password: loginForm.value.password
        });

        if (localStorage.getItem('token')) {
          router.push('/home');
        } else {
          loginError.value = response.detail || '登录失败';
        }
      } catch (err) {
        loginError.value = '登录失败，请检查网络连接或后端服务';
        console.error('登录错误:', err);
      } finally {
        loginLoading.value = false;
      }
    };

    /**
     * 用户注册
     * 验证表单,调用注册API,成功后自动切换到登录页
     */
    const register = async () => {
      if (!registerForm.value.username || !registerForm.value.password || !registerForm.value.email) {
        registerError.value = '请填写所有必填项';
        return;
      }

      if (registerForm.value.password !== registerForm.value.password2) {
        registerError.value = '两次输入的密码不一致';
        return;
      }

      if (registerForm.value.password.length < 6) {
        registerError.value = '密码长度至少6位';
        return;
      }

      registerLoading.value = true;
      registerError.value = '';
      registerSuccess.value = '';

      try {
        const response = await userApi.register({
          username: registerForm.value.username,
          email: registerForm.value.email,
          password: registerForm.value.password
        });

        registerSuccess.value = '注册成功！请登录';
        
        setTimeout(() => {
          isFlipped.value = false;
          loginForm.value.username = registerForm.value.username;
          registerForm.value = { username: '', email: '', password: '', password2: '' };
          registerSuccess.value = '';
        }, 1500);
      } catch (err) {
        if (err.response?.data) {
          const data = err.response.data;
          if (data.username) {
            registerError.value = `用户名错误: ${data.username.join(', ')}`;
          } else if (data.email) {
            registerError.value = `邮箱错误: ${data.email.join(', ')}`;
          } else if (data.password) {
            registerError.value = `密码错误: ${data.password.join(', ')}`;
          } else if (data.detail) {
            registerError.value = data.detail;
          } else {
            registerError.value = '注册失败，请检查输入';
          }
        } else {
          registerError.value = '注册失败，请检查网络连接或后端服务';
        }
        console.error('注册错误:', err);
      } finally {
        registerLoading.value = false;
      }
    };

    return {
      loginForm,
      registerForm,
      loginLoading,
      registerLoading,
      loginError,
      registerError,
      registerSuccess,
      isFlipped,
      login,
      register,
      toggleFlip,
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

/* 翻转卡片容器 */
.flip-card {
  position: relative;
  width: 480px;
  perspective: 1500px;
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 翻转动画 */
.flip-card-inner {
  position: relative;
  width: 100%;
  min-height: 450px;
  transition: transform 0.8s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  transform-style: preserve-3d;
}

.flip-card.flipped .flip-card-inner {
  transform: rotateY(180deg);
}

.flip-card .card-front,
.flip-card .card-back {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  min-height: 450px;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
}

.flip-card .card-front {
  z-index: 2;
}

.flip-card .card-back {
  transform: rotateY(180deg);
  z-index: 1;
}

/* 原有登录表单样式 - 保持不变 */
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

/* 注册表单额外样式 */
.register-form {
  /* 继承 login-form 的所有样式 */
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
  margin-top: -70px;
}

.register-form:hover {
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

/* 注册按钮 - 绿色 */
.register-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
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

.register-btn:hover {
  background: linear-gradient(135deg, #85ce61 0%, #67c23a 100%);
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.3);
  transform: translateY(-2px);
}

.register-btn:disabled {
  background: linear-gradient(135deg, #c2e7b0 0%, #b3e19d 100%);
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

.success-message {
  color: #67c23a;
  text-align: center;
  margin-top: 15px;
  font-size: 14px;
  background-color: #f0f9eb;
  padding: 10px;
  border-radius: 4px;
  border-left: 4px solid #67c23a;
}

/* 翻转箭头样式 */
.flip-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  z-index: 100;
  animation: breathe 2s ease-in-out infinite;
}

.flip-arrow.arrow-right {
  right: -60px;
}

.flip-arrow.arrow-left {
  left: -60px;
}

.arrow-icon {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 50px;
  height: 50px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  font-size: 24px;
  color: #333;
  transition: all 0.3s ease;
}

.flip-arrow:hover .arrow-icon {
  background: rgba(255, 255, 255, 0.6);
  transform: scale(1.1);
}

/* 呼吸动画 */
@keyframes breathe {
  0%, 100% {
    opacity: 0.5;
    transform: translateY(-50%) scale(1);
  }
  50% {
    opacity: 1;
    transform: translateY(-50%) scale(1.15);
  }
}
</style>
