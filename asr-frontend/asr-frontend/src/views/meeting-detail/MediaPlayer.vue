<template>
  <div class="player-container" :class="{ 'audio-container': !isVideoFile }">
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
export default {
  name: 'MediaPlayer',
  props: {
    src: {
      type: String,
      required: true
    },
    isVideoFile: {
      type: Boolean,
      default: false
    }
  },
  emits: ['loadedmetadata', 'duration-change'],
  methods: {
    handleLoadedMetadata() {
      this.$emit('loadedmetadata');
      if (this.$refs.mediaPlayerRef && this.$refs.mediaPlayerRef.duration) {
        const mins = Math.floor(this.$refs.mediaPlayerRef.duration / 60);
        const secs = Math.floor(this.$refs.mediaPlayerRef.duration % 60);
        const formatted = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        this.$emit('duration-change', formatted);
      }
    },
    handleError(event) {
      console.error('❌ [媒体加载失败]', event);
    },
    jumpTo(timeSeconds) {
      if (this.$refs.mediaPlayerRef) {
        this.$refs.mediaPlayerRef.currentTime = timeSeconds;
      }
    },
    play() {
      if (this.$refs.mediaPlayerRef) {
        this.$refs.mediaPlayerRef.play();
      }
    },
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
