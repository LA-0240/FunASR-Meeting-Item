import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { addVoiceprint, getVoiceprintList, renameVoiceprint, deleteVoiceprint } from '@/api/voiceprintApi'

export const useVoiceprint = () => {
  const voiceprintList = ref([])
  const loading = ref(false)
  const uploadLoading = ref(false)
  const renameDialogVisible = ref(false)
  const currentVoiceprint = ref(null)
  const renameForm = reactive({
    name: ''
  })

  // 时间格式化工具
  const formatDateTime = (utcTime) => {
    if (!utcTime) return '未知'
    const date = new Date(utcTime)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  // 声纹列表查询
  const fetchVoiceprintList = async () => {
    loading.value = true
    try {
      const res = await getVoiceprintList()
      voiceprintList.value = Array.isArray(res.data) ? res.data.map(item => ({
        id: item.id,
        name: item.name,
        createTime: formatDateTime(item.created_at),
        updateTime: formatDateTime(item.updated_at)
      })) : []
    } catch (error) {
      ElMessage.error('获取声纹列表失败：' + (error.message || '网络异常'))
      voiceprintList.value = []
    } finally {
      loading.value = false
    }
  }

  // 修复：新增声纹接收name+file参数
  const handleVoiceprintAdd = async (name, file) => {
    if (!name || !file) return
    uploadLoading.value = true
    
    const formData = new FormData()
    formData.append('name', name.trim()) // 补充name参数
    formData.append('file', file)
    
    try {
      await addVoiceprint(formData)
      ElMessage.success('声纹注册成功！')
      fetchVoiceprintList()
    } catch (error) {
      // 细化400错误提示
      const errMsg = error.response?.data?.detail || '参数错误，请检查名称和文件格式'
      ElMessage.error(`声纹注册失败：${errMsg}`)
      console.error('Voiceprint add error:', error)
    } finally {
      uploadLoading.value = false
    }
  }

  // 打开重命名弹窗
  const openRenameDialog = (item) => {
    if (!item) return
    currentVoiceprint.value = item
    renameForm.name = item.name || ''
    renameDialogVisible.value = true
  }

  // 修复：重命名增加「名称未变更」提示
  const handleRenameVoiceprint = async () => {
    if (!currentVoiceprint.value?.id) {
      return ElMessage.warning('无效的声纹ID！')
    }
    const newName = renameForm.name.trim()
    if (!newName) {
      return ElMessage.warning('请输入有效的声纹名称！')
    }
    // 新增：对比新旧名称
    if (newName === currentVoiceprint.value.name) {
      renameDialogVisible.value = false
      return ElMessage.info('声纹名称未变更，无需修改！')
    }
    
    try {
      await renameVoiceprint({
        id: currentVoiceprint.value.id,
        new_name: newName // 注意接口参数是new_name（和后端保持一致）
      })
      ElMessage.success('声纹名称修改成功！')
      renameDialogVisible.value = false
      fetchVoiceprintList()
    } catch (error) {
      const errMsg = error.response?.data?.detail || '修改失败，请重试'
      ElMessage.error(`声纹名称修改失败：${errMsg}`)
      console.error('Voiceprint rename error:', error)
    }
  }

  // 声纹删除（保持不变）
  const handleDeleteVoiceprint = async (id) => {
    if (!id) return ElMessage.warning('无效的声纹ID！')
    
    try {
      await ElMessageBox.confirm(
        '确定要删除该声纹数据吗？此操作不可恢复！',
        '删除确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
      
      await deleteVoiceprint({ id })
      ElMessage.success('声纹删除成功！')
      fetchVoiceprintList()
    } catch (error) {
      if (error !== 'cancel') {
        const errMsg = error.response?.data?.detail || '删除失败，请重试'
        ElMessage.error(`声纹删除失败：${errMsg}`)
        console.error('Voiceprint delete error:', error)
      }
    }
  }

  onMounted(() => {
    fetchVoiceprintList()
  })

  return {
    voiceprintList,
    loading,
    uploadLoading,
    renameDialogVisible,
    renameForm,
    fetchVoiceprintList,
    handleVoiceprintAdd,
    openRenameDialog,
    handleRenameVoiceprint,
    handleDeleteVoiceprint
  }
}