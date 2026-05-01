<template>
  <div class="voiceprint-container" ref="containerRef">
    <!-- 顶部标签栏 -->
    <div class="section-header">
      <div class="section-tabs">
        <span class="section-tab active">全部说话人</span>
      </div>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="search-box">
        <input type="text" v-model="searchKeyword" placeholder="搜索说话人姓名..." class="search-input" />
        <button class="search-btn" @click="handleSearch">
          <span class="icon">🔍</span>
        </button>
      </div>
      <div class="add-btn" @click="showAddModal = true">
        <span class="icon">➕</span>
        <span>添加说话人</span>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧：Speaker 列表 -->
      <div class="speakers-list">
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="speakers.length === 0" class="empty">
          {{ searchKeyword ? '没有找到匹配的说话人' : '暂未添加说话人' }}
        </div>
        <div v-else>
          <div
            v-for="sp in speakers"
            :key="sp.id"
            class="speaker-item"
            :class="{ active: selectedSpeaker?.id === sp.id }"
            @click="handleSelectSpeaker(sp)"
          >
            <div class="speaker-avatar">
              <img v-if="sp.avatar_url" :src="API_BASE_URL + sp.avatar_url" class="speaker-avatar-img" alt="说话人头像" />
              <div v-else class="speaker-avatar-default">👤</div>
            </div>
            <div class="speaker-info">
              <div class="speaker-name">{{ sp.name }}</div>
              <div class="speaker-meta">
                <span>{{ formatDate(sp.created_at) }}</span>
                <span class="voice-count"> {{ sp.voiceprints_count }} 条声纹</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：选中 Speaker 的详情和声纹管理 -->
      <div class="speaker-detail" v-if="selectedSpeaker">
        <div class="detail-header">
          <div class="detail-speaker-info">
            <div class="detail-avatar">
              <img v-if="selectedSpeaker.avatar_url" :src="API_BASE_URL + selectedSpeaker.avatar_url" class="detail-avatar-img" alt="说话人头像" />
              <div v-else class="detail-avatar-default">👤</div>
            </div>
            <div>
              <h2 class="detail-name">{{ selectedSpeaker.name }}</h2>
              <span class="detail-meta"> {{ selectedSpeaker.voiceprints_count }} 条声纹</span>
            </div>
          </div>
          <div class="detail-actions">
            <button class="edit-btn" @click="showEditSpeakerModalHandler">✏️ 修改</button>
            <button class="delete-btn" @click="handleDeleteSpeaker">🗑️ 删除</button>
          </div>
        </div>

        <div class="voiceprints-section">
          <div class="section-header">
            <h3>声纹管理</h3>
            <button class="add-voiceprint-btn" @click="showAddVoiceprintModal = true">➕ 追加声纹</button>
          </div>
          <div v-if="loadingVoiceprints" class="loading">加载中...</div>
          <div v-else-if="selectedSpeaker.voiceprints.length === 0" class="empty">
            该说话人暂无声纹，请先添加
          </div>
          <div v-else class="voiceprints-grid">
            <div
              v-for="vp in selectedSpeaker.voiceprints"
              :key="vp.id"
              class="voiceprint-card"
              :class="{ playing: playingVoiceprint?.id === vp.id }"
            >
              <div class="voiceprint-preview" @click="handleTogglePlayVoiceprint(vp)">
                <div v-if="playingVoiceprint?.id === vp.id" class="sound-waves">
                  <div class="wave"></div>
                  <div class="wave"></div>
                  <div class="wave"></div>
                  <div class="wave"></div>
                  <div class="wave"></div>
                </div>
                <div v-else class="play-icon">▶️</div>
              </div>
              <div class="voiceprint-info">
                <div class="source-type">
                  <span :class="vp.source_type === 'manual' ? 'manual-tag' : 'auto-tag'">
                    {{ vp.source_type === 'manual' ? '手动注册' : '会议自动' }}
                  </span>
                </div>
                <div class="voiceprint-date">{{ formatDate(vp.created_at) }}</div>
              </div>
              <div class="voiceprint-actions">
                <button class="update-btn" @click="showUpdateVoiceprintModalHandler(vp)">更新</button>
                <button
                  class="delete-vp-btn"
                  :disabled="isFirstManualVoiceprint(vp)"
                  @click="handleDeleteVoiceprint(vp)"
                >
                  删除
                </button>
              </div>
              <div v-if="isFirstManualVoiceprint(vp)" class="first-voiceprint-badge">第一条声纹</div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty-detail">
        <div class="empty-detail-content">
          <span class="empty-icon">👤</span>
          <p>请选择左侧的说话人查看详情</p>
        </div>
      </div>
    </div>

    <!-- 添加说话人模态框 -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>添加说话人</h3>
          <button class="close-btn" @click="showAddModal = false">×</button>
        </div>
        <div v-if="similarSpeaker" class="similar-warning">
          <p>检测到和「{{ similarSpeaker.name }}」很相似！</p>
          <p>是否强制创建？</p>
          <div class="similar-actions">
            <button class="cancel-btn" @click="showAddModal = false; resetSimilarWarning();">取消</button>
            <button class="confirm-btn" @click="handleForceCreateSpeaker">强制创建</button>
          </div>
        </div>
        <div v-else class="modal-body">
          <div class="form-group">
            <label>说话人姓名</label>
            <input type="text" v-model="newSpeaker.name" placeholder="请输入说话人姓名" />
          </div>
          <div class="form-group">
            <label>上传第一条声纹（可选）</label>
            <div class="file-upload">
              <input type="file" ref="addSpeakerFileInput" @change="handleAddSpeakerFileSelect" accept="audio/*" />
              <div class="file-placeholder" v-if="!newSpeaker.file">
                <span class="icon">📁</span>
                <span>点击上传音频文件</span>
              </div>
              <div class="file-selected" v-else>
                <span class="icon">✅</span>
                <span>{{ newSpeaker.file.name }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-if="!similarSpeaker" class="modal-footer">
          <button class="cancel-btn" @click="showAddModal = false; resetSimilarWarning();">取消</button>
          <button class="confirm-btn" @click="handleAddSpeaker" :disabled="addSpeakerLoading">
            {{ addSpeakerLoading ? '添加中...' : '添加' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 修改说话人模态框 -->
    <div v-if="showEditSpeakerModal" class="modal-overlay" @click.self="showEditSpeakerModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>修改说话人</h3>
          <button class="close-btn" @click="showEditSpeakerModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>说话人姓名</label>
            <input type="text" v-model="editingSpeaker.name" placeholder="请输入说话人姓名" />
          </div>
          <div class="form-group">
            <label>上传头像（可选）</label>
            <div class="file-upload">
              <input type="file" ref="editSpeakerAvatarInput" @change="handleEditSpeakerAvatarSelect" accept="image/*" />
              <div class="file-placeholder" v-if="!editingSpeaker.avatar">
                <span class="icon">📁</span>
                <span>点击上传图片文件</span>
              </div>
              <div class="file-selected" v-else>
                <span class="icon">✅</span>
                <span>{{ editingSpeaker.avatar.name }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="showEditSpeakerModal = false">取消</button>
          <button class="confirm-btn" @click="handleEditSpeaker" :disabled="editSpeakerLoading">
            {{ editSpeakerLoading ? '修改中...' : '修改' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 追加声纹模态框 -->
    <div v-if="showAddVoiceprintModal" class="modal-overlay" @click.self="showAddVoiceprintModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>给「{{ selectedSpeaker?.name }}」追加声纹</h3>
          <button class="close-btn" @click="showAddVoiceprintModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>上传音频文件</label>
            <div class="file-upload">
              <input type="file" ref="addVoiceprintFileInput" @change="handleAddVoiceprintFileSelect" accept="audio/*" />
              <div class="file-placeholder" v-if="!newVoiceprint.file">
                <span class="icon">📁</span>
                <span>点击上传音频文件</span>
              </div>
              <div class="file-selected" v-else>
                <span class="icon">✅</span>
                <span>{{ newVoiceprint.file.name }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="showAddVoiceprintModal = false">取消</button>
          <button class="confirm-btn" @click="handleAddVoiceprint" :disabled="addVoiceprintLoading">
            {{ addVoiceprintLoading ? '追加中...' : '追加' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 更新声纹模态框 -->
    <div v-if="showUpdateVoiceprintModal" class="modal-overlay" @click.self="showUpdateVoiceprintModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>更新声纹</h3>
          <button class="close-btn" @click="showUpdateVoiceprintModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>上传新音频文件</label>
            <div class="file-upload">
              <input type="file" ref="updateVoiceprintFileInput" @change="handleUpdateVoiceprintFileSelect" accept="audio/*" />
              <div class="file-placeholder" v-if="!updatingVoiceprint.file">
                <span class="icon">📁</span>
                <span>点击上传音频文件</span>
              </div>
              <div class="file-selected" v-else>
                <span class="icon">✅</span>
                <span>{{ updatingVoiceprint.file.name }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="cancel-btn" @click="showUpdateVoiceprintModal = false">取消</button>
          <button class="confirm-btn" @click="handleUpdateVoiceprint" :disabled="updateVoiceprintLoading">
            {{ updateVoiceprintLoading ? '更新中...' : '更新' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue';
import { speakerApi } from '../api/speakerApi';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default {
  name: 'VoiceprintView',
  setup() {
    const speakers = ref([]);
    const selectedSpeaker = ref(null);
    const searchKeyword = ref('');
    const loading = ref(false);
    const loadingVoiceprints = ref(false);

    // 模态框显示控制
    const showAddModal = ref(false);
    const showEditSpeakerModal = ref(false);
    const showAddVoiceprintModal = ref(false);
    const showUpdateVoiceprintModal = ref(false);

    // 新建 Speaker 数据
    const newSpeaker = ref({ name: '', file: null });
    const addSpeakerLoading = ref(false);
    const similarSpeaker = ref(null);
    const pendingNewSpeaker = ref(null);

    // 修改 Speaker 数据
    const editingSpeaker = ref({ name: '', avatar: null });
    const editSpeakerLoading = ref(false);

    // 声纹数据
    const newVoiceprint = ref({ file: null });
    const updatingVoiceprint = ref({ id: null, file: null });
    const addVoiceprintLoading = ref(false);
    const updateVoiceprintLoading = ref(false);

    // 播放相关
    const playingVoiceprint = ref(null);
    const audioElement = ref(null);
    const containerRef = ref(null);

    // DOM 引用
    const addSpeakerFileInput = ref(null);
    const editSpeakerAvatarInput = ref(null);
    const addVoiceprintFileInput = ref(null);
    const updateVoiceprintFileInput = ref(null);

    // 格式化日期
    const formatDate = (dateStr) => {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return date.toLocaleString('zh-CN');
    };

    // 加载 Speaker 列表
    const loadSpeakers = async () => {
      loading.value = true;
      try {
        console.log('[DEBUG] 开始获取 Speaker 列表...');
        const response = await speakerApi.getList(searchKeyword.value.trim());
        console.log('[DEBUG] Speaker API 完整返回结果:', response);
        
        if (response?.speakers && Array.isArray(response.speakers)) {
          speakers.value = response.speakers;
        } else if (response?.data?.speakers && Array.isArray(response.data.speakers)) {
          speakers.value = response.data.speakers;
        } else if (Array.isArray(response.data)) {
          speakers.value = response.data;
        } else if (Array.isArray(response)) {
          speakers.value = response;
        }
        
        console.log('[DEBUG] 最终 speakers.value 内容:', speakers.value);
      } catch (error) {
        console.error('加载说话人列表失败:', error);
      } finally {
        loading.value = false;
      }
    };

    // 搜索处理
    const handleSearch = async () => {
      await loadSpeakers();
    };

    // 选择 Speaker
    const handleSelectSpeaker = (sp) => {
      selectedSpeaker.value = { ...sp };
    };

    // 判断是否是第一条 manual 声纹
    const isFirstManualVoiceprint = (vp) => {
      if (!selectedSpeaker.value || selectedSpeaker.value.voiceprints.length === 0) return false;
      const manualVoiceprints = selectedSpeaker.value.voiceprints
        .filter(v => v.source_type === 'manual')
        .sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
      if (manualVoiceprints.length === 0) return false;
      return manualVoiceprints[0].id === vp.id;
    };

    // 添加 Speaker
    const handleAddSpeaker = async () => {
      if (!newSpeaker.value.name) {
        alert('请填写说话人姓名');
        return;
      }
      addSpeakerLoading.value = true;
      try {
        const res = await speakerApi.add(newSpeaker.value.name, newSpeaker.value.file);
        if (res.status === 'warning' && res.similar_speaker) {
          similarSpeaker.value = res.similar_speaker;
          pendingNewSpeaker.value = { name: newSpeaker.value.name, file: newSpeaker.value.file };
        } else {
          await loadSpeakers();
          showAddModal.value = false;
          resetSimilarWarning();
          newSpeaker.value = { name: '', file: null };
        }
      } catch (error) {
        console.error('添加说话人失败:', error);
        alert('添加说话人失败');
      } finally {
        addSpeakerLoading.value = false;
      }
    };

    // 强制创建 Speaker
    const handleForceCreateSpeaker = async () => {
      addSpeakerLoading.value = true;
      try {
        await speakerApi.add(pendingNewSpeaker.value.name, pendingNewSpeaker.value.file, true);
        await loadSpeakers();
        showAddModal.value = false;
        resetSimilarWarning();
        newSpeaker.value = { name: '', file: null };
      } catch (error) {
        console.error('强制创建说话人失败:', error);
        alert('强制创建说话人失败');
      } finally {
        addSpeakerLoading.value = false;
      }
    };

    // 重置相似警告
    const resetSimilarWarning = () => {
      similarSpeaker.value = null;
      pendingNewSpeaker.value = null;
    };

    // 选择上传 Speaker 的第一个声纹
    const handleAddSpeakerFileSelect = (e) => {
      const file = e.target.files[0];
      if (file) {
        newSpeaker.value.file = file;
      }
    };

    // 选择修改 Speaker 的头像
    const handleEditSpeakerAvatarSelect = (e) => {
      const file = e.target.files[0];
      if (file) {
        editingSpeaker.value.avatar = file;
      }
    };

    // 显示修改 Speaker 模态框
    const showEditSpeakerModalHandler = () => {
      editingSpeaker.value = { name: selectedSpeaker.value.name, avatar: null };
      showEditSpeakerModal.value = true;
    };

    // 修改 Speaker
    const handleEditSpeaker = async () => {
      console.log('[DEBUG] 开始修改 Speaker...');
      console.log('[DEBUG] editingSpeaker.value:', editingSpeaker.value);
      console.log('[DEBUG] selectedSpeaker.value:', selectedSpeaker.value);
      
      if (!editingSpeaker.value.name) {
        alert('请填写说话人姓名');
        return;
      }
      editSpeakerLoading.value = true;
      try {
        const nameToSend = editingSpeaker.value.name !== selectedSpeaker.value.name ? editingSpeaker.value.name : null;
        const avatarToSend = editingSpeaker.value.avatar;
        
        console.log('[DEBUG] 发送请求 nameToSend:', nameToSend);
        console.log('[DEBUG] 发送请求 avatarToSend:', avatarToSend);
        
        const res = await speakerApi.update(
          selectedSpeaker.value.id,
          nameToSend,
          avatarToSend
        );
        
        console.log('[DEBUG] 修改 Speaker API 返回结果:', res);
        
        await loadSpeakers();
        // 更新选中的 Speaker
        const updated = speakers.value.find(sp => sp.id === selectedSpeaker.value.id);
        if (updated) {
          selectedSpeaker.value = { ...updated };
        }
        showEditSpeakerModal.value = false;
      } catch (error) {
        console.error('修改说话人失败:', error);
        alert('修改说话人失败');
      } finally {
        editSpeakerLoading.value = false;
      }
    };

    // 删除 Speaker
    const handleDeleteSpeaker = async () => {
      if (!confirm(`确定要删除说话人「${selectedSpeaker.value.name}」吗？这会同时删除该说话人的所有声纹！`)) {
        return;
      }
      try {
        await speakerApi.delete(selectedSpeaker.value.id);
        await loadSpeakers();
        selectedSpeaker.value = null;
      } catch (error) {
        console.error('删除说话人失败:', error);
        alert('删除说话人失败');
      }
    };

    // 追加声纹
    const handleAddVoiceprintFileSelect = (e) => {
      const file = e.target.files[0];
      if (file) {
        newVoiceprint.value.file = file;
      }
    };

    const handleAddVoiceprint = async () => {
      if (!newVoiceprint.value.file) {
        alert('请上传音频文件');
        return;
      }
      addVoiceprintLoading.value = true;
      try {
        await speakerApi.addVoiceprint(selectedSpeaker.value.id, newVoiceprint.value.file);
        await loadSpeakers();
        const updated = speakers.value.find(sp => sp.id === selectedSpeaker.value.id);
        if (updated) {
          selectedSpeaker.value = { ...updated };
        }
        showAddVoiceprintModal.value = false;
        newVoiceprint.value = { file: null };
      } catch (error) {
        console.error('追加声纹失败:', error);
        alert('追加声纹失败');
      } finally {
        addVoiceprintLoading.value = false;
      }
    };

    // 更新声纹
    const showUpdateVoiceprintModalHandler = (vp) => {
      updatingVoiceprint.value = { id: vp.id, file: null };
      showUpdateVoiceprintModal.value = true;
    };

    const handleUpdateVoiceprintFileSelect = (e) => {
      const file = e.target.files[0];
      if (file) {
        updatingVoiceprint.value.file = file;
      }
    };

    const handleUpdateVoiceprint = async () => {
      console.log('[DEBUG] 开始更新声纹...');
      console.log('[DEBUG] updatingVoiceprint.value:', updatingVoiceprint.value);
      
      if (!updatingVoiceprint.value.file) {
        alert('请上传新的音频文件');
        return;
      }
      updateVoiceprintLoading.value = true;
      try {
        const res = await speakerApi.updateVoiceprint(selectedSpeaker.value.id, updatingVoiceprint.value.id, updatingVoiceprint.value.file);
        console.log('[DEBUG] 更新声纹 API 返回结果:', res);
        
        await loadSpeakers();
        const updated = speakers.value.find(sp => sp.id === selectedSpeaker.value.id);
        if (updated) {
          selectedSpeaker.value = { ...updated };
        }
        showUpdateVoiceprintModal.value = false;
        updatingVoiceprint.value = { id: null, file: null };
      } catch (error) {
        console.error('更新声纹失败:', error);
        alert('更新声纹失败');
      } finally {
        updateVoiceprintLoading.value = false;
      }
    };

    // 删除声纹
    const handleDeleteVoiceprint = async (vp) => {
      console.log('[DEBUG] 开始删除声纹...');
      console.log('[DEBUG] 要删除的声纹:', vp);
      
      if (isFirstManualVoiceprint(vp)) {
        alert('这是该说话人第一条手动注册的声纹，不能删除！');
        return;
      }
      if (!confirm(`确定要删除这条声纹吗？`)) {
        return;
      }
      try {
        const res = await speakerApi.deleteVoiceprint(selectedSpeaker.value.id, vp.id);
        console.log('[DEBUG] 删除声纹 API 返回结果:', res);
        
        await loadSpeakers();
        const updated = speakers.value.find(sp => sp.id === selectedSpeaker.value.id);
        if (updated) {
          selectedSpeaker.value = { ...updated };
        }
      } catch (error) {
        console.error('删除声纹失败:', error);
        alert('删除声纹失败');
      }
    };

    // 播放/停止声纹音频
    const handleTogglePlayVoiceprint = (vp) => {
      if (playingVoiceprint.value?.id === vp.id) {
        stopPlayback();
      } else {
        playVoiceprintAudio(vp);
      }
    };

    const playVoiceprintAudio = async (vp) => {
      stopPlayback();
      
      try {
        console.log('[DEBUG] ============= 开始播放声纹 =============');
        console.log('[DEBUG] 完整 vp 对象:', vp);
        console.log('[DEBUG] vp.audio_url 值:', vp.audio_url);
        
        // 🌟 优先使用 audio_url
        let audioUrl = null;
        if (vp.audio_url) {
          audioUrl = API_BASE_URL + vp.audio_url;
        }
        
        console.log('[DEBUG] API_BASE_URL:', API_BASE_URL);
        console.log('[DEBUG] 最终 audioUrl:', audioUrl);
        
        if (!audioUrl) {
          alert('该声纹没有对应的音频文件');
          return;
        }
        
        // 先尝试用 fetch 测试一下这个 URL 是否能请求到
        console.log('[DEBUG] 用 fetch 测试 URL 是否可访问...');
        try {
          const testResp = await fetch(audioUrl, { method: 'HEAD' });
          console.log('[DEBUG] fetch HEAD 状态码:', testResp.status, testResp.statusText);
          if (testResp.status === 404) {
            console.error('[DEBUG] 文件不存在！404 错误！');
            alert('音频文件不存在 (404)！请检查后端是否正确保存了文件！');
            return;
          }
        } catch (fetchErr) {
          console.warn('[DEBUG] HEAD 请求失败，可能是跨域，继续尝试播放:', fetchErr);
        }
        
        playingVoiceprint.value = vp;
        audioElement.value = new Audio(audioUrl);
        
        audioElement.value.onerror = (e) => {
          console.error('[DEBUG] 音频加载错误事件对象:', e);
          console.error('[DEBUG] audioElement 错误:', audioElement.value.error);
          alert('音频加载失败，请检查网络或文件是否存在');
          stopPlayback();
        };
        
        audioElement.value.onloadedmetadata = () => {
          console.log('[DEBUG] 音频元数据加载成功！时长:', audioElement.value.duration);
        };
        
        audioElement.value.onended = () => {
          stopPlayback();
        };
        
        console.log('[DEBUG] 开始调用 audioElement.play()...');
        const playPromise = audioElement.value.play();
        if (playPromise !== undefined) {
          playPromise.then(_ => {
            console.log('[DEBUG] 播放成功开始！');
          })
          .catch(error => {
            console.error('[DEBUG] play() 抛出异常:', error);
            alert('播放失败: ' + (error.message || '未知错误'));
            stopPlayback();
          });
        }
      } catch (error) {
        console.error('[DEBUG] 播放失败（外层 catch）:', error);
        console.error('[DEBUG] 错误栈:', error.stack);
        alert('播放失败: ' + (error.message || '未知错误'));
        stopPlayback();
      }
    };

    const stopPlayback = () => {
      if (audioElement.value) {
        audioElement.value.pause();
        audioElement.value = null;
      }
      playingVoiceprint.value = null;
    };

    onMounted(() => {
      loadSpeakers();
    });

    onUnmounted(() => {
      stopPlayback();
    });

    return {
      API_BASE_URL,
      speakers,
      selectedSpeaker,
      searchKeyword,
      loading,
      loadingVoiceprints,
      showAddModal,
      showEditSpeakerModal,
      showAddVoiceprintModal,
      showUpdateVoiceprintModal,
      newSpeaker,
      addSpeakerLoading,
      similarSpeaker,
      editingSpeaker,
      editSpeakerLoading,
      newVoiceprint,
      updatingVoiceprint,
      addVoiceprintLoading,
      updateVoiceprintLoading,
      playingVoiceprint,
      containerRef,
      addSpeakerFileInput,
      editSpeakerAvatarInput,
      addVoiceprintFileInput,
      updateVoiceprintFileInput,
      formatDate,
      handleSearch,
      handleSelectSpeaker,
      isFirstManualVoiceprint,
      handleAddSpeaker,
      handleForceCreateSpeaker,
      resetSimilarWarning,
      handleAddSpeakerFileSelect,
      handleEditSpeakerAvatarSelect,
      showEditSpeakerModalHandler,
      showEditSpeakerModal,
      handleEditSpeaker,
      handleDeleteSpeaker,
      handleAddVoiceprintFileSelect,
      handleAddVoiceprint,
      showUpdateVoiceprintModalHandler,
      showUpdateVoiceprintModal,
      handleUpdateVoiceprintFileSelect,
      handleUpdateVoiceprint,
      handleDeleteVoiceprint,
      handleTogglePlayVoiceprint
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

.main-content {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

.speakers-list {
  width: 320px;
  min-width: 320px;
  background: white;
  border: 1px solid #eee;
  border-radius: 12px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.speaker-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: all 0.2s;
}

.speaker-item:hover {
  background: #f5f7fa;
}

.speaker-item.active {
  background: #e8f4ff;
  border-left: 3px solid #409eff;
}

.speaker-avatar {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
}

.speaker-avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.speaker-avatar-default {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.speaker-info {
  flex: 1;
  overflow: hidden;
}

.speaker-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.speaker-meta {
  font-size: 12px;
  color: #999;
  display: flex;
  gap: 8px;
}

.speaker-detail {
  flex: 1;
  background: white;
  border: 1px solid #eee;
  border-radius: 12px;
  padding: 24px;
  overflow-y: auto;
}

.empty-detail {
  flex: 1;
  background: white;
  border: 1px solid #eee;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-detail-content {
  text-align: center;
  color: #999;
}

.empty-icon {
  font-size: 64px;
  display: block;
  margin-bottom: 16px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 24px;
  border-bottom: 1px solid #eee;
  margin-bottom: 24px;
}

.detail-speaker-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.detail-avatar {
  width: 72px;
  height: 72px;
}

.detail-avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.detail-avatar-default {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
}

.detail-name {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.detail-meta {
  font-size: 14px;
  color: #999;
}

.detail-actions {
  display: flex;
  gap: 8px;
}

.edit-btn {
  padding: 10px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.edit-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

.delete-btn {
  padding: 10px 16px;
  border: 1px solid #f56c6c;
  background: white;
  color: #f56c6c;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.delete-btn:hover {
  background: #fef0f0;
}

.voiceprints-section {
  margin-top: 24px;
}

.voiceprints-section .section-header {
  border-bottom: none;
  padding: 0;
  margin-bottom: 20px;
}

.voiceprints-section .section-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.add-voiceprint-btn {
  padding: 10px 16px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.add-voiceprint-btn:hover {
  background: #66b1ff;
}

.voiceprints-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.voiceprint-card {
  background: white;
  border: 1px solid #eee;
  border-radius: 12px;
  padding: 16px;
  position: relative;
  transition: all 0.2s;
}

.voiceprint-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.voiceprint-card.playing {
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  border-color: #409eff;
}

.voiceprint-preview {
  height: 120px;
  background: #f5f7fa;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  margin-bottom: 12px;
}

.play-icon {
  font-size: 28px;
}

.sound-waves {
  display: flex;
  align-items: center;
  gap: 3px;
}

.sound-waves .wave {
  width: 4px;
  background: #409eff;
  border-radius: 2px;
  animation: wave 0.5s ease-in-out infinite;
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

.voiceprint-info {
  margin-bottom: 12px;
}

.source-type {
  margin-bottom: 4px;
}

.manual-tag {
  padding: 4px 8px;
  background: #e8f4ff;
  color: #409eff;
  border-radius: 4px;
  font-size: 12px;
}

.auto-tag {
  padding: 4px 8px;
  background: #f0f9ff;
  color: #096dd9;
  border-radius: 4px;
  font-size: 12px;
}

.voiceprint-date {
  font-size: 12px;
  color: #999;
}

.voiceprint-actions {
  display: flex;
  gap: 8px;
}

.update-btn {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.update-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

.delete-vp-btn {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  color: #f56c6c;
  border-color: #f56c6c;
}

.delete-vp-btn:hover:not(:disabled) {
  background: #fef0f0;
}

.delete-vp-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.first-voiceprint-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  padding: 4px 8px;
  background: #f5a623;
  color: white;
  font-size: 10px;
  border-radius: 12px;
}

.loading,
.empty {
  text-align: center;
  padding: 48px;
  color: #999;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
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

.similar-warning {
  padding: 24px;
  text-align: center;
}

.similar-warning p {
  margin: 0 0 20px;
  font-size: 14px;
  color: #333;
}

.similar-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
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

.confirm-btn:hover:not(:disabled) {
  background: #66b1ff;
}

.confirm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
