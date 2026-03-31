import axios from 'axios'

// 统一设置基础URL（避免硬编码，和现有ASR接口保持一致）
axios.defaults.baseURL = '' // 若ASR接口有baseURL，此处保持一致

/**
 * 声纹注册
 * @param {FormData} formData 包含音频文件的表单数据
 * @returns {Promise}
 */
export const addVoiceprint = async (formData) => {
  return axios.post('/voiceprint/add', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 声纹列表查询
 * @param {Object} params 可选查询参数
 * @returns {Promise}
 */
export const getVoiceprintList = async (params = {}) => {
  try {
    const res = await axios.get('/voiceprint/list', { params })
    console.log('获取声纹列表接口响应：', res)
    // 强制兜底：确保返回数组（适配接口返回 {data: []} 或直接返回 [] 两种情况）
    return {
      data: Array.isArray(res.data?.voiceprints) ? res.data.voiceprints : []
    }
  } catch (error) {
    // 异常兜底：返回空数组，避免表格无数据时报错
    console.error('获取声纹列表接口异常：', error)
    return { data: [] }
  }
}

/**
 * 声纹名称修改
 * @param {Object} data {id: 声纹ID, new_name: 新名称}
 * @returns {Promise}
 */
export const renameVoiceprint = async (data) => {
  return axios.post('/voiceprint/rename', data)
}

/**
 * 声纹删除
 * @param {Object} data {id: 声纹ID}
 * @returns {Promise}
 */
export const deleteVoiceprint = async (data) => {
  return axios.post('/voiceprint/delete', data)
}