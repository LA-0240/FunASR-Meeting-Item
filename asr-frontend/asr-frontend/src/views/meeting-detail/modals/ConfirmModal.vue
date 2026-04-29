<template>
  <div v-if="show" class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content confirm-modal">
      <div class="modal-body">
        <div class="confirm-icon">⚠️</div>
        <h3>{{ title }}</h3>
        <p v-if="message">{{ message }}</p>
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
export default {
  name: 'ConfirmModal',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    title: {
      type: String,
      default: '确认'
    },
    message: {
      type: String,
      default: ''
    },
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
