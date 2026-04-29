<template>
  <div class="detail-header">
    <div class="header-left">
      <button class="back-btn" @click="$emit('back')">
        <span class="icon">←</span>
        返回
      </button>
      <h2>{{ file.name || '会议详情' }}</h2>
      <div class="file-info">
        <span>{{ formatDate(file.created_at || file.upload_time) }}</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DetailHeader',
  props: {
    file: {
      type: Object,
      default: () => ({})
    }
  },
  methods: {
    formatDate(dateStr) {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return date.toLocaleString('zh-CN');
    }
  }
};
</script>

<style scoped>
.detail-header {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  background: white;
  border-bottom: 1px solid #eee;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  font-size: 14px;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.file-info {
  display: flex;
  gap: 16px;
  color: #999;
  font-size: 14px;
}
</style>
