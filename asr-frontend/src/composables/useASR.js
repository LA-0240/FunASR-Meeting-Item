import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { requestASR } from '@/api/asrApi'

export const useASR = (currentFile) => {
  const asrLoading = ref(false)
  const transcriptionResult = ref([])
  const transcriptionText = ref('')
  // ASR配置
  const asrForm = reactive({ batch_size_s: 300, hotword: '' })

  // 语音转写
  const handleASR = async () => {
    if (!currentFile.value) return ElMessage.warning('请先上传音频文件！')

    asrLoading.value = true
    try {
      const formData = new FormData()
      formData.append('file', currentFile.value)
      formData.append('batch_size_s', asrForm.batch_size_s)
      if (asrForm.hotword) formData.append('hotword', asrForm.hotword)

      const response = await requestASR(formData)
      if (response.data.status === 'success') {
        transcriptionResult.value = response.data.transcription
        transcriptionText.value = response.data.transcription
          .map(item => `【发言人${item.spk}】${item.text}`)
          .join('\n')
        ElMessage.success('语音转写完成！')
      } else {
        ElMessage.error(response.data.detail || '转写失败')
      }
    } catch (error) {
      console.error('ASR Error:', error)
      ElMessage.error(`转写失败：${error.message}`)
    } finally {
      asrLoading.value = false
    }
  }

  return {
    asrLoading,
    transcriptionResult,
    transcriptionText,
    asrForm,
    handleASR
  }
}