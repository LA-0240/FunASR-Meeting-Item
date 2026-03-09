import { ref, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { formatTime, getTimeMarkPosition } from '@/utils/timeFormat'

export const useAudio = () => {
  // 音频相关状态
  const audioRef = ref(null)
  const timelineRef = ref(null)
  const scrollWrapperRef = ref(null)
  const audioUrl = ref('')
  const audioDuration = ref(0)
  const currentTime = ref(0)
  const progressPercent = ref(0)
  const fileList = ref([])
  const currentFile = ref(null)

  // 音频加载完成
  const handleLoadedMetadata = () => {
    if (audioRef.value) {
      audioDuration.value = audioRef.value.duration
      ElMessage.success('音频加载完成，可以播放')
    }
  }

  // 音频错误捕获
  const handleAudioError = (e) => {
    ElMessage.error(`音频加载失败：${e.target.error.message}`)
    console.error('音频错误详情：', e.target.error)
  }

  // 上传前校验
  const beforeUpload = (file) => {
    const isAudio = ['audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/ogg', 'audio/flac'].includes(file.type)
    if (!isAudio) {
      ElMessage.error('仅支持 .wav / .mp3 / .ogg / .flac 格式音频！')
      return false
    }
    return true
  }

  // 文件选择事件
  const handleFileChange = (file) => {
    fileList.value = [file]
    currentFile.value = file.raw

    // 释放旧的URL
    if (audioUrl.value) {
      URL.revokeObjectURL(audioUrl.value)
    }

    // 创建新的音频URL
    audioUrl.value = URL.createObjectURL(file.raw)
    if (audioRef.value) {
      audioRef.value.src = audioUrl.value
      audioRef.value.load()
    }

    // 重置状态
    audioDuration.value = 0
    currentTime.value = 0
    progressPercent.value = 0
  }

  // 音频时间更新（优化自动滚动）
  let timeUpdateTimer = null
  const handleTimeUpdate = (transcriptionResult) => {
    if (!audioRef.value || !audioDuration.value) return

    clearTimeout(timeUpdateTimer)
    timeUpdateTimer = setTimeout(() => {
      currentTime.value = audioRef.value.currentTime
      progressPercent.value = (currentTime.value / audioDuration.value) * 100 || 0

      // 播放状态下自动滚动到当前转写段
      if (!audioRef.value.paused && transcriptionResult.length) {
        const activeItem = document.querySelector('.transcript-item.highlight')
        if (activeItem && scrollWrapperRef.value) {
          const wrapperRect = scrollWrapperRef.value.getBoundingClientRect()
          const itemRect = activeItem.getBoundingClientRect()
          if (itemRect.bottom > wrapperRect.bottom + 20 || itemRect.top < wrapperRect.top - 20) {
            activeItem.scrollIntoView({ behavior: 'smooth', block: 'center' })
          }
        }
      }
    }, 150)
  }

  // 时间轴点击跳转
  const handleTimelineClick = (e) => {
    if (!audioRef.value || !audioDuration.value || !timelineRef.value) return

    const rect = timelineRef.value.getBoundingClientRect()
    const clickX = e.clientX - rect.left
    const timelineWidth = rect.width
    const percent = Math.max(0, Math.min(1, clickX / timelineWidth))
    const targetTime = percent * audioDuration.value

    jumpToTime(targetTime)
  }

  // 精准跳转到指定时间
  const jumpToTime = (time) => {
    if (!audioRef.value || !audioDuration.value) {
      ElMessage.warning('音频未加载完成，无法跳转')
      return
    }

    const targetTime = Math.max(0, Math.min(time, audioDuration.value))
    audioRef.value.currentTime = targetTime
    audioRef.value.play().catch(err => {
      ElMessage.warning('播放需要手动触发：请先点击音频控件的播放按钮')
    })

    currentTime.value = targetTime
    progressPercent.value = (targetTime / audioDuration.value) * 100 || 0

    // 滚动到对应转写项
    setTimeout(() => {
      const activeItem = document.querySelector('.transcript-item.highlight')
      if (activeItem && scrollWrapperRef.value) {
        activeItem.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }, 100)
  }

  // 清理音频URL
  onMounted(() => {
    window.addEventListener('beforeunload', () => {
      if (audioUrl.value) URL.revokeObjectURL(audioUrl.value)
    })
  })

  watch(() => false, () => {
    if (audioUrl.value) URL.revokeObjectURL(audioUrl.value)
  }, { once: true })

  return {
    // 状态
    audioRef,
    timelineRef,
    scrollWrapperRef,
    audioUrl,
    audioDuration,
    currentTime,
    progressPercent,
    fileList,
    currentFile,
    // 方法
    formatTime,
    getTimeMarkPosition,
    handleLoadedMetadata,
    handleAudioError,
    beforeUpload,
    handleFileChange,
    handleTimeUpdate,
    handleTimelineClick,
    jumpToTime
  }
}