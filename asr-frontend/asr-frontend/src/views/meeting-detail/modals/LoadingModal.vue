<template>
  <div v-if="show" class="modal-overlay loading-overlay" @click.self="$emit('close')">
    <div class="modal-content loading-modal">
      <div class="loading-spinner"></div>
      <p>正在处理中，请稍候...</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LoadingModal',
  props: {
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
