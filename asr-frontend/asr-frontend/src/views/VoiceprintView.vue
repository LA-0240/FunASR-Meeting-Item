<template>
  <div class="voiceprint-container" ref="containerRef" @click="handleClickOutside">
    <!-- 顶部标签栏 -->
    <div class="section-header">
      <div class="section-tabs">
        <span class="section-tab active">全部声纹</span>
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

    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="search-box">
        <input type="text" v-model="searchKeyword" placeholder="搜索声纹名称..." class="search-input" />
        <button class="search-btn" @click="handleSearch">
          <span class="icon">🔍</span>
        </button>
      </div>
      <div class="add-btn" @click="showAddModal = true">
        <span class="icon">➕</span>
        <span>添加声纹</span>
      </div>
    </div>

    <!-- 声纹列表 -->
    <div class="content-area">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="filteredVoiceprints.length === 0" class="empty">
        {{ searchKeyword ? '没有找到匹配的声纹' : '暂无声纹数据' }}
      </div>
      <div v-else>
        <!-- 网格视图 -->
        <div v-if="viewMode === 'grid'" class="grid-view">
          <div 
            v-for="item in filteredVoiceprints" 
            :key="item.id" 
            class="grid-item"
            :class="{ 'playing-orange': playingId === item.id && !isPaused, 'playing-green': playingId === item.id && isPaused }"
            @click="handleTogglePlay(item)"
          >
            <div class="item-preview">
              <span class="preview-icon">👤</span>
              <div v-if="playingId === item.id" class="sound-waves" :class="{ paused: isPaused }">
                <div class="wave"></div>
                <div class="wave"></div>
                <div class="wave"></div>
                <div class="wave"></div>
                <div class="wave"></div>
              </div>
            </div>
            <div class="item-info">
              <div class="item-name">{{ item.name }}</div>
              <div class="item-meta">
                <span>{{ formatDate(item.created_at) }}</span>
              </div>
            </div>
            <div class="item-actions" @click.stop>
              <button @click="handleRename(item)">重命名</button>
              <button class="delete" @click="handleDelete(item.id)">删除</button>
            </div>
          </div>
        </div>
        <!-- 列表视图 -->
        <div v-else class="list-view">
          <table>
            <thead>
              <tr>
                <th>声纹名称</th>
                <th>播放</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in filteredVoiceprints" :key="item.id">
                <td>
                  <span class="icon">👤</span>
                  {{ item.name }}
                </td>
                <td>
                  <div class="play-control" @click="handleTogglePlay(item)">
                    <span v-if="playingId !== item.id || isPaused" class="play-icon">▶️</span>
                    <span v-else class="pause-icon">⏸️</span>
                    <div v-if="playingId === item.id" class="sound-waves-small" :class="{ paused: isPaused }">
                      <div class="wave"></div>
                      <div class="wave"></div>
                      <div class="wave"></div>
                      <div class="wave"></div>
                      <div class="wave"></div>
                    </div>
                    <span v-if="playingId === item.id" class="current-time">{{ formatTime(currentTime) }}</span>
                  </div>
                </td>
                <td>{{ formatDate(item.created_at) }}</td>
                <td class="actions">
                  <button @click="handleRename(item)">重命名</button>
                  <button class="delete" @click="handleDelete(item.id)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 添加声纹模态框 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>添加声纹</h3>
          <button class="close-btn" @click="showAddModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>声纹名称</label>
            <input type="text" v-model="newVoiceprint.name" placeholder="请输入声纹名称" />
          </div>
          <div class="form-group">
            <label>上传音频文件</label>
            <div class="file-upload">
              <input
                type="file"
                ref="fileInput"
                @change="handleFileSelect"
                accept="audio/*"
              />
              <div class="file-placeholder" v-if="!selectedFile">
                  <span class="icon">📁</span>
                  <span>点击上传音频文件</span>
              </div>
              <div class="file-selected" v-else>
                  <span class="icon">✅</span>
                  <span>{{ selectedFile.name }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="showAddModal = false">取消</button>
          <button class="confirm-btn" @click="handleAddVoiceprint" :disabled="addLoading">
            {{ addLoading ? '添加中...' : '添加' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 重命名模态框 -->
    <div v-if="showRenameModal" class="modal-overlay" @click.self="showRenameModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>重命名声纹</h3>
          <button class="close-btn" @click="showRenameModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>新名称</label>
            <input type="text" v-model="renameVoiceprint.newName" placeholder="请输入新名称" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="showRenameModal = false">取消</button>
          <button class="confirm-btn" @click="handleConfirmRename">确认</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, onUnmounted, computed } from 'vue';
import { voiceprintApi } from '../api/voiceprintApi';

export default {
  name: 'VoiceprintView',
  setup() {
    const viewMode = ref(localStorage.getItem('voiceprint_view_mode') || 'grid');
    const voiceprints = ref([]);
    const searchKeyword = ref('');
    const loading = ref(false);
    const showAddModal = ref(false);
    const showRenameModal = ref(false);
    const addLoading = ref(false);
    const newVoiceprint = ref({ name: '' });
    const renameVoiceprint = ref({ id: null, newName: '' });
    const selectedFile = ref(null);
    const fileInput = ref(null);
    const containerRef = ref(null);
    const playingId = ref(null);
    const isPaused = ref(false);
    const currentTime = ref(0);
    const audioElement = ref(null);
    const timeUpdateInterval = ref(null);
    const isLoading = ref(false);

    // 根据关键词筛选声纹
    const filteredVoiceprints = computed(() => {
      let filtered = voiceprints.value;
      
      // 按关键词搜索
      if (searchKeyword.value.trim()) {
        const keyword = searchKeyword.value.toLowerCase().trim();
        filtered = filtered.filter(item => 
          item.name.toLowerCase().includes(keyword)
        );
      }
      
      return filtered;
    });

    const handleSearch = () => {
      // 搜索逻辑已经在computed属性中实现，这里可以添加额外的逻辑
      console.log('搜索关键词:', searchKeyword.value);
    };

    const loadVoiceprints = async () => {
      loading.value = true;
      try {
        const response = await voiceprintApi.getList();
        console.log('声纹列表响应:', response);
        
        // 支持多种响应格式
        if (response.voiceprints && Array.isArray(response.voiceprints)) {
          voiceprints.value = response.voiceprints;
        } else if (response.data?.voiceprints && Array.isArray(response.data.voiceprints)) {
          voiceprints.value = response.data.voiceprints;
        } else if (Array.isArray(response.data)) {
          voiceprints.value = response.data;
        } else if (Array.isArray(response)) {
          voiceprints.value = response;
        }
      } catch (error) {
        console.error('加载声纹列表失败:', error);
      } finally {
        loading.value = false;
      }
    };

    const handleFileSelect = (e) => {
      const file = e.target.files[0];
      if (file) {
        selectedFile.value = file;
      }
    };

    const handleAddVoiceprint = async () => {
      if (!newVoiceprint.value.name || !selectedFile.value) {
        alert('请填写声纹名称并选择文件');
        return;
      }
      addLoading.value = true;
      try {
        await voiceprintApi.add(selectedFile.value, newVoiceprint.value.name);
        await loadVoiceprints();
        showAddModal.value = false;
        newVoiceprint.value = { name: '' };
        selectedFile.value = null;
        if (fileInput.value) {
          fileInput.value.value = '';
        }
      } catch (error) {
        console.error('添加声纹失败:', error);
        alert('添加声纹失败');
      } finally {
        addLoading.value = false;
      }
    };

    const handleRename = (item) => {
      renameVoiceprint.value = { id: item.id, newName: item.name };
      showRenameModal.value = true;
    };

    const handleConfirmRename = async () => {
      try {
        await voiceprintApi.rename(renameVoiceprint.value.id, renameVoiceprint.value.newName);
        await loadVoiceprints();
        showRenameModal.value = false;
      } catch (error) {
        console.error('重命名失败:', error);
        alert('重命名失败');
      }
    };

    const handleDelete = async (voiceprintId) => {
      if (playingId.value === voiceprintId) {
        stopPlayback();
      }
      if (!confirm('确定要删除这个声纹吗？')) {
        return;
      }
      try {
        await voiceprintApi.delete(voiceprintId);
        await loadVoiceprints();
      } catch (error) {
        console.error('删除声纹失败:', error);
        alert('删除声纹失败');
      }
    };

    const handleTogglePlay = (item) => {
      // 防止重复点击导致多个音频同时播放
      if (isLoading.value) {
        return;
      }
      
      // 如果点击的是当前正在播放的声纹
      if (playingId.value === item.id) {
        if (isPaused.value) {
          // 暂停状态，继续播放
          resumePlayback();
        } else {
          // 播放状态，暂停
          pausePlayback();
        }
      } else {
        // 点击的是其他声纹，停止当前播放，开始新的播放
        stopPlayback();
        startPlayback(item);
      }
    };

    const startPlayback = async (item) => {
      // 立即设置播放状态，确保UI及时更新
      playingId.value = item.id;
      isPaused.value = false;
      currentTime.value = 0;
      
      // 设置加载状态，防止重复点击
      isLoading.value = true;
      
      try {
        // 使用新的API获取音频文件
        const response = await voiceprintApi.getAudio(item.id);
        const blob = new Blob([response.data], { type: 'audio/wav' });
        const url = URL.createObjectURL(blob);
        
        // 创建新的音频元素
        audioElement.value = new Audio(url);
        
        // 监听播放结束
        audioElement.value.addEventListener('ended', () => {
          stopPlayback();
        });

        // 监听播放时间更新
        timeUpdateInterval.value = setInterval(() => {
          if (audioElement.value && !isPaused.value) {
            currentTime.value = audioElement.value.currentTime;
          }
        }, 100);

        // 开始播放
        await audioElement.value.play();
      } catch (error) {
        console.error('播放失败:', error);
        alert('播放失败，请检查音频文件');
        stopPlayback();
      } finally {
        // 无论成功失败，都清除加载状态
        isLoading.value = false;
      }
    };

    // 点击空白处停止播放
    const handleClickOutside = (event) => {
      // 检查点击是否在声纹卡片或播放控制区域外
      const isGridItem = event.target.closest('.grid-item');
      const isPlayControl = event.target.closest('.play-control');
      
      if (!isGridItem && !isPlayControl) {
        stopPlayback();
      }
    };

    const pausePlayback = () => {
      if (audioElement.value) {
        audioElement.value.pause();
        isPaused.value = true;
      }
    };

    const resumePlayback = () => {
      if (audioElement.value) {
        audioElement.value.play().catch(error => {
          console.error('继续播放失败:', error);
        });
        isPaused.value = false;
      }
    };

    const stopPlayback = () => {
      if (audioElement.value) {
        audioElement.value.pause();
        audioElement.value = null;
      }
      if (timeUpdateInterval.value) {
        clearInterval(timeUpdateInterval.value);
        timeUpdateInterval.value = null;
      }
      playingId.value = null;
      isPaused.value = false;
      currentTime.value = 0;
      isLoading.value = false; // 清除加载状态
    };

    const formatDate = (dateStr) => {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return date.toLocaleString('zh-CN');
    };

    const formatTime = (seconds) => {
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    // 监听视图模式变化，保存到localStorage
    watch(viewMode, (newMode) => {
      localStorage.setItem('voiceprint_view_mode', newMode);
    });

    // 组件卸载时停止播放
    onUnmounted(() => {
      stopPlayback();
      // 移除点击事件监听器
      document.removeEventListener('click', handleClickOutside);
    });

    onMounted(() => {
      loadVoiceprints();
      // 添加点击事件监听器
      document.addEventListener('click', handleClickOutside);
    });

    return {
      viewMode,
      voiceprints,
      filteredVoiceprints,
      searchKeyword,
      loading,
      showAddModal,
      showRenameModal,
      addLoading,
      newVoiceprint,
      renameVoiceprint,
      selectedFile,
      fileInput,
      containerRef,
      playingId,
      isPaused,
      currentTime,
      isLoading,
      loadVoiceprints,
      handleFileSelect,
      handleAddVoiceprint,
      handleRename,
      handleConfirmRename,
      handleDelete,
      handleTogglePlay,
      handleSearch,
      handleClickOutside,
      formatDate,
      formatTime
    };
  }
};
</script>

<style scoped>
.voiceprint-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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

.action-bar {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  width: 200px;
  box-sizing: border-box;
}

.search-btn {
  padding: 8px 12px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.search-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

.add-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.add-btn:hover {
  background: #66b1ff;
}

.content-area {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.loading,
.empty {
  text-align: center;
  padding: 48px;
  color: #999;
}

.grid-view {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 24px;
}

.grid-item {
  background: white;
  border: 1px solid #eee;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s;
  cursor: pointer;
  position: relative;
}

.grid-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.grid-item.playing-orange {
  box-shadow: 0 4px 12px rgba(255, 140, 0, 0.4);
  border-color: #ff8c00;
}

.grid-item.playing-orange .item-preview {
  background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
}

.grid-item.playing-green {
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
  border-color: #4caf50;
}

.grid-item.playing-green .item-preview {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
}

.item-preview {
  height: 160px;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: all 0.3s;
}

.preview-icon {
  font-size: 64px;
  z-index: 1;
}

.sound-waves {
  position: absolute;
  bottom: 20px;
  display: flex;
  align-items: center;
  gap: 3px;
  z-index: 2;
}

.sound-waves .wave {
  width: 4px;
  background: #409eff;
  border-radius: 2px;
  animation: wave 0.5s ease-in-out infinite;
}

.sound-waves.paused .wave {
  animation: none;
  transform: scaleY(0.5);
}

.sound-waves .wave:nth-child(1) {
  height: 16px;
  animation-delay: 0s;
}

.sound-waves .wave:nth-child(2) {
  height: 24px;
  animation-delay: 0.1s;
}

.sound-waves .wave:nth-child(3) {
  height: 32px;
  animation-delay: 0.2s;
}

.sound-waves .wave:nth-child(4) {
  height: 24px;
  animation-delay: 0.3s;
}

.sound-waves .wave:nth-child(5) {
  height: 16px;
  animation-delay: 0.4s;
}

@keyframes wave {
  0%, 100% {
    transform: scaleY(0.5);
  }
  50% {
    transform: scaleY(1);
  }
}

.item-info {
  padding: 16px;
}

.item-name {
  font-size: 14px;
  color: #333;
  margin-bottom: 8px;
  font-weight: 500;
}

.item-meta {
  font-size: 12px;
  color: #999;
}

.item-actions {
  padding: 0 16px 16px;
  display: flex;
  gap: 8px;
}

.item-actions button {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.item-actions button:hover {
  border-color: #409eff;
  color: #409eff;
}

.item-actions button.delete {
  border-color: #f56c6c;
  color: #f56c6c;
}

.item-actions button.delete:hover {
  background: #fef0f0;
}

.list-view table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 12px;
  overflow: hidden;
}

.list-view th,
.list-view td {
  padding: 16px;
  text-align: left;
  border-bottom: 1px solid #eee;
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

.list-view td .icon {
  margin-right: 8px;
}

.play-control {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 6px;
  transition: background 0.2s;
  min-height: 30px;
  width: 200px;
}

.play-control:hover {
  background: #f5f7fa;
}

.play-icon,
.pause-icon {
  font-size: 18px;
}

.sound-waves-small {
  display: flex;
  align-items: center;
  gap: 2px;
}

.sound-waves-small .wave {
  width: 3px;
  background: #409eff;
  border-radius: 1px;
  animation: waveSmall 0.5s ease-in-out infinite;
}

.sound-waves-small.paused .wave {
  animation: none;
  transform: scaleY(0.5);
}

.play-control .play-icon,
.play-control .pause-icon {
  cursor: pointer;
  user-select: none;
  pointer-events: none;
}

.sound-waves-small .wave:nth-child(1) {
  height: 12px;
  animation-delay: 0s;
}

.sound-waves-small .wave:nth-child(2) {
  height: 16px;
  animation-delay: 0.1s;
}

.sound-waves-small .wave:nth-child(3) {
  height: 20px;
  animation-delay: 0.2s;
}

.sound-waves-small .wave:nth-child(4) {
  height: 16px;
  animation-delay: 0.3s;
}

.sound-waves-small .wave:nth-child(5) {
  height: 12px;
  animation-delay: 0.4s;
}

@keyframes waveSmall {
  0%, 100% {
    transform: scaleY(0.5);
  }
  50% {
    transform: scaleY(1);
  }
}

.current-time {
  font-size: 12px;
  color: #666;
  min-width: 40px;
}

.list-view .actions {
  display: flex;
  gap: 8px;
}

.list-view .actions button {
  padding: 6px 12px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.list-view .actions button:hover {
  border-color: #409eff;
  color: #409eff;
}

.list-view .actions button.delete {
  border-color: #f56c6c;
  color: #f56c6c;
}

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
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 480px;
  max-width: 90%;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #999;
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

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #eee;
}

.cancel-btn,
.confirm-btn {
  padding: 10px 24px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn {
  background: #f5f7fa;
  color: #666;
}

.confirm-btn {
  background: #409eff;
  color: white;
}

.confirm-btn:hover {
  background: #66b1ff;
}
</style>
