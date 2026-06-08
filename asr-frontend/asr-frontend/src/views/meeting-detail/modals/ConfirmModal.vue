<template>
  <!-- 确认遮罩层：点击遮罩层关闭弹窗 -->
  <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
    <!-- 确认弹窗内容 -->
    <div class="modal-content confirm-modal">
      <div class="modal-body">
        <!-- 警告图标 -->
        <div class="confirm-icon">⚠️</div>
        <h3>{{ title }}</h3>
        <p v-if="message">{{ message }}</p>
        <!-- 多行消息渲染 -->
        <p v-for="(line, index) in messageLines" :key="index">{{ line }}</p>
      </div>
      <div class="modal-footer">
        <button class="cancel-btn" @click="$emit('close')">取消</button>
        <button class="confirm-btn danger" @click="$emit('confirm')">确认</button>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * 确认操作弹窗组件
 * 
 * 会议详情页的二次确认组件
 * 用于在执行重要操作前向用户确认
 * 
 * 功能特点：
 * - 支持自定义标题和消息
 * - 支持单行或多行消息
 * - 提供取消和确认两个按钮
 * - 确认按钮为危险样式，提示重要性
 * - 点击遮罩层可取消
 *
 * @component
 * @example
 * <ConfirmModal 
 *   :show="showConfirm" 
 *   title="删除确认" 
 *   message="确定要删除这个会议吗？" 
 *   @close="showConfirm = false" 
 *   @confirm="handleDelete" 
 * />
 */
export default {
  name: 'ConfirmModal',
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
     * 弹窗标题
     * 
     * @type {String}
     * @default '确认'
     */
    title: {
      type: String,
      default: '确认'
    },
    /**
     * 单行提示消息
     * 
     * @type {String}
     * @default ''
     */
    message: {
      type: String,
      default: ''
    },
    /**
     * 多行提示消息（数组格式）
     * 
     * @type {Array<String>}
     * @default []
     */
    messageLines: {
      type: Array,
      default: () => []
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

.confirm-modal {
  padding: 40px;
  text-align: center;
  min-width: 350px;
}

.confirm-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.confirm-modal h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #333;
}

.confirm-modal p {
  margin: 8px 0;
  font-size: 14px;
  color: #666;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 24px 0 0;
}

.cancel-btn,
.confirm-btn {
  padding: 10px 24px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.cancel-btn {
  background: white;
  border: 1px solid #ddd;
  color: #666;
}

.cancel-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

.confirm-btn {
  background: #409eff;
  border: 1px solid #409eff;
  color: white;
}

.confirm-btn:hover {
  background: #66b1ff;
}

.confirm-btn.danger {
  background: #f56c6c;
  border: 1px solid #f56c6c;
}

.confirm-btn.danger:hover {
  background: #f78989;
}
</style>
