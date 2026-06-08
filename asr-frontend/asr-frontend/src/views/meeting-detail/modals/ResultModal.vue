<template>
  <!-- 结果遮罩层：点击遮罩层关闭弹窗 -->
  <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
    <!-- 结果弹窗内容 -->
    <div class="modal-content result-modal">
      <!-- 结果图标：成功或失败 -->
      <div class="result-icon" :class="type">{{ type === 'success' ? '✓' : '✗' }}</div>
      <h3>{{ type === 'success' ? '操作成功' : '操作失败' }}</h3>
      <p>{{ message }}</p>
      <div class="modal-footer">
        <button class="confirm-btn" @click="$emit('close')">确定</button>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * 操作结果弹窗组件
 * 
 * 会议详情页的操作结果提示组件
 * 用于展示操作的成功或失败状态
 * 
 * 功能特点：
 * - 支持成功和失败两种状态
 * - 显示对应的图标和标题
 * - 可自定义提示消息
 * - 点击确定按钮关闭
 *
 * @component
 * @example
 * <ResultModal 
 *   :show="showResult" 
 *   type="success" 
 *   message="保存成功！" 
 *   @close="showResult = false" 
 * />
 */
export default {
  name: 'ResultModal',
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
    },
    /**
     * 结果类型：成功或失败
     * 
     * @type {String}
     * @default 'success'
     * @values 'success' | 'error'
     */
    type: {
      type: String,
      default: 'success'
    },
    /**
     * 提示消息内容
     * 
     * @type {String}
     * @default ''
     */
    message: {
      type: String,
      default: ''
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
}

.result-modal {
  padding: 40px;
  text-align: center;
  min-width: 300px;
}

.result-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  color: white;
  margin: 0 auto 20px;
}

.result-icon.success {
  background: #67c23a;
}

.result-icon.error {
  background: #f56c6c;
}

.result-modal h3 {
  margin: 0 0 12px 0;
  font-size: 18px;
  color: #333;
}

.result-modal p {
  margin: 0 0 24px 0;
  font-size: 14px;
  color: #666;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 0 0;
}

.confirm-btn {
  padding: 10px 24px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  background: #409eff;
  border: 1px solid #409eff;
  color: white;
}

.confirm-btn:hover {
  background: #66b1ff;
}
</style>
