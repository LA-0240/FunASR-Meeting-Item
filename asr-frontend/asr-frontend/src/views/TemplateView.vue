<template>
  <div class="template-container">
    <!-- 顶部标签栏 -->
    <div class="section-header">
      <div class="section-tabs">
        <span 
          v-for="tab in tabs" 
          :key="tab.key"
          class="section-tab"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </span>
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
        <input type="text" v-model="searchKeyword" placeholder="搜索模板名称..." class="search-input" />
        <button class="search-btn" @click="handleSearch">
          <span class="icon">🔍</span>
        </button>
      </div>
      <div class="add-btn" @click="showAddModal = true">
        <span class="icon">➕</span>
        <span>添加模板</span>
      </div>
    </div>

    <!-- 模板列表 -->
    <div class="content-area">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="allTemplates.length === 0" class="empty">暂无模板数据</div>
      <div v-else>
        <!-- 纪要模板部分 -->
        <div v-if="hasSummaryTemplates" class="template-section">
          <div class="section-title">📝 纪要模板</div>
          <div class="templates-wrapper">
            <!-- 网格视图 -->
            <div v-if="viewMode === 'grid'" class="grid-view">
              <div v-for="item in summaryTemplates" :key="item.id" class="grid-item">
                <div class="item-preview">
                  <span class="preview-icon">{{ getCategoryIcon(item.template_type) }}</span>
                </div>
                <div class="item-info">
                  <div class="item-name">{{ item.name }}</div>
                  <div class="item-meta">
                    <span class="type-tag" :class="item.category">{{ getTypeLabel(item.category) }}</span>
                  </div>
                  <div class="item-description">{{ item.category === 'default' ? '系统推荐' : '用户自定义' }}</div>
                </div>
                <div class="item-actions">
                  <button v-if="item.category === 'default'" class="copy" @click="handleCopy(item)">复制</button>
                  <button v-if="item.category === 'default'" class="edit" @click="handleEdit(item, true)">查看</button>
                  <button v-else class="edit" @click="handleEdit(item)">编辑</button>
                  <button v-if="item.category === 'custom'" class="delete" @click="handleDelete(item.id)">删除</button>
                </div>
              </div>
            </div>
            <!-- 列表视图 -->
            <div v-else class="list-view">
              <table>
                <thead>
                  <tr>
                    <th>模板名称</th>
                    <th>类型</th>
                    <th>作者</th>
                    <th>创建时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in summaryTemplates" :key="item.id">
                    <td>
                      <span class="icon">{{ getCategoryIcon(item.template_type) }}</span>
                      {{ item.name }}
                    </td>
                    <td>
                      <span class="type-tag" :class="item.category">{{ getTypeLabel(item.category) }}</span>
                    </td>
                    <td>{{ item.category === 'default' ? '系统推荐' : '用户自定义' }}</td>
                    <td>{{ formatDate(item.created_at || new Date()) }}</td>
                    <td class="actions">
                      <button v-if="item.category === 'default'" class="copy" @click="handleCopy(item)">复制</button>
                      <button v-if="item.category === 'default'" class="edit" @click="handleEdit(item, true)">查看</button>
                      <button v-else class="edit" @click="handleEdit(item)">编辑</button>
                      <button v-if="item.category === 'custom'" class="delete" @click="handleDelete(item.id)">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- 分割线 -->
        <div v-if="hasSummaryTemplates && hasAbstractTemplates" class="divider"></div>

        <!-- 摘要模板部分 -->
        <div v-if="hasAbstractTemplates" class="template-section">
          <div class="section-title">📄 摘要模板</div>
          <div class="templates-wrapper">
            <!-- 网格视图 -->
            <div v-if="viewMode === 'grid'" class="grid-view">
              <div v-for="item in abstractTemplates" :key="item.id" class="grid-item">
                <div class="item-preview">
                  <span class="preview-icon">{{ getCategoryIcon(item.template_type) }}</span>
                </div>
                <div class="item-info">
                  <div class="item-name">{{ item.name }}</div>
                  <div class="item-meta">
                    <span class="type-tag" :class="item.category">{{ getTypeLabel(item.category) }}</span>
                  </div>
                  <div class="item-description">{{ item.category === 'default' ? '系统推荐' : '用户自定义' }}</div>
                </div>
                <div class="item-actions">
                  <button v-if="item.category === 'default'" class="copy" @click="handleCopy(item)">复制</button>
                  <button v-if="item.category === 'default'" class="edit" @click="handleEdit(item, true)">查看</button>
                  <button v-else class="edit" @click="handleEdit(item)">编辑</button>
                  <button v-if="item.category === 'custom'" class="delete" @click="handleDelete(item.id)">删除</button>
                </div>
              </div>
            </div>
            <!-- 列表视图 -->
            <div v-else class="list-view">
              <table>
                <thead>
                  <tr>
                    <th>模板名称</th>
                    <th>类型</th>
                    <th>作者</th>
                    <th>创建时间</th>
                    <th>操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in abstractTemplates" :key="item.id">
                    <td>
                      <span class="icon">{{ getCategoryIcon(item.template_type) }}</span>
                      {{ item.name }}
                    </td>
                    <td>
                      <span class="type-tag" :class="item.category">{{ getTypeLabel(item.category) }}</span>
                    </td>
                    <td>{{ item.category === 'default' ? '系统推荐' : '用户自定义' }}</td>
                    <td>{{ formatDate(item.created_at || new Date()) }}</td>
                    <td class="actions">
                      <button v-if="item.category === 'default'" class="copy" @click="handleCopy(item)">复制</button>
                      <button v-if="item.category === 'default'" class="edit" @click="handleEdit(item, true)">查看</button>
                      <button v-else class="edit" @click="handleEdit(item)">编辑</button>
                      <button v-if="item.category === 'custom'" class="delete" @click="handleDelete(item.id)">删除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加/编辑模板模态框 -->
    <div v-if="showAddModal || showEditModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content large">
        <div class="modal-header">
          <h3>{{ showEditModal ? '编辑模板' : '添加模板' }}</h3>
          <button class="close-btn" @click="closeModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>模板名称</label>              <input type="text" v-model="formData.name" placeholder="请输入模板名称" :disabled="isViewMode" />
            </div>
            <div class="form-group">
              <label>分类</label>
              <select v-model="formData.category" class="form-select" :disabled="showEditModal || isViewMode">
                <option value="summary">纪要</option>
                <option value="abstract">摘要</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group half-width">
              <label>系统提示词</label>
              <textarea v-model="formData.system_prompt" rows="20" placeholder="请输入系统提示词" :disabled="isViewMode"></textarea>
            </div>
            <div class="form-group half-width">
              <label>用户提示词</label>
              <textarea v-model="formData.user_prompt" rows="20" placeholder="请输入用户提示词" :disabled="isViewMode"></textarea>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button v-if="!formData.id && !isViewMode" class="paste-btn" @click="handlePasteTemplate" :disabled="isViewMode">一键粘贴</button>
          <button class="cancel-btn" @click="closeModal">取消</button>
          <button v-if="!isViewMode" class="confirm-btn" @click="handleSaveTemplate" :disabled="saveLoading">
            {{ saveLoading ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue';
import { promptApi } from '../api/promptApi';

export default {
  name: 'TemplateView',
  setup() {
    const viewMode = ref(localStorage.getItem('template_view_mode') || 'grid');
    const activeTab = ref('all');
    const templates = ref([]);
    const loading = ref(false);
    const showAddModal = ref(false);
    const showEditModal = ref(false);
    const saveLoading = ref(false);
    const formData = ref({
      id: null,
      name: '',
      category: 'summary',
      system_prompt: '',
      user_prompt: ''
    });

    const searchKeyword = ref('');

    const tabs = [
      { key: 'all', label: '全部' },
      { key: 'summary', label: '纪要' },
      { key: 'abstract', label: '摘要' }
    ];

    // 根据tab和关键词筛选模板
    const filteredTemplates = computed(() => {
      let filtered = templates.value;
      
      // 按标签筛选
      if (activeTab.value === 'summary') {
        filtered = filtered.filter(t => 
          t.template_type === 'summary'
        );
      } else if (activeTab.value === 'abstract') {
        filtered = filtered.filter(t => 
          t.template_type === 'abstract'
        );
      }
      
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

    // 所有模板（用于显示）
    const allTemplates = computed(() => filteredTemplates.value);

    // 纪要模板
    const summaryTemplates = computed(() => {
      return filteredTemplates.value.filter(t => 
        t.template_type === 'summary'
      );
    });

    // 摘要模板
    const abstractTemplates = computed(() => {
      return filteredTemplates.value.filter(t => 
        t.template_type === 'abstract'
      );
    });

    // 是否有纪要模板
    const hasSummaryTemplates = computed(() => summaryTemplates.value.length > 0);

    // 是否有摘要模板
    const hasAbstractTemplates = computed(() => abstractTemplates.value.length > 0);

    const loadTemplates = async () => {
      loading.value = true;
      try {
        const response = await promptApi.getList();
        console.log('模板列表响应:', response);
        
        // 支持多种响应格式
        if (response.prompts && Array.isArray(response.prompts)) {
          templates.value = response.prompts;
        } else if (response.data?.prompts && Array.isArray(response.data.prompts)) {
          templates.value = response.data.prompts;
        } else if (Array.isArray(response.data)) {
          templates.value = response.data;
        } else if (Array.isArray(response)) {
          templates.value = response;
        }
      } catch (error) {
        console.error('加载模板列表失败:', error);
      } finally {
        loading.value = false;
      }
    };

    const isViewMode = ref(false);

    const handleEdit = (item, viewOnly = false) => {
      formData.value = {
        id: item.id,
        name: item.name || '',
        category: item.template_type || 'summary',
        system_prompt: item.system_prompt || '',
        user_prompt: item.user_prompt || ''
      };
      isViewMode.value = viewOnly;
      showEditModal.value = true;
    };

    const handleSaveTemplate = async () => {
      if (!formData.value.name) {
        alert('请输入模板名称');
        return;
      }
      saveLoading.value = true;
      try {
        if (showEditModal.value) {
          await promptApi.update(formData.value.id, formData.value);
        } else {
          // 对于添加模板，需要将category作为template_type传递
          const addData = {
            name: formData.value.name,
            template_type: formData.value.category,
            system_prompt: formData.value.system_prompt,
            user_prompt: formData.value.user_prompt
          };
          await promptApi.add(addData);
        }
        await loadTemplates();
        closeModal();
      } catch (error) {
        console.error('保存模板失败:', error);
        alert('保存模板失败');
      } finally {
        saveLoading.value = false;
      }
    };

    const showToast = (message, type = 'success') => {
      const toast = document.createElement('div');
      toast.className = `toast toast-${type}`;
      toast.textContent = message;
      document.body.appendChild(toast);
      
      // 显示动画
      setTimeout(() => {
        toast.classList.add('show');
      }, 10);
      
      // 自动消失
      setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
          document.body.removeChild(toast);
        }, 300);
      }, 2000);
    };

    const handleCopy = async (item) => {
      try {
        const response = await promptApi.copy(item.id);
        
        // 将模板内容复制到剪贴板
        const templateData = {
          name: response.name,
          category: response.category || '',
          system_prompt: response.system_prompt,
          user_prompt: response.user_prompt
        };
        
        // 复制到剪贴板
        await navigator.clipboard.writeText(JSON.stringify(templateData));
        
        // 提示复制成功
        showToast('模板内容已复制到剪贴板');
        
        await loadTemplates();
      } catch (error) {
        console.error('复制模板失败:', error);
        showToast('复制模板失败', 'error');
      }
    };

    const handleDelete = async (templateId) => {
      if (!confirm('确定要删除这个模板吗？')) {
        return;
      }
      try {
        await promptApi.delete(templateId);
        await loadTemplates();
      } catch (error) {
        console.error('删除模板失败:', error);
        alert('删除模板失败');
      }
    };

    const closeModal = () => {
      showAddModal.value = false;
      showEditModal.value = false;
      isViewMode.value = false;
      formData.value = {
        id: null,
        name: '',
        category: 'summary',
        system_prompt: '',
        user_prompt: ''
      };
    };

    const handlePasteTemplate = async () => {
      try {
        // 从剪贴板读取内容
        const clipboardText = await navigator.clipboard.readText();
        
        // 解析模板数据
        const templateData = JSON.parse(clipboardText);
        
        // 填充表单
        formData.value = {
          id: null,
          name: templateData.name || '',
          category: templateData.category || '',
          system_prompt: templateData.system_prompt || '',
          user_prompt: templateData.user_prompt || ''
        };
        
        // 提示粘贴成功
        showToast('模板内容已粘贴');
      } catch (error) {
        console.error('粘贴模板失败:', error);
        showToast('粘贴模板失败，请确保剪贴板中有正确的模板内容', 'error');
      }
    };

    const getTypeLabel = (category) => {
      if (category === 'default') return '默认推荐';
      if (category === 'custom') return '用户自定义';
      return category || '未知';
    };

    const getCategoryIcon = (template_type) => {
      if (template_type === 'summary') return '📝';
      if (template_type === 'abstract') return '📄';
      return '📄';
    };

    const formatDate = (dateStr) => {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return date.toLocaleString('zh-CN');
    };

    // 监听视图模式变化，保存到localStorage
    watch(viewMode, (newMode) => {
      localStorage.setItem('template_view_mode', newMode);
    });

    onMounted(() => {
      loadTemplates();
    });

    return {
      viewMode, activeTab, templates, filteredTemplates, allTemplates,
      summaryTemplates, abstractTemplates,
      hasSummaryTemplates, hasAbstractTemplates,
      loading, showAddModal, showEditModal, saveLoading, isViewMode,
      formData, tabs, loadTemplates, searchKeyword, handleSearch,
      handleEdit, handleSaveTemplate, handleCopy, handleDelete, closeModal, handlePasteTemplate,
      getTypeLabel, getCategoryIcon, formatDate
    };
  }
};
</script>

<style scoped>
.template-container {
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

.loading, .empty {
  text-align: center;
  padding: 48px;
  color: #999;
}

.template-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.templates-wrapper {
  background: white;
  border-radius: 12px;
  padding: 20px;
}

.divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, #ddd, transparent);
  margin: 24px 0;
}

.grid-view {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 24px;
}

.grid-item {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.2s;
}

.grid-item:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  transform: translateY(-2px);
}

.item-preview {
  height: 140px;
  background: #eef2ff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-icon {
  font-size: 56px;
}

.item-info {
  padding: 16px;
}

.item-name {
  font-size: 15px;
  color: #333;
  margin-bottom: 8px;
  font-weight: 500;
}

.item-description {
  font-size: 13px;
  color: #999;
  margin-top: 8px;
}

.type-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.type-tag.default {
  background: #e6f7ff;
  color: #409eff;
}

.type-tag.custom {
  background: #f0f9ff;
  color: #52c41a;
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

.item-actions button.copy {
  border-color: #67c23a;
  color: #67c23a;
}

.item-actions button.copy:hover {
  background: #f0f9ff;
  border-color: #85ce61;
  color: #67c23a;
}

.item-actions button.edit {
  border-color: #409eff;
  color: #409eff;
}

.item-actions button.edit:hover {
  background: #ecf5ff;
  border-color: #66b1ff;
  color: #409eff;
}

.item-actions button.delete {
  border-color: #f56c6c;
  color: #f56c6c;
}

.item-actions button.delete:hover {
  background: #fef0f0;
  border-color: #f78989;
  color: #f56c6c;
}

.list-view table {
  width: 100%;
  border-collapse: collapse;
  background: #f8f9fa;
  border-radius: 12px;
  overflow: hidden;
}

.list-view th, .list-view td {
  padding: 16px;
  text-align: left;
  border-bottom: 1px solid #e9ecef;
}

.list-view th {
  background: #eef2ff;
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

.list-view .actions button.copy {
  border-color: #67c23a;
  color: #67c23a;
}

.list-view .actions button.copy:hover {
  background: #f0f9ff;
  border-color: #85ce61;
  color: #67c23a;
}

.list-view .actions button.edit {
  border-color: #409eff;
  color: #409eff;
}

.list-view .actions button.edit:hover {
  background: #ecf5ff;
  border-color: #66b1ff;
  color: #409eff;
}

.list-view .actions button.delete {
  border-color: #f56c6c;
  color: #f56c6c;
}

.list-view .actions button.delete:hover {
  background: #fef0f0;
  border-color: #f78989;
  color: #f56c6c;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
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

.modal-content.large {
  width: 800px;
  max-width: 95%;
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
  padding: 32px 24px;
  min-height: 500px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 0;
}

.form-group.half-width {
  width: 100%;
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
}

.form-group input, .form-group textarea, .form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  box-sizing: border-box;
}

.form-group select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='6' viewBox='0 0 12 6'%3E%3Cpath fill='%23999' d='M0 0l6 6 6-6z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 12px 6px;
  cursor: pointer;
}

.form-group textarea {
  resize: vertical;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #eee;
}

.cancel-btn, .confirm-btn, .paste-btn {
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

.paste-btn {
  background: #67c23a;
  color: white;
  margin-right: auto;
}

.confirm-btn:hover {
  background: #66b1ff;
}

.paste-btn:hover {
  background: #85ce61;
}

/* Toast 样式 */
:global(.toast) {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translate(-50%, -20px);
  padding: 12px 20px;
  border-radius: 6px;
  color: white;
  font-size: 14px;
  font-weight: 500;
  z-index: 9999;
  opacity: 0;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  text-align: center;
  min-width: 200px;
  max-width: 80%;
}

:global(.toast.show) {
  opacity: 1;
  transform: translate(-50%, 0);
}

:global(.toast-success) {
  background: #67c23a;
}

:global(.toast-error) {
  background: #f56c6c;
}

:global(.toast-info) {
  background: #409eff;
}
</style>