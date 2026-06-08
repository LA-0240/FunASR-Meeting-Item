<template>
  <div class="stats-container">
    <h3>会议统计</h3>
    <div class="stats-grid">
      <!-- 总时长 -->
      <div class="stat-item">
        <span class="stat-label">总时长</span>
        <span class="stat-value">{{ totalDuration }}</span>
      </div>
      <!-- 说话人数 -->
      <div class="stat-item">
        <span class="stat-label">说话人数</span>
        <span class="stat-value">{{ speakerCount }}</span>
      </div>
      <!-- 总句数 -->
      <div class="stat-item">
        <span class="stat-label">总句数</span>
        <span class="stat-value">{{ totalSentences }}</span>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * 会议统计信息展示组件
 * 
 * 显示会议的基本统计数据，包括总时长、说话人数和总句数
 * 
 * 功能特点：
 * - 简洁的卡片式布局
 * - 展示核心会议统计信息
 * - 支持通过 props 动态传入数据
 * 
 * @component
 * @example
 * <MeetingStats 
 *   totalDuration="01:30:45" 
 *   :speakerCount="5" 
 *   :totalSentences="245" 
 * />
 */
export default {
  name: 'MeetingStats',
  props: {
    /**
     * 会议总时长，格式为 "HH:MM:SS" 或 "MM:SS"
     */
    totalDuration: {
      type: String,
      default: '00:00'
    },
    /**
     * 会议中参与说话的人数
     */
    speakerCount: {
      type: Number,
      default: 0
    },
    /**
     * 会议中转录的总句子数量
     */
    totalSentences: {
      type: Number,
      default: 0
    }
  }
};
</script>

<style scoped>
.stats-container {
  background: white;
  border-radius: 8px;
  padding: 16px;
}

.stats-container h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.stats-grid {
  display: grid;
  gap: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 13px;
  color: #999;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}
</style>
