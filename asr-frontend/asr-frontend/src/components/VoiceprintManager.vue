<template>
  <div class="voiceprint-container">
    <!-- 顶部操作区：标题 + 新增声纹按钮 -->
    <div class="voiceprint-header">
      <h4>声纹管理</h4>
      <el-button 
        type="primary" 
        icon="el-icon-plus"
        @click="openAddVoiceprintDialog"
      >
        新增声纹
      </el-button>
    </div>

    <!-- 声纹列表 -->
    <div class="voiceprint-list">
      <el-table
        v-loading="loading"
        :data="Array.isArray(voiceprintList) ? voiceprintList : []"
        border
        stripe
        style="width: 100%"
        :empty-text="!loading ? '暂无已注册的声纹数据，请上传音频文件完成注册' : ''"
      >
        <el-table-column 
          prop="id" 
          label="声纹ID" 
          width="180" 
        />
        <el-table-column 
          prop="name" 
          label="声纹名称" 
          min-width="200"
          :formatter="(row) => row.name || '未命名'"
        />
        <el-table-column 
          prop="createTime" 
          label="注册时间" 
          width="200"
          :formatter="(row) => row.createTime || '未知'"
        />
        <el-table-column 
          label="操作" 
          width="200" 
          fixed="right"
        >
          <template #default="scope">
            <el-button
              v-if="scope.row.id"
              size="small"
              type="text"
              @click="openRenameDialog(scope.row)"
            >
              重命名
            </el-button>
            <el-button
              v-if="scope.row.id"
              size="small"
              type="text"
              text-color="danger"
              @click="handleDeleteVoiceprint(scope.row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 新增声纹弹窗 -->
    <el-dialog
      v-model="addVoiceprintDialogVisible"
      title="注册声纹"
      width="500px"
      @close="resetAddForm"
    >
      <el-form 
        :model="addForm" 
        label-width="80px" 
        ref="addFormRef"
        :rules="addFormRules"
      >
        <el-form-item label="声纹名称" prop="name">
          <el-input
            v-model="addForm.name"
            placeholder="请输入声纹名称"
            maxlength="50"
            clearable
          />
        </el-form-item>
        <el-form-item label="音频文件" prop="file">
          <el-upload
            class="upload-btn"
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            accept=".mp3,.wav,.ogg,.flac"
            :show-file-list="true"
            :file-list="addForm.fileList"
            :before-upload="beforeUploadFile"
          >
            <i class="el-icon-upload"></i>
            <div class="el-upload__text">拖拽音频文件至此<br/>或<em>点击上传</em></div>
            <div class="el-upload__tip">支持 MP3/WAV/OGG/FLAC 格式（大小≤10MB）</div>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addVoiceprintDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          :loading="uploadLoading"
          @click="handleSubmitAddVoiceprint"
        >
          确认注册
        </el-button>
      </template>
    </el-dialog>

    <!-- 重命名弹窗 -->
    <el-dialog
      v-model="renameDialogVisible"
      title="修改声纹名称"
      width="400px"
      @close="resetRenameForm"
    >
      <el-form :model="renameForm" label-width="80px">
        <el-form-item label="新名称">
          <el-input
            v-model="renameForm.name"
            placeholder="请输入声纹名称"
            maxlength="50"
            clearable
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="renameDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleRenameVoiceprint">
          确认修改
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useVoiceprint } from '@/composables/useVoiceprint'
import { ElMessage, ElForm } from 'element-plus'

// 新增声纹弹窗相关
const addVoiceprintDialogVisible = ref(false)
const addFormRef = ref(null)
const addForm = reactive({
  name: '',
  file: null,
  fileList: [] // 上传文件列表
})

// 主流音频格式配置（后缀 + MIME类型）
const AUDIO_FORMATS = {
  mp3: {
    exts: ['.mp3'],
    mime: ['audio/mp3', 'audio/mpeg', 'audio/x-mpeg', 'audio/mpg', 'audio/x-mpg', 'audio/mpeg3']
  },
  wav: {
    exts: ['.wav'],
    mime: ['audio/wav', 'audio/x-wav', 'audio/wave']
  },
  ogg: {
    exts: ['.ogg'],
    mime: ['audio/ogg', 'application/ogg']
  },
  flac: {
    exts: ['.flac'],
    mime: ['audio/flac', 'audio/x-flac']
  }
}

// 新增表单校验规则
const addFormRules = reactive({
  name: [{ required: true, message: '请输入声纹名称', trigger: 'blur' }],
  file: [{ required: true, message: '请上传主流音频格式文件（MP3/WAV/OGG/FLAC）', trigger: 'change' }]
})

// 引入声纹管理核心逻辑
const {
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
} = useVoiceprint()

// 打开新增声纹弹窗
const openAddVoiceprintDialog = () => {
  addVoiceprintDialogVisible.value = true
  // 重置表单校验状态
  if (addFormRef.value) {
    addFormRef.value.clearValidate()
  }
}

// 重置新增表单
const resetAddForm = () => {
  addForm.name = ''
  addForm.file = null
  addForm.fileList = []
  if (addFormRef.value) {
    addFormRef.value.clearValidate()
  }
}

// 文件移除事件
const handleFileRemove = () => {
  addForm.file = null
  addForm.fileList = []
}

// 校验文件格式（后缀 + MIME）
const checkFileFormat = (file) => {
  const fileName = file.name.toLowerCase()
  const fileMime = file.type.toLowerCase()

  // 遍历所有支持的格式
  for (const format in AUDIO_FORMATS) {
    const { exts, mime } = AUDIO_FORMATS[format]
    // 后缀匹配 或 MIME匹配
    const extMatch = exts.some(ext => fileName.endsWith(ext))
    const mimeMatch = mime.some(m => fileMime.includes(m))
    if (extMatch || mimeMatch) {
      return { valid: true, format }
    }
  }
  return { valid: false, format: '' }
}

// 上传前校验（格式 + 文件大小）
const beforeUploadFile = (file) => {
  // 1. 校验文件大小（≤10MB）
  const isLt10M = file.size / 1024 / 1024 <= 10
  if (!isLt10M) {
    ElMessage.error('上传音频文件大小不能超过 10MB！')
    return false
  }

  // 2. 校验文件格式
  const { valid } = checkFileFormat(file)
  if (!valid) {
    ElMessage.error('仅支持 MP3/WAV/OGG/FLAC 格式的音频文件！')
    return false
  }

  return true
}

// 文件选择后处理（兼容多格式）
const handleFileChange = (file, fileList) => {
  addForm.fileList = fileList
  if (file && file.raw) {
    // 校验文件格式
    const { valid, format } = checkFileFormat(file.raw)
    if (!valid) {
      ElMessage.error('仅支持 MP3/WAV/OGG/FLAC 格式的音频文件！')
      addForm.file = null
      addForm.fileList = []
      return
    }

    // 格式提示（可选）
    ElMessage.success(`已选择 ${format.toUpperCase()} 格式文件`)
    addForm.file = file.raw
  }
}

// 提交注册声纹
const handleSubmitAddVoiceprint = async () => {
  // 1. 表单校验
  const valid = await addFormRef.value.validate()
  if (!valid) return

  // 2. 二次校验文件
  if (!addForm.file) {
    return ElMessage.warning('请上传有效的音频文件（MP3/WAV/OGG/FLAC）！')
  }

  // 3. 提交注册
  await handleVoiceprintAdd(addForm.name.trim(), addForm.file)

  // 4. 关闭弹窗+重置表单
  addVoiceprintDialogVisible.value = false
  resetAddForm()
}

// 重置重命名表单
const resetRenameForm = () => {
  renameForm.name = ''
}
</script>

<style scoped>
.voiceprint-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 0 10px;
}

.voiceprint-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.voiceprint-header h4 {
  font-size: 15px;
  color: #1d2129;
  margin: 0;
  font-weight: 500;
}

.voiceprint-list {
  flex: 1;
  overflow: auto;
}

/* 上传按钮样式 */
.upload-btn {
  width: 100%;
  margin-top: 8px;
}

:deep(.el-upload-dragger) {
  width: 100%;
  padding: 20px;
}

/* 统一弹窗样式（编辑/删除弹窗视觉一致） */
:deep(.el-dialog__wrapper) {
  background-color: rgba(240, 242, 245, 0.7) !important;
  z-index: 2000 !important;
}

:deep(.el-message-box__wrapper) {
  background-color: rgba(240, 242, 245, 0.7) !important;
  z-index: 2001 !important;
}

/* 表格样式优化 */
:deep(.el-table) {
  --el-table-text-color: #1d2129;
  --el-table-row-hover-bg-color: #f0f5ff;
}

/* 弹窗内部样式 */
:deep(.el-dialog__body) {
  padding: 20px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

/* 空状态提示 */
:deep(.el-table__empty-text) {
  color: #86909c;
  font-size: 14px;
}
</style>