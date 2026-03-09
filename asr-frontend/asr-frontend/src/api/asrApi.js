import axios from 'axios'

// ASR语音转写
export const requestASR = async (formData) => {
  return axios.post('/asr', formData)
}

// 生成会议纪要
export const requestSummary = async (transcriptionText) => {
  return axios.post('/generate_summary', {
    transcription_text: transcriptionText,
    output_format: 'txt'
  })
}

// 生成会议摘要
export const requestAbstract = async (transcriptionText, abstract_length = 'medium') => {
  return axios.post(
    '/meeting_abstract',
    {
      transcription_text: transcriptionText,
      abstract_length
    },
    { timeout: 60000 }
  )
}

// 导出转写结果为Word
export const exportTranscriptionWord = async (transcriptionText, fileName) => {
  return axios.post(
    '/export_transcription_word',
    { transcription_text: transcriptionText, file_name: fileName },
    { responseType: 'blob' }
  )
}

// 导出摘要为Word
export const exportSummaryWord = async (summaryText, fileName) => {
  return axios.post(
    '/export_summary_word',
    { summary_text: summaryText, file_name: fileName },
    { responseType: 'blob' }
  )
}

// 导出会议摘要Word
export const exportAbstractWord = async (abstract_text, file_name) => {
  return axios.post(
    '/export_abstract_word',
    { abstract_text, file_name },
    { responseType: 'blob', timeout: 60000 }
  )
}

// 视频ASR转写
export const requestVideoASR = async (formData) => {
  return axios.post('/video_asr', formData)
}

// 下载字幕
export const downloadSubtitleApi = (url) => {
  return axios.get(url, { responseType: 'blob' })
}