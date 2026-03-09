import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { requestVideoASR } from '@/api/asrApi'

export const useVideoASR = (currentFile) => {
  const videoAsrLoading = ref(false)
  const transcriptionResult = ref([])
  const transcriptionText = ref('')
  const subtitleDownloadUrl = ref('')

  const videoAsrForm = reactive({
    batch_size_s: 300,
    hotword: ''
  })

  // 视频转写
  const handleVideoASR = async () => {
    if (!currentFile.value) return ElMessage.warning('请先上传视频文件！')
    videoAsrLoading.value = true
    try {
      const formData = new FormData()
      formData.append('file', currentFile.value)
      formData.append('batch_size_s', videoAsrForm.batch_size_s)
      if (videoAsrForm.hotword) formData.append('hotword', videoAsrForm.hotword)

      const response = await requestVideoASR(formData)
      if (response.data.status === 'success') {
        transcriptionResult.value = response.data.transcription
        subtitleDownloadUrl.value = response.data.subtitle_download_url
        transcriptionText.value = response.data.transcription
          .map(item => `【发言人${item.spk}】${item.text}`)
          .join('\n')
        ElMessage.success('视频转写+字幕生成完成！')
      } else {
        ElMessage.error(response.data.detail || '视频转写失败')
      }
    } catch (error) {
      console.error('Video ASR Error:', error)
      ElMessage.error(`视频转写失败：${error.message}`)
    } finally {
      videoAsrLoading.value = false
    }
  }

  return {
    videoAsrLoading,
    transcriptionResult,
    transcriptionText,
    subtitleDownloadUrl,
    videoAsrForm,
    handleVideoASR
  }
}