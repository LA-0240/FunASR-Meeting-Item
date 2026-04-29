<template>
  <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content result-modal">
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
export default {
  name: 'ResultModal',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    type: {
      type: String,
      default: 'success'
    },
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
