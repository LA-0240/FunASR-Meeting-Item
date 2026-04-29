<template>
  <div class="stats-container">
    <h3>会议统计</h3>
    <div class="stats-grid">
      <div class="stat-item">
        <span class="stat-label">总时长</span>
        <span class="stat-value">{{ totalDuration }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">说话人数</span>
        <span class="stat-value">{{ speakerCount }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">总句数</span>
        <span class="stat-value">{{ totalSentences }}</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MeetingStats',
  props: {
    totalDuration: {
      type: String,
      default: '00:00'
    },
    speakerCount: {
      type: Number,
      default: 0
    },
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
