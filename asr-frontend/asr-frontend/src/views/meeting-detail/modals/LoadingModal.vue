<template>
  <!-- 加载遮罩层：点击遮罩层关闭弹窗 -->
  <div v-if="show" class="modal-overlay loading-overlay" @click.self="$emit('close')">
    <!-- 加载弹窗内容 -->
    <div class="modal-content loading-modal">
      <div class="loading-spinner"></div>
      <p>正在处理中，请稍候...</p>
    </div>
  </div>
</template>

<script>
/**
 * 加载状态弹窗组件
 * 
 * 会议详情页的通用加载提示组件
 * 用于在异步操作进行时向用户展示加载状态
 * 
 * 功能特点：
 * - 显示旋转加载动画
 * - 半透明遮罩层防止用户操作
 * - 点击遮罩层可关闭（可选）
 * - 固定定位显示在页面中央
 *
 * @component
 * @example
 * <LoadingModal :show="isLoading" @close="isLoading = false" />
 */
export default {
  name: 'LoadingModal',
  props: {
    /**
     * 控制弹窗显示/隐藏
     * 
     * @type {Boolean}
     * @default false
     */
    show: {
      type: Boolean,
      default: false
    }
  }
};
</script>

<style scoped>
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
  z-index: 10000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  text-align: center;
}

.loading-modal {
  padding: 40px;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #f0f0f0;
  border-top: 4px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-modal p {
  font-size: 16px;
  color: #333;
  margin: 0;
}
</style>
