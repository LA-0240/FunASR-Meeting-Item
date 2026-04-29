<template>
  <div class="conference-container">
    <!-- 标签栏 -->
    <div class="section-header">
      <div class="section-tabs">
        <span class="section-tab" :class="{ active: activeTab === 'all' }" @click="activeTab = 'all'">全部</span>
        <span class="section-tab" :class="{ active: activeTab === 'video' }" @click="activeTab = 'video'">视频</span>
        <span class="section-tab" :class="{ active: activeTab === 'audio' }" @click="activeTab = 'audio'">音频</span>
      </div>
      <div class="view-toggle">
        <button @click="viewMode = 'grid'" :class="{ active: viewMode === 'grid' }">
          <span class="icon">🗂️</span>
        </button>
        <button @click="viewMode = 'list'" :class="{ active: viewMode === 'list' }">
          <span class="icon">📋</span>
        </button>
      </div>
    </div>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <div class="search-form">
        <div class="form-group">
          <label>文件名</label>
          <input type="text" v-model="searchParams.name" placeholder="请输入文件名" />
        </div>
        <div class="form-group">
          <label>用户标签</label>
          <input type="text" v-model="searchParams.meeting_type" placeholder="请输入会议类型" />
        </div>
        <button class="search-btn" @click="searchFiles">搜索</button>
        <button class="reset-btn" @click="resetSearch">重置</button>
        <button class="upload-btn" @click="showUploadModal = true" :disabled="uploading">{{ uploading ? '上传中...' : '上传文件' }}</button>
      </div>
    </div>

    <!-- 文件列表 -->
    <div class="content-area">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="files.length === 0" class="empty">暂无文件，请上传音频或视频文件</div>
      <div v-else>
        <!-- 全部标签下的分类展示 -->
        <div v-if="activeTab === 'all'">
          <!-- 视频文件 -->
          <div v-if="videoFiles.length > 0" class="file-section">
            <h3 class="section-title">视频文件</h3>
            <!-- 网格视图 -->
            <div v-if="viewMode === 'grid'" class="grid-view">
              <div v-for="file in videoFiles" :key="file.id" class="grid-item" @click="handleFileClick(file)">
                <div class="item-preview" :class="getFileIcon(file.file_type)">
                  <img v-if="file.thumbnail" :src="file.thumbnail" alt="" />
                  <span class="preview-icon" v-else>{{ getPreviewIcon(file.file_type) }}</span>
                  <!-- 菜单按钮 -->
                  <div class="menu-container" @click.stop>
                    <button class="menu-btn" @click="toggleMenu(file.id)">
                      <span class="icon">⋮</span>
                    </button>
                    <!-- 下拉菜单 -->
                    <div v-if="activeMenu === file.id" class="dropdown-menu" @click.stop>
                      <div class="menu-item" @click="handleRename(file)">重命名</div>
                      <div class="menu-item delete" @click="handleDelete(file.id)">删除</div>
                      <div class="menu-item" @click="openFileLocation(file)">打开本地文件位置</div>
                    </div>
                  </div>
                </div>
                <div class="item-info">
                  <div class="item-name">{{ file.name }}</div>
                  <div class="item-meta">
                    <span>{{ formatDate(file.created_at) }}</span>
                    <span>{{ formatFileSize(file.size) }}</span>
                  </div>
                </div>
              </div>
            </div>
            <!-- 列表视图 -->
            <div v-else class="list-view">
              <table>
                <thead>
                  <tr>
                    <th>文件名称</th>
                    <th>文件大小</th>
                    <th>上传时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="file in videoFiles" :key="file.id" @click="handleFileClick(file)">
                    <td>
                      <span class="file-icon">{{ getPreviewIcon(file.file_type) }}</span>
                      {{ file.name }}
                    </td>
                    <td>{{ formatFileSize(file.size) }}</td>
                    <td>{{ formatDate(file.created_at) }}</td>
                    <td>
                      <!-- 菜单按钮 -->
                      <div class="menu-container" @click.stop>
                        <button class="menu-btn" @click="toggleMenu(file.id)">
                          <span class="icon">⋮</span>
                        </button>
                        <!-- 下拉菜单 -->
                        <div v-if="activeMenu === file.id" class="dropdown-menu" @click.stop>
                          <div class="menu-item" @click="handleRename(file)">重命名</div>
                          <div class="menu-item delete" @click="handleDelete(file.id)">删除</div>
                          <div class="menu-item" @click="openFileLocation(file)">打开本地文件位置</div>
                        </div>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          
          <!-- 音频文件 -->
          <div v-if="audioFiles.length > 0" class="file-section">
            <h3 class="section-title">音频文件</h3>
            <!-- 网格视图 -->
            <div v-if="viewMode === 'grid'" class="grid-view">
              <div v-for="file in audioFiles" :key="file.id" class="grid-item" @click="handleFileClick(file)">
                <div class="item-preview" :class="getFileIcon(file.file_type)">
                  <img v-if="file.thumbnail" :src="file.thumbnail" alt="" />
                  <span class="preview-icon" v-else>{{ getPreviewIcon(file.file_type) }}</span>
                  <!-- 菜单按钮 -->
                  <div class="menu-container" @click.stop>
                    <button class="menu-btn" @click="toggleMenu(file.id)">
                      <span class="icon">⋮</span>
                    </button>
                    <!-- 下拉菜单 -->
                    <div v-if="activeMenu === file.id" class="dropdown-menu" @click.stop>
                      <div class="menu-item" @click="handleRename(file)">重命名</div>
                      <div class="menu-item delete" @click="handleDelete(file.id)">删除</div>
                      <div class="menu-item" @click="openFileLocation(file)">打开本地文件位置</div>
                    </div>
                  </div>
                </div>
                <div class="item-info">
                  <div class="item-name">{{ file.name }}</div>
                  <div class="item-meta">
                    <span>{{ formatDate(file.created_at) }}</span>
                    <span>{{ formatFileSize(file.size) }}</span>
                  </div>
                </div>
              </div>
            </div>
            <!-- 列表视图 -->
            <div v-else class="list-view">
              <table>
                <thead>
                  <tr>
                    <th>文件名称</th>
                    <th>文件大小</th>
                    <th>上传时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="file in audioFiles" :key="file.id" @click="handleFileClick(file)">
                    <td>
                      <span class="file-icon">{{ getPreviewIcon(file.file_type) }}</span>
                      {{ file.name }}
                    </td>
                    <td>{{ formatFileSize(file.size) }}</td>
                    <td>{{ formatDate(file.created_at) }}</td>
                    <td>
                      <!-- 菜单按钮 -->
                      <div class="menu-container" @click.stop>
                        <button class="menu-btn" @click="toggleMenu(file.id)">
                          <span class="icon">⋮</span>
                        </button>
                        <!-- 下拉菜单 -->
                        <div v-if="activeMenu === file.id" class="dropdown-menu" @click.stop>
                          <div class="menu-item" @click="handleRename(file)">重命名</div>
                          <div class="menu-item delete" @click="handleDelete(file.id)">删除</div>
                          <div class="menu-item" @click="openFileLocation(file)">打开本地文件位置</div>
                        </div>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        
        <!-- 视频或音频标签下的展示 -->
        <div v-else>
          <!-- 网格视图 -->
          <div v-if="viewMode === 'grid'" class="grid-view">
            <div v-for="file in filteredFiles" :key="file.id" class="grid-item" @click="handleFileClick(file)">
              <div class="item-preview" :class="getFileIcon(file.file_type)">
                <img v-if="file.thumbnail" :src="file.thumbnail" alt="" />
                <span class="preview-icon" v-else>{{ getPreviewIcon(file.file_type) }}</span>
                <!-- 菜单按钮 -->
                <div class="menu-container" @click.stop>
                  <button class="menu-btn" @click="toggleMenu(file.id)">
                    <span class="icon">⋮</span>
                  </button>
                  <!-- 下拉菜单 -->
                  <div v-if="activeMenu === file.id" class="dropdown-menu" @click.stop>
                    <div class="menu-item" @click="handleRename(file)">重命名</div>
                    <div class="menu-item delete" @click="handleDelete(file.id)">删除</div>
                    <div class="menu-item" @click="openFileLocation(file)">打开本地文件位置</div>
                  </div>
                </div>
              </div>
              <div class="item-info">
                <div class="item-name">{{ file.name }}</div>
                <div class="item-meta">
                  <span>{{ formatDate(file.created_at) }}</span>
                  <span>{{ formatFileSize(file.size) }}</span>
                </div>
              </div>
            </div>
          </div>
          <!-- 列表视图 -->
          <div v-else class="list-view">
            <table>
              <thead>
                <tr>
                  <th>文件名称</th>
                  <th>文件大小</th>
                  <th>上传时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="file in filteredFiles" :key="file.id" @click="handleFileClick(file)">
                  <td>
                    <span class="file-icon">{{ getPreviewIcon(file.file_type) }}</span>
                    {{ file.name }}
                  </td>
                  <td>{{ formatFileSize(file.size) }}</td>
                  <td>{{ formatDate(file.created_at) }}</td>
                  <td>
                    <!-- 菜单按钮 -->
                    <div class="menu-container" @click.stop>
                      <button class="menu-btn" @click="toggleMenu(file.id)">
                        <span class="icon">⋮</span>
                      </button>
                      <!-- 下拉菜单 -->
                      <div v-if="activeMenu === file.id" class="dropdown-menu" @click.stop>
                        <div class="menu-item" @click="handleRename(file)">重命名</div>
                        <div class="menu-item delete" @click="handleDelete(file.id)">删除</div>
                        <div class="menu-item" @click="openFileLocation(file)">打开本地文件位置</div>
                      </div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 重命名模态框 -->
  <div v-if="showRenameModal" class="modal-overlay" @click.self="showRenameModal = false">
    <div class="modal-content">
      <div class="modal-header">
        <h3>重命名文件</h3>
        <button class="close-btn" @click="showRenameModal = false">×</button>
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label>新名称</label>
          <input type="text" v-model="renameFile.newName" placeholder="请输入新名称" />
        </div>
      </div>
      <div class="modal-footer">
        <button class="cancel-btn" @click="showRenameModal = false">取消</button>
        <button class="confirm-btn" @click="handleConfirmRename">确认</button>
      </div>
    </div>
  </div>

  <!-- 上传文件模态框 -->
  <div v-if="showUploadModal" class="modal-overlay" @click.self="showUploadModal = false">
    <div class="modal-content">
      <div class="modal-header">
        <h3>上传文件</h3>
        <button class="close-btn" @click="showUploadModal = false">×</button>
      </div>
      <div class="modal-body">
        <div class="form-group">
          <label>会议用户标签</label>
          <input type="text" v-model="uploadParams.meeting_type" placeholder="请输入会议类型" />
        </div>
        <div class="form-group">
          <label>上传文件</label>
          <div class="file-upload">
            <input
              type="file"
              ref="fileInput"
              @change="handleFileSelect"
              accept="audio/*,video/*"
              multiple
            />
            <div class="file-placeholder" v-if="selectedFiles.length === 0">
                <span class="icon">📁</span>
                <span>点击上传音频或视频文件</span>
            </div>
            <div class="file-selected" v-else>
                <span class="icon">✅</span>
                <span>{{ selectedFiles.length }} 个文件已选择</span>
            </div>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="cancel-btn" @click="showUploadModal = false">取消</button>
        <button class="confirm-btn" @click="handleFileUpload" :disabled="uploading">
          {{ uploading ? '上传中...' : '上传' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { fileApi } from '../api/fileApi';

export default {
  name: 'ConferenceView',
  setup() {
    const router = useRouter();
    // 从localStorage读取上次的视图模式
    const viewMode = ref(localStorage.getItem('conference_view_mode') || 'grid');
    const files = ref([]);
    const loading = ref(false);
    const activeMenu = ref(null);
    const showRenameModal = ref(false);
    const showUploadModal = ref(false);
    const renameFile = ref({ id: null, newName: '' });
    const searchParams = ref({ name: '', meeting_type: '' });
    const uploadParams = ref({ meeting_type: '' });
    const activeTab = ref('all');
    const fileInput = ref(null);
    const uploading = ref(false);
    const selectedFiles = ref([]);

    // 生成视频缩略图
    const generateVideoThumbnail = (file) => {
      return new Promise((resolve, reject) => {
        // 只处理视频文件
        const fileType = file.file_type;
        if (!fileType?.includes('video') && !['mp4', 'avi', 'mov', 'mkv'].includes(fileType)) {
          resolve(null);
          return;
        }

        const video = document.createElement('video');
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        const videoUrl = fileApi.getDownloadUrl(file.id);

        video.src = videoUrl;
        video.crossOrigin = 'anonymous';
        video.currentTime = 1; // 取第1秒的画面

        video.onloadeddata = () => {
          // 设置画布大小与视频相同
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          
          // 绘制视频帧到画布
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          
          // 转换为 base64
          const thumbnailUrl = canvas.toDataURL('image/jpeg', 0.7);
          resolve(thumbnailUrl);
          
          // 清理资源
          video.src = '';
        };

        video.onerror = () => {
          console.error('生成缩略图失败:', file.name);
          resolve(null);
        };
      });
    };

    const loadFiles = async (params = {}) => {
      loading.value = true;
      try {
        const response = await fileApi.getList(params);
        console.log('文件列表响应:', response);
        
        // 支持多种响应格式
        let fileList = [];
        if (response.files && Array.isArray(response.files)) {
          fileList = response.files;
        } else if (response.data?.files && Array.isArray(response.data.files)) {
          fileList = response.data.files;
        } else if (Array.isArray(response.data)) {
          fileList = response.data;
        } else if (Array.isArray(response)) {
          fileList = response;
        }
        
        // 映射字段名（后端用 original_name/file_size/upload_time，前端用 name/size/created_at）
        const mappedFiles = fileList.map(file => ({
          ...file,
          id: file.file_id || file.id,
          name: file.original_name || file.name,
          size: file.file_size || file.size,
          created_at: file.upload_time || file.created_at
        }));
        
        files.value = mappedFiles;
        
        // 异步为视频文件生成缩略图（不阻塞页面加载）
        nextTick(async () => {
          const videoFilesOnly = mappedFiles.filter(file => {
            const fileType = file.file_type;
            return fileType?.includes('video') || ['mp4', 'avi', 'mov', 'mkv'].includes(fileType);
          });
          
          // 并发处理缩略图生成
          const thumbnailPromises = videoFilesOnly.map(async (file) => {
            try {
              const thumbnail = await generateVideoThumbnail(file);
              if (thumbnail) {
                // 更新files数组中的对应文件
                const fileIndex = files.value.findIndex(f => f.id === file.id);
                if (fileIndex !== -1) {
                  files.value[fileIndex].thumbnail = thumbnail;
                }
              }
            } catch (e) {
              console.error('生成缩略图出错:', e);
            }
          });
          
          await Promise.all(thumbnailPromises);
        });
      } catch (error) {
        console.error('加载文件列表失败:', error);
      } finally {
        loading.value = false;
      }
    };

    // 计算属性：过滤后的视频文件
    const videoFiles = computed(() => {
      return files.value.filter(file => {
        const fileType = file.file_type;
        return fileType?.includes('video') || ['mp4', 'avi', 'mov', 'mkv'].includes(fileType);
      });
    });

    // 计算属性：过滤后的音频文件
    const audioFiles = computed(() => {
      return files.value.filter(file => {
        const fileType = file.file_type;
        return !fileType?.includes('video') && !['mp4', 'avi', 'mov', 'mkv'].includes(fileType);
      });
    });

    // 计算属性：根据当前标签过滤的文件
    const filteredFiles = computed(() => {
      if (activeTab.value === 'video') {
        return videoFiles.value;
      } else if (activeTab.value === 'audio') {
        return audioFiles.value;
      } else {
        return files.value;
      }
    });

    // 搜索文件
    const searchFiles = () => {
      // 过滤掉空值参数
      const params = Object.fromEntries(
        Object.entries(searchParams.value)
          .filter(([_, value]) => value !== '')
      );
      loadFiles(params);
    };

    // 重置搜索
    const resetSearch = () => {
      searchParams.value = { name: '', meeting_type: '' };
      loadFiles();
    };

    // 处理文件选择
    const handleFileSelect = (e) => {
      const files = e.target.files;
      if (files.length > 0) {
        selectedFiles.value = Array.from(files);
      }
    };

    // 处理文件上传
    const handleFileUpload = async () => {
      if (selectedFiles.value.length === 0) {
        alert('请选择要上传的文件');
        return;
      }

      uploading.value = true;
      try {
        // 逐个上传文件
        for (const file of selectedFiles.value) {
          await fileApi.uploadTranscribe(file, uploadParams.meeting_type);
        }
        // 上传完成后刷新文件列表
        await loadFiles();
        // 清空表单
        showUploadModal.value = false;
        uploadParams.value = { meeting_type: '' };
        selectedFiles.value = [];
        if (fileInput.value) {
          fileInput.value.value = '';
        }
      } catch (error) {
        console.error('上传文件失败:', error);
        alert('上传文件失败，请重试');
      } finally {
        uploading.value = false;
      }
    };

    const getFileIcon = (fileType) => {
      if (fileType?.includes('video') || ['mp4', 'avi', 'mov', 'mkv'].includes(fileType)) {
        return 'video';
      }
      return 'audio';
    };

    const getPreviewIcon = (fileType) => {
      if (fileType?.includes('video') || ['mp4', 'avi', 'mov', 'mkv'].includes(fileType)) {
        return '🎬';
      }
      return '🎵';
    };

    const formatDate = (dateStr) => {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return date.toLocaleString('zh-CN');
    };

    const formatFileSize = (bytes) => {
      if (!bytes) return '';
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(1024));
      return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    };

    // 切换菜单
    const toggleMenu = (fileId) => {
      if (activeMenu.value === fileId) {
        activeMenu.value = null;
      } else {
        activeMenu.value = fileId;
      }
    };

    // 点击外部关闭菜单
    const handleClickOutside = (event) => {
      if (!event.target.closest('.menu-container')) {
        activeMenu.value = null;
      }
    };

    // 处理重命名
    const handleRename = (file) => {
      renameFile.value = {
        id: file.id,
        newName: file.name
      };
      showRenameModal.value = true;
      activeMenu.value = null;
    };

    // 确认重命名
    const handleConfirmRename = async () => {
      try {
        // 调用后端API进行重命名
        console.log('重命名文件:', renameFile.value.id, renameFile.value.newName);
        const response = await fileApi.rename(renameFile.value.id, renameFile.value.newName);
        console.log('重命名响应:', response);
        // 重命名成功后刷新文件列表
        console.log('开始刷新文件列表');
        await loadFiles();
        console.log('文件列表刷新完成');
        showRenameModal.value = false;
      } catch (error) {
        console.error('重命名文件失败:', error);
        alert('重命名文件失败，请重试');
      }
    };

    // 处理删除
    const handleDelete = async (fileId) => {
      if (confirm('确定要删除这个文件吗？')) {
        try {
          // 调用后端API进行删除
          console.log('删除文件:', fileId);
          const response = await fileApi.delete(fileId);
          console.log('删除响应:', response);
          // 删除成功后刷新文件列表
          console.log('开始刷新文件列表');
          await loadFiles();
          console.log('文件列表刷新完成');
          activeMenu.value = null;
        } catch (error) {
          console.error('删除文件失败:', error);
          alert('删除文件失败，请重试');
        }
      }
    };

    // 打开本地文件位置
    const openFileLocation = (file) => {
      console.log('打开本地文件位置:', file);
      // 这里需要调用后端API获取文件路径，然后打开
      activeMenu.value = null;
    };

    // 点击文件跳转至业务页面
    const handleFileClick = (file) => {
      console.log('🚀 [跳转] 点击文件，准备跳转，file:', file);
      // 先保存到 localStorage 作为备用方案
      localStorage.setItem('currentFileData', JSON.stringify(file));
      router.push({
        name: 'MeetingDetail',
        params: {
          id: file.id
        }
      });
    };

    // 监听视图模式变化，保存到localStorage
    watch(viewMode, (newMode) => {
      localStorage.setItem('conference_view_mode', newMode);
    });

    onMounted(() => {
      loadFiles();
      // 添加点击事件监听器
      document.addEventListener('click', handleClickOutside);
    });

    onUnmounted(() => {
      // 移除点击事件监听器
      document.removeEventListener('click', handleClickOutside);
    });

    return {
      viewMode,
      files,
      loading,
      activeMenu,
      showRenameModal,
      showUploadModal,
      renameFile,
      searchParams,
      uploadParams,
      activeTab,
      fileInput,
      uploading,
      selectedFiles,
      videoFiles,
      audioFiles,
      filteredFiles,
      getFileIcon,
      getPreviewIcon,
      formatDate,
      formatFileSize,
      toggleMenu,
      handleRename,
      handleConfirmRename,
      handleDelete,
      openFileLocation,
      searchFiles,
      resetSearch,
      handleFileSelect,
      handleFileUpload,
      handleFileClick
    };
  }
};
</script>

<style scoped>
.conference-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 1;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #eee;
}

.section-tabs {
  display: flex;
  gap: 16px;
}

.section-tab {
  padding: 8px 16px;
  cursor: pointer;
  border-radius: 6px;
  font-size: 14px;
  color: #666;
  transition: all 0.2s;
}

.section-tab.active {
  background: #409eff;
  color: white;
}

.view-toggle {
  display: flex;
  gap: 8px;
}

.view-toggle button {
  padding: 8px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.view-toggle button.active {
  background: #409eff;
  border-color: #409eff;
  color: white;
}

.search-bar {
  padding: 16px;
  background: #f9fafc;
  border-bottom: 1px solid #eee;
}

.search-form {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.search-form .form-group {
  margin-bottom: 0;
  flex: 1;
  min-width: 200px;
}

.search-form .form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  color: #666;
  font-weight: 500;
}

.search-form .form-group input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
  transition: all 0.2s;
}

.search-form .form-group input:focus {
  outline: none;
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.search-btn, .reset-btn, .upload-btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  height: 36px;
}

.search-btn {
  background: #409eff;
  border: 1px solid #409eff;
  color: white;
}

.search-btn:hover {
  background: #66b1ff;
  border-color: #66b1ff;
}

.reset-btn {
  background: white;
  border: 1px solid #ddd;
  color: #666;
}

.reset-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

.upload-btn {
  background: #67c23a;
  border: 1px solid #67c23a;
  color: white;
}

.upload-btn:hover {
  background: #85ce61;
  border-color: #85ce61;
}

.upload-btn:disabled {
  background: #c0c4cc;
  border-color: #c0c4cc;
  cursor: not-allowed;
}

.file-upload {
  position: relative;
}

.file-upload input {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
}

.file-placeholder,
.file-selected {
  padding: 24px;
  border: 2px dashed #ddd;
  border-radius: 8px;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: #999;
}

.file-selected {
  border-color: #409eff;
  color: #409eff;
}

.file-placeholder .icon,
.file-selected .icon {
  font-size: 32px;
}

.storage-info {
  padding: 12px 24px;
  background: #f5f7fa;
  font-size: 13px;
  color: #666;
}

.content-area {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  z-index: 1;
}

.file-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #eee;
}

.loading,
.empty {
  text-align: center;
  padding: 48px;
  color: #999;
}

.grid-view {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 24px;
}

.grid-item {
  background: white;
  border: 1px solid #eee;
  border-radius: 12px;
  overflow: visible;
  transition: all 0.2s;
  position: relative;
}

.grid-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.item-preview {
  height: 140px;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.item-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.item-preview img + .preview-icon {
  display: none;
}

.preview-icon {
  font-size: 48px;
}

.item-preview.video {
  background: #e6f7ff;
}

.item-preview.audio {
  background: #f0f9ff;
}

.item-info {
  padding: 16px;
}

.item-name {
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

.item-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
}

.list-view {
  position: relative;
  overflow: visible;
}

.list-view table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 12px;
  overflow: visible;
}

.list-view th, .list-view td {
  padding: 16px;
  text-align: left;
  border-bottom: 1px solid #eee;
  overflow: visible;
  position: relative;
}

.list-view td:last-child {
  text-align: right;
}

/* 菜单样式 */
.menu-container {
  position: relative;
  display: inline-block;
}

.menu-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s;
  color: #999;
}

.menu-btn:hover {
  background: #f5f7fa;
  color: #666;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: white;
  border: 1px solid #eee;
  border-radius: 6px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  min-width: 160px;
  z-index: 10000;
  margin-top: 4px;
  overflow: visible;
  white-space: nowrap;
}

.menu-item {
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: background 0.2s;
  text-align: center;
}

.menu-item:hover {
  background: #f5f7fa;
}

.menu-item.delete {
  color: #f56c6c;
}

.menu-item.delete:hover {
  background: #fef0f0;
}

/* 网格视图菜单位置 */
.grid-item .menu-container {
  position: absolute;
  top: 8px;
  right: 8px;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #999;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f5f7fa;
  color: #666;
}

.modal-body {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  box-sizing: border-box;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #eee;
  background: #fafafa;
}

.cancel-btn, .confirm-btn {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn {
  background: white;
  border: 1px solid #ddd;
  color: #666;
}

.cancel-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

.confirm-btn {
  background: #409eff;
  border: 1px solid #409eff;
  color: white;
}

.confirm-btn:hover {
  background: #66b1ff;
  border-color: #66b1ff;
}

.list-view th {
  background: #f5f7fa;
  font-weight: 500;
  color: #666;
  font-size: 14px;
}

.list-view td {
  font-size: 14px;
  color: #333;
}

.file-icon {
  margin-right: 8px;
}
</style>
