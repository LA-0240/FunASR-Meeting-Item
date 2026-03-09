import { ElMessage } from 'element-plus'

/**
 * 导出Blob为文件
 * @param {Blob} blob 文件Blob
 * @param {string} fileName 文件名
 */
export const exportBlobToFile = (blob, fileName) => {
  try {
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = fileName
    a.click()
    URL.revokeObjectURL(a.href)
    ElMessage.success(`${fileName} 导出成功！`)
  } catch (error) {
    ElMessage.error(`导出失败：${error.message}`)
    console.error('文件导出错误：', error)
  }
}