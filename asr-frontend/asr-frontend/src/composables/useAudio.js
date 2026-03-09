import { ref, nextTick , onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { formatTime, getTimeMarkPosition } from '@/utils/timeFormat'

export const useAudio = () => {
  // 播放器ref
  const audioRef = ref(null)
  const videoRef = ref(null)
  const timelineRef = ref(null)
  const scrollWrapperRef = ref(null)
  
  // ====================== 这里定义了 mediaUrl ======================
  const mediaUrl = ref('')
  const audioDuration = ref(0)
  const currentTime = ref(0)
  const progressPercent = ref(0)
  const fileList = ref([])
  const currentFile = ref(null)
  const fileType = ref('')

  // 加载完成
  const handleLoadedMetadata = () => {
    audioDuration.value = audioRef.value?.duration || 0
  }
  const handleVideoLoadedMetadata = () => {
    audioDuration.value = videoRef.value?.duration || 0
  }

  // 错误提示
  const handleAudioError = () => ElMessage.error('音频加载失败')
  const handleVideoError = () => ElMessage.error('视频加载失败')

  // 上传校验
  const beforeUpload = (file) => {
    const isAudio = file.type.startsWith('audio/')
    const isVideo = file.type.startsWith('video/')
    if (!isAudio && !isVideo) {
      ElMessage.error('仅支持音频/视频')
      return false
    }
    return true
  }

  // ==============================================
  // 🔥 稳定版文件选择（第一次必成功，绝不失败）
  // ==============================================
  const handleFileChange = async (file) => {
    fileList.value = [file]
    currentFile.value = file.raw
    const isVideo = file.raw.type.startsWith('video/')
    fileType.value = isVideo ? 'video' : 'audio'

    // 释放旧资源
    if (mediaUrl.value) URL.revokeObjectURL(mediaUrl.value)
    mediaUrl.value = ''

    // 等待 DOM 渲染完成（解决第一次必败问题）
    await nextTick()

    // 创建新地址
    mediaUrl.value = URL.createObjectURL(file.raw)

    // 完全重置两个播放器
    if (audioRef.value) {
      audioRef.value.src = ''
      audioRef.value.load()
    }
    if (videoRef.value) {
      videoRef.value.src = ''
      videoRef.value.load()
    }

    // 赋值
    if (isVideo) {
      videoRef.value.src = mediaUrl.value
      videoRef.value.load()
    } else {
      audioRef.value.src = mediaUrl.value
      audioRef.value.load()
    }

    // 重置进度
    audioDuration.value = 0
    currentTime.value = 0
    progressPercent.value = 0
  }

  // 时间更新
  let timeUpdateTimer = null
  const handleTimeUpdate = () => {
    const player = fileType.value === 'video' ? videoRef.value : audioRef.value
    if (!player) return

    clearTimeout(timeUpdateTimer)
    timeUpdateTimer = setTimeout(() => {
      currentTime.value = player.currentTime
      progressPercent.value = (currentTime.value / audioDuration.value) * 100 || 0
    }, 150)
  }

  // 跳转
  const handleTimelineClick = (e) => {
    const player = fileType.value === 'video' ? videoRef.value : audioRef.value
    if (!player || !timelineRef.value) return
    const per = (e.clientX - timelineRef.value.getBoundingClientRect().left) / timelineRef.value.offsetWidth
    jumpToTime(per * audioDuration.value)
  }

  const jumpToTime = (time) => {
    const player = fileType.value === 'video' ? videoRef.value : audioRef.value
    if (!player) return
    player.currentTime = Math.min(time, audioDuration.value)
    player.play().catch(() => ElMessage.warning('请手动播放'))
  }

  // 清理
  onMounted(() => {
    window.addEventListener('beforeunload', () => {
      if (mediaUrl.value) URL.revokeObjectURL(mediaUrl.value)
    })
  })


  return {
    audioRef,
    videoRef,
    timelineRef,
    scrollWrapperRef,
    audioDuration,
    currentTime,
    progressPercent,
    fileList,
    currentFile,
    fileType,
    formatTime,
    getTimeMarkPosition,
    handleLoadedMetadata,
    handleVideoLoadedMetadata,
    handleAudioError,
    handleVideoError,
    beforeUpload,
    handleFileChange,
    handleTimeUpdate,
    handleTimelineClick,
    jumpToTime
  }
}