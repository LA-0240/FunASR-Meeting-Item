<template>
  <!-- 会议详情页头部 -->
  <div class="detail-header">
    <div class="header-left">
      <!-- 返回按钮 -->
      <button class="back-btn" @click="$emit('back')">
        <span class="icon">←</span>
        返回
      </button>
      <!-- 会议标题 -->
      <h2>{{ file.name || '会议详情' }}</h2>
      <!-- 文件信息 -->
      <div class="file-info">
        <span>{{ formatDate(file.created_at || file.upload_time) }}</span>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * 会议详情页头部组件
 * 
 * 展示会议文件的基本信息，包括返回按钮、会议标题和创建时间
 * 
 * 功能特点：
 * - 返回按钮：点击触发 'back' 事件
 * - 会议标题：显示文件名或默认标题
 * - 创建时间：格式化显示文件创建/上传时间
 * 
 * @component
 * @example
 * <DetailHeader :file="currentFile" @back="goBack" />
 */
export default {
  name: 'DetailHeader',
  props: {
    /**
     * 会议文件对象
     * 包含 name, created_at, upload_time 等属性
     */
    file: {
      type: Object,
      default: () => ({})
    }
  },
  methods: {
    /**
     * 格式化日期时间字符串
     * 将 ISO 格式的日期转换为中文本地化显示
     * 
     * @param {string} dateStr - 日期字符串 (ISO 格式或可解析格式)
     * @returns {string} 格式化后的日期时间字符串，例如 "2024/5/13 09:30:00"
     */
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
