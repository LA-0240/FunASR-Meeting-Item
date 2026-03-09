import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  requestSummary,
  requestAbstract,
  exportTranscriptionWord,
  exportSummaryWord,
  exportAbstractWord
} from '@/api/asrApi'
import { exportBlobToFile } from '@/utils/fileExport'

// 接收 subtitleDownloadUrl 从父组件传入
export const useSummary = (transcriptionText, currentFile, subtitleDownloadUrl) => {
  // 会议纪要
  const summaryLoading = ref(false)
  const summaryResult = ref('')
  // 会议摘要
  const abstractLoading = ref(false)
  const abstractResult = ref('')
  const activeTab = ref('transcript')

  // 生成会议纪要
  const handleGenerateSummary = async () => {
    if (!transcriptionText.value) return ElMessage.warning('请先完成语音转写！')
    summaryLoading.value = true
    try {
      const response = await requestSummary(transcriptionText.value)
      if (response.data.status === 'success') {
        summaryResult.value = response.data.meeting_minutes
        activeTab.value = 'summary'
        ElMessage.success('会议纪要生成完成！')
      } else {
        ElMessage.error(response.data.detail || '生成失败')
      }
    } catch (error) {
      console.error('Summary Error:', error)
      ElMessage.error(`生成失败：${error.message}`)
    } finally {
      summaryLoading.value = false
    }
  }

  // 生成会议摘要
  const handleGenerateAbstract = async () => {
    if (!transcriptionText.value) return ElMessage.warning('请先完成语音转写！')
    abstractLoading.value = true
    try {
      const response = await requestAbstract(transcriptionText.value)
      if (response.data.status === 'success') {
        abstractResult.value = response.data.meeting_abstract
        activeTab.value = 'abstract'
        ElMessage.success('会议摘要生成完成！')
      } else {
        ElMessage.error(response.data.detail || '生成失败')
      }
    } catch (error) {
      console.error('Abstract Error:', error)
      ElMessage.error(`生成失败：${error.message}`)
    } finally {
      abstractLoading.value = false
    }
  }

  // 导出转写结果Word
  const exportTranscriptionWordHandler = async () => {
    if (!transcriptionText.value) return ElMessage.warning('暂无转写内容可导出！')
    try {
      const fileNamePrefix = currentFile.value.name.replace(/\.\w+$/, '')
      const response = await exportTranscriptionWord(transcriptionText.value, fileNamePrefix)
      const blob = new Blob([response.data])
      const fileName = `${fileNamePrefix}_语音转写结果.docx`
      exportBlobToFile(blob, fileName)
    } catch (error) {
      console.error('Export Transcription Error:', error)
      ElMessage.error(`导出失败：${error.message}`)
    }
  }

  // 导出会议纪要Word
  const exportSummaryWordHandler = async () => {
    if (!summaryResult.value) return ElMessage.warning('暂无纪要可导出！')
    try {
      const fileNamePrefix = currentFile.value.name.replace(/\.\w+$/, '')
      const response = await exportSummaryWord(summaryResult.value, fileNamePrefix)
      const blob = new Blob([response.data])
      const fileName = `${fileNamePrefix}_会议纪要.docx`
      exportBlobToFile(blob, fileName)
    } catch (error) {
      console.error('Export Summary Error:', error)
      ElMessage.error(`导出失败：${error.message}`)
    }
  }

  // 导出会议摘要Word
  const exportAbstractWordHandler = async () => {
    if (!abstractResult.value) return ElMessage.warning('暂无摘要可导出！')
    try {
      const fileNamePrefix = currentFile.value.name.replace(/\.\w+$/, '')
      const response = await exportAbstractWord(abstractResult.value, fileNamePrefix)
      const blob = new Blob([response.data])
      const fileName = `${fileNamePrefix}_会议摘要.docx`
      exportBlobToFile(blob, fileName)
    } catch (error) {
      console.error('Export Abstract Error:', error)
      ElMessage.error(`导出失败：${error.message}`)
    }
  }

  // 新增：下载SRT字幕
  const downloadSubtitle = () => {
    if (!subtitleDownloadUrl.value) return ElMessage.warning('暂无字幕可下载！')
    const a = document.createElement('a')
    a.href = subtitleDownloadUrl.value
    a.download = ''
    a.click()
    ElMessage.success('字幕下载开始')
  }

  return {
    summaryLoading,
    summaryResult,
    abstractLoading,
    abstractResult,
    activeTab,
    handleGenerateSummary,
    handleGenerateAbstract,
    exportTranscriptionWordHandler,
    exportSummaryWordHandler,
    exportAbstractWordHandler,
    downloadSubtitle // 导出方法
  }
}