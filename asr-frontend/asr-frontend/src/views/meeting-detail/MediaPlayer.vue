<template>
  <!-- 媒体播放器容器 -->
  <div class="player-container" :class="{ 'audio-container': !isVideoFile }">
    <!-- 视频播放器 -->
    <video
      v-if="isVideoFile"
      ref="mediaPlayerRef"
      class="media-player"
      controls
      :src="src"
      @loadedmetadata="handleLoadedMetadata"
      @error="handleError"
    >
      您的浏览器不支持视频播放
    </video>
    <!-- 音频播放器 -->
    <audio
      v-else
      ref="mediaPlayerRef"
      class="media-player audio-only"
      controls
      :src="src"
      @loadedmetadata="handleLoadedMetadata"
      @error="handleError"
    >
      您的浏览器不支持音频播放
    </audio>
  </div>
</template>

<script>
/**
 * 媒体播放器组件
 * 
 * 支持视频和音频播放，提供播放控制、跳转到指定时间、获取时长等功能
 * 
 * 功能特点：
 * - 自动识别视频/音频文件类型
 * - 播放/暂停控制
 * - 跳转到指定时间点
 * - 加载完成时获取并格式化总时长
 * - 错误处理
 * 
 * @component
 * @example
 * <MediaPlayer 
 *   ref="player" 
 *   :src="mediaUrl" 
 *   :isVideoFile="isVideo" 
 *   @loadedmetadata="onLoad"
 *   @duration-change="onDurationChange" 
 * />
 */
export default {
  name: 'MediaPlayer',
  props: {
    /**
     * 媒体文件源 URL
     */
    src: {
      type: String,
      required: true
    },
    /**
     * 是否为视频文件
     * true = 显示 video 标签，false = 显示 audio 标签
     */
    isVideoFile: {
      type: Boolean,
      default: false
    }
  },
  emits: ['loadedmetadata', 'duration-change'],
  methods: {
    /**
     * 媒体元数据加载完成处理
     * 触发 'loadedmetadata' 事件，并格式化总时长后触发 'duration-change' 事件
     */
    handleLoadedMetadata() {
      this.$emit('loadedmetadata');
      if (this.$refs.mediaPlayerRef && this.$refs.mediaPlayerRef.duration) {
        const mins = Math.floor(this.$refs.mediaPlayerRef.duration / 60);
        const secs = Math.floor(this.$refs.mediaPlayerRef.duration % 60);
        const formatted = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        this.$emit('duration-change', formatted);
      }
    },
    /**
     * 媒体加载错误处理
     * 在控制台输出错误信息
     * 
     * @param {Event} event - 错误事件对象
     */
    handleError(event) {
      console.error('❌ [媒体加载失败]:', event);
    },
    /**
     * 跳转到指定时间点
     * 
     * @param {number} timeSeconds - 目标时间（秒）
     */
    jumpTo(timeSeconds) {
      if (this.$refs.mediaPlayerRef) {
        this.$refs.mediaPlayerRef.currentTime = timeSeconds;
      }
    },
    /**
     * 开始播放媒体
     */
    play() {
      if (this.$refs.mediaPlayerRef) {
        this.$refs.mediaPlayerRef.play();
      }
    },
    /**
     * 暂停播放媒体
     */
    pause() {
      if (this.$refs.mediaPlayerRef) {
        this.$refs.mediaPlayerRef.pause();
      }
    }
  }
};
</script>

<style scoped>
.player-container {
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.player-container.audio-container {
  background: #f5f7fa;
  padding: 16px;
}

.media-player {
  width: 100%;
  display: block;
}

.media-player.audio-only {
  border-radius: 8px;
}
</style>
