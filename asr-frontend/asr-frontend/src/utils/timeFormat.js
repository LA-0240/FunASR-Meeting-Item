/**
 * 格式化秒数为 MM:SS 格式
 * @param {number} seconds 秒数
 * @returns {string} 格式化后的时间字符串
 */
export const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

/**
 * 计算时间标记在时间轴的百分比位置
 * @param {number} time 目标时间（秒）
 * @param {number} totalDuration 音频总时长（秒）
 * @returns {number} 百分比（0-100）
 */
export const getTimeMarkPosition = (time, totalDuration) => {
  if (!totalDuration || totalDuration === 0) return 0
  return Math.min(100, (time / totalDuration) * 100)
}