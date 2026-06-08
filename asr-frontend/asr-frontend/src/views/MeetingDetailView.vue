<!--
 * @Description: 会议详情组件
 * 包含会议纪要、摘要、时间轴、逐字稿、智能问答等功能
 * 支持音频/视频播放、字幕显示、全屏等功能
 * @Author: Trae AI
 * @Date: 2026
-->
<template>
  <div class="meeting-detail-container">
    <!-- 标题栏 -->
    <div class="detail-header">
      <div class="header-left">
        <button class="back-btn" @click="goBack">
          <span class="icon">←</span>
          返回
        </button>
        <h2>{{ file.name }}</h2>
        <div class="file-info">
          <span>{{ formatDate(file.created_at) }}</span>
        </div>
      </div>
    </div>

    <!-- 主体内容 -->
    <div class="detail-content">
      <!-- 左侧内容区域 -->
      <div class="left-panel">
        <!-- 标签页 -->
        <div class="tabs">
          <button 
            class="tab-btn" 
            :class="{ active: activeTab === 'summary' }"
            @click="activeTab = 'summary'"
          >
            纪要
          </button>
          <button 
            class="tab-btn" 
            :class="{ active: activeTab === 'abstract' }"
            @click="activeTab = 'abstract'"
          >
            摘要
          </button>
          <button 
            class="tab-btn" 
            :class="{ active: activeTab === 'timeline' }"
            @click="activeTab = 'timeline'"
          >
            时间轴
          </button>
          <button 
            class="tab-btn" 
            :class="{ active: activeTab === 'transcript' }"
            @click="activeTab = 'transcript'"
          >
            逐字稿
          </button>
          <button 
            class="tab-btn" 
            :class="{ active: activeTab === 'chat' }"
            @click="activeTab = 'chat'"
          >
            智能问答
          </button>
        </div>

        <!-- 内容区域 -->
        <div 
          ref="contentPanelRef"
          class="content-panel"
          @mousedown="updateUserActivity"
          @mouseup="updateUserActivity"
          @click="updateUserActivity"
          @scroll="updateUserActivity"
          @wheel="updateUserActivity"
        >
          <!-- 会议纪要 -->
          <div v-if="activeTab === 'summary'" class="summary-content">
            <div class="content-header">
              <div class="content-tag">
                <span class="icon">📋</span>
                <span>智能总结</span>
              </div>
              <div class="header-actions">
                <div class="template-selector" v-if="!isEditingSummary">
                  <button class="template-btn" @click="showTemplateModal = true">
                    <span class="icon">📄</span>
                    更换模板
                  </button>
                </div>
                <button class="export-btn" @click="exportSummaryToWord">
                  <span class="icon">📥</span>
                  导出Word
                </button>
                <button class="edit-btn" @click="editSummary" v-if="!isEditingSummary">
                  <span class="icon">✏️</span>
                  编辑
                </button>
                <div class="edit-actions" v-else>
                  <button class="save-btn" @click="saveSummary">保存</button>
                  <button class="cancel-btn" @click="cancelEditSummary">取消</button>
                </div>
              </div>
            </div>
            
            <div v-if="loadingSummary" class="loading">加载中...</div>
            <div v-else-if="summaryError" class="error">{{ summaryError }}</div>
            <div v-else class="summary-text">
              <div v-if="isEditingSummary">
                <textarea 
                  v-model="summaryEditText" 
                  class="edit-textarea"
                  placeholder="请输入会议纪要..."
                ></textarea>
              </div>
              <div v-else v-html="summaryHtml" class="formatted-content markdown-body"></div>
              <div v-if="!summaryData.meeting_summary && !isEditingSummary" class="empty-state">
                <p>暂无会议纪要</p>
                <button class="generate-btn" @click="showTemplateModal = true">生成会议纪要</button>
              </div>
            </div>
          </div>

          <!-- 会议摘要 -->
          <div v-if="activeTab === 'abstract'" class="abstract-content">
            <div class="content-header">
              <div class="content-tag">
                <span class="icon">📝</span>
                <span>会议摘要</span>
              </div>
              <div class="header-actions">
                <div class="template-selector" v-if="!isEditingAbstract">
                  <button class="template-btn" @click="showAbstractTemplateModal = true">
                    <span class="icon">📄</span>
                    更换模板
                  </button>
                </div>
                <button class="export-btn" @click="exportAbstractToWord">
                  <span class="icon">📥</span>
                  导出Word
                </button>
                <button class="edit-btn" @click="editAbstract" v-if="!isEditingAbstract">
                  <span class="icon">✏️</span>
                  编辑
                </button>
                <div class="edit-actions" v-else>
                  <button class="save-btn" @click="saveAbstract">保存</button>
                  <button class="cancel-btn" @click="cancelEditAbstract">取消</button>
                </div>
              </div>
            </div>
            
            <div v-if="loadingAbstract" class="loading">加载中...</div>
            <div v-else-if="abstractError" class="error">{{ abstractError }}</div>
            <div v-else class="abstract-text">
              <div v-if="isEditingAbstract">
                <textarea 
                  v-model="abstractEditText" 
                  class="edit-textarea"
                  placeholder="请输入会议摘要..."
                ></textarea>
              </div>
              <div v-else v-html="abstractHtml" class="formatted-content markdown-body"></div>
              <div v-if="!abstractData.meeting_abstract && !isEditingAbstract" class="empty-state">
                <p>暂无会议摘要</p>
                <button class="generate-btn" @click="showAbstractTemplateModal = true">生成会议摘要</button>
              </div>
            </div>
          </div>

          <!-- 时间轴 -->
          <div v-if="activeTab === 'timeline'" class="timeline-content">
            <div class="content-header">
              <div class="content-tag">
                <span class="icon">⏱️</span>
                <span>时间轴分段</span>
              </div>
              <div class="header-actions">
                <button class="export-btn" @click="exportTimelineToWord">
                  <span class="icon">📥</span>
                  导出Word
                </button>
                <button class="regenerate-btn" @click="regenerateSegments">
                  <span class="icon">🔄</span>
                  重新生成
                </button>
                <button class="refresh-btn" @click="loadSegments">
                  <span class="icon">🔄</span>
                  刷新
                </button>
              </div>
            </div>
            
            <div v-if="loadingSegments" class="loading">加载中...</div>
            <div v-else-if="segmentsError" class="error">{{ segmentsError }}</div>
            <div v-else class="segments-list">
              <div v-if="segmentsData.segments?.length === 0" class="empty-state">
                <p>暂无分段数据</p>
                <button class="generate-btn" @click="generateSegments">生成分段</button>
              </div>
              <div 
                v-for="segment in segmentsData.segments" 
                :key="segment.id" 
                class="segment-item"
                :class="{ 
                  editing: editingSegmentId === segment.id,
                  highlighted: highlightedSegmentIndex === segment.id 
                }"
                @click="handleSegmentClick(segment, $event)"
              >
                <div class="segment-time">
                  <span>{{ formatTime(segment.start_time) }} - {{ formatTime(segment.end_time) }}</span>
                </div>
                <div class="segment-content">
                  <div v-if="editingSegmentId === segment.id">
                    <input 
                      v-model="editingSegmentTitle" 
                      class="segment-title-input"
                      placeholder="分段标题"
                      @keyup.esc="cancelSegmentEdit"
                      @keyup.enter.prevent="saveSegmentEdit(segment.id)"
                    />
                    <textarea 
                      v-model="editingSegmentSummary" 
                      class="segment-summary-textarea"
                      placeholder="分段摘要"
                      @keyup.esc="cancelSegmentEdit"
                    ></textarea>
                    <div class="edit-buttons">
                      <button class="text-save-btn" @click.stop="saveSegmentEdit(segment.id)">保存</button>
                      <button class="text-cancel-btn" @click.stop="cancelSegmentEdit">取消</button>
                    </div>
                  </div>
                  <div v-else class="segment-display-wrapper" @click.stop>
                    <div 
                      class="segment-display"
                      @click.stop="startSegmentEdit(segment)"
                      :title="'点击编辑'"
                    >
                      <h4 class="segment-title">{{ segment.title || '未命名分段' }}</h4>
                      <p class="segment-summary">{{ segment.summary || '暂无总结' }}</p>
                    </div>
                    <button 
                      class="segment-edit-btn"
                      @click.stop="startSegmentEdit(segment)"
                      title="编辑分段"
                    >
                      ✏️
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 逐字稿 -->
          <div v-if="activeTab === 'transcript'" class="transcript-content">
            <div class="content-header">
              <div class="content-tag">
                <span class="icon">📄</span>
                <span>逐字稿</span>
              </div>
              <div class="header-actions">
                <button class="export-btn" @click="exportTranscriptToWord">
                  <span class="icon">📥</span>
                  导出Word
                </button>
                <button class="regenerate-btn" @click="regenerateTranscription">
                  <span class="icon">🔄</span>
                  重新生成
                </button>
                <button class="refresh-btn" @click="loadTranscription">
                  <span class="icon">🔄</span>
                  刷新
                </button>
              </div>
            </div>
            
            <!-- 搜索功能 -->
            <div class="search-container">
              <div class="search-input-wrapper">
                <div class="search-input-container">
                  <input 
                    v-model="searchKeyword" 
                    class="search-input" 
                    placeholder="搜索逐字稿内容..."
                    @keyup.enter="handleSearchOrNavigate"
                  />
                  <div v-if="searchResults.length > 0" class="search-counter">
                    {{ currentSearchIndex + 1 }}/{{ searchResults.length }}
                  </div>
                </div>
                <button class="search-btn" @click="handleSearch">
                  🔍
                </button>
              </div>
            </div>
            
            <div v-if="loadingTranscription" class="loading">加载中...</div>
            <div v-else-if="transcriptionError" class="error">{{ transcriptionError }}</div>
            <div v-else class="transcript-list">
              <div v-if="unifiedTranscription.length === 0" class="empty-state">
                <p>暂无逐字稿数据</p>
                <button class="generate-btn" @click="generateTranscription">生成逐字稿</button>
              </div>
              <div 
                v-for="(item, index) in unifiedTranscription" 
                :key="index" 
                class="transcript-item"
                :class="{ 
                  editing: editingIndex === index,
                  highlighted: highlightedTranscriptIndex === index,
                  'search-highlight': isCurrentSearchResult(item)
                }"
                @click="jumpToTranscript(item, index)"
              >
                <!-- 发言人头像 -->
                <div class="transcript-avatar" v-if="editingIndex !== index">
                  <img v-if="item.avatar_url" :src="API_BASE_URL + item.avatar_url" class="transcript-avatar-img" alt="头像" />
                  <div v-else class="transcript-avatar-default">👤</div>
                </div>
                <div class="transcript-content-area">
                  <div class="transcript-header">
                    <div class="speaker-info">
                      <span 
                        class="speaker-name"
                        @click.stop="editingIndex !== index && startEditSpeaker(index, item)"
                        :class="{ 'clickable': editingIndex !== index }"
                        :title="editingIndex !== index ? '点击编辑说话人' : ''"
                      >{{ item.speaker || '未知说话人' }}</span>
                      <span class="transcript-time">{{ formatTime(item.start_time) }}</span>
                    </div>
                  </div>
                  <div class="transcript-text">
                    <div v-if="editingIndex === index">
                      <input 
                        v-model="editingSpeaker" 
                        class="speaker-input"
                        placeholder="说话人名称"
                        @keyup.enter="saveTextEdit(index)"
                      />
                      <textarea 
                        v-model="editingText" 
                        class="text-editarea"
                        placeholder="文本内容"
                        @keyup.enter="!event.shiftKey && saveTextEdit(index)"
                      ></textarea>
                      <div class="edit-buttons">
                        <button class="text-save-btn" @click="saveTextEdit(index)">保存</button>
                        <button class="text-cancel-btn" @click="cancelTextEdit">取消</button>
                      </div>
                    </div>
                    <div 
                      v-else
                      class="transcript-text-content"
                      @click.stop="startEditText(index, item)"
                      :title="'点击编辑文本'"
                    >
                      <span v-if="!isCurrentSearchResult(item)">{{ item.text }}</span>
                      <span v-else v-html="getMatchedText(item)"></span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 智能问答 -->
          <div v-if="activeTab === 'chat'" class="chat-content">
            <MeetingChatPanel 
              :file-id="fileId" 
              :user-id="userId"
            />
          </div>
        </div>
      </div>

      <!-- 右侧内容区域 -->
      <div class="right-panel">
        <!-- 视频/音频播放器 -->
        <div class="player-container" ref="playerContainerRef" :class="{ 'audio-container': !isVideoFile, 'is-fullscreen': isFullScreen }">
          <video 
            v-if="isVideoFile"
            ref="mediaPlayerRef"
            class="media-player"
            controls
            controlslist="nofullscreen"
            :src="fileUrl"
            @loadedmetadata="handleLoadedMetadata"
            @error="console.error('❌ [视频加载失败]', $event)"
          >
            您的浏览器不支持视频播放
          </video>
          <audio 
            v-else
            ref="mediaPlayerRef"
            class="media-player audio-only"
            controls
            :src="fileUrl"
            @loadedmetadata="handleLoadedMetadata"
            @error="console.error('❌ [音频加载失败]', $event)"
          >
            您的浏览器不支持音频播放
          </audio>
          
          <!-- 自定义全屏按钮（仅视频显示） -->
          <button v-if="isVideoFile" class="custom-fullscreen-btn" @click="toggleFullScreen" title="全屏">
            <span v-if="isFullScreen">✕</span>
            <span v-else>⛶</span>
          </button>
          
          <!-- 字幕显示区域（仅视频显示） -->
          <div v-if="isVideoFile && currentSubtitle" class="subtitle-container" :class="{ 'subtitle-fullscreen': isFullScreen }">
            <div class="subtitle-avatar">
              <img v-if="currentSubtitle.avatar_url" :src="API_BASE_URL + currentSubtitle.avatar_url" class="subtitle-avatar-img" alt="头像" />
              <div v-else class="subtitle-avatar-default">👤</div>
            </div>
            <div class="subtitle-content">
              <div class="subtitle-speaker">{{ currentSubtitle.speaker || '未知说话人' }}</div>
              <div class="subtitle-text">{{ currentSubtitle.text }}</div>
            </div>
          </div>
        </div>

        <!-- 会议统计 -->
        <div class="stats-container">
          <h3>会议统计</h3>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-label">总时长</span>
              <span class="stat-value">{{ totalDuration }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">说话人数</span>
              <span class="stat-value">{{ speakerCount }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">总句数</span>
              <span class="stat-value">{{ totalSentences }}</span>
            </div>
          </div>
        </div>

        <!-- 会议类型 -->
        <div class="meeting-type-container" v-if="file.meeting_type">
          <h3>会议类型</h3>
          <div class="meeting-type-tag">
            {{ file.meeting_type }}
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 模板选择模态框 -->
  <div v-if="showTemplateModal" class="modal-overlay" @click.self="showTemplateModal = false">
    <div class="modal-content">
      <div class="modal-header">
        <h3>选择模板</h3>
        <button class="close-btn" @click="showTemplateModal = false">×</button>
      </div>
      <div class="modal-body">
        <div v-if="loadingTemplates" class="loading">加载模板中...</div>
        <div v-else-if="templatesError" class="error">{{ templatesError }}</div>
        <div v-else class="templates-list">
          <div 
            v-for="template in templates" 
            :key="template.id"
            class="template-item"
            :class="{ selected: selectedTemplateId === template.id }"
            @click="selectedTemplateId = template.id"
          >
            <div class="template-info">
              <h4>{{ template.name }}</h4>
              <div class="template-actions">
                <a href="javascript:void(0)" class="view-details-link" @click.stop="showTemplateDetails(template)">
                  {{ template.description ? '查看详情' : '查看详情' }}
                </a>
              </div>
            </div>
            <div class="template-select">
              <input 
                type="radio" 
                :name="'template'" 
                :value="template.id"
                v-model="selectedTemplateId"
              />
            </div>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="cancel-btn" @click="showTemplateModal = false">取消</button>
        <button class="confirm-btn" @click="confirmTemplateChange" :disabled="!selectedTemplateId">
          确认更换
        </button>
      </div>
    </div>
  </div>

  <!-- 确认覆盖弹窗 -->
  <div v-if="showConfirmModal" class="modal-overlay" @click.self="showConfirmModal = false">
    <div class="modal-content confirm-modal">
      <div class="modal-body">
        <div class="confirm-icon">⚠️</div>
        <h3>确认更换模板</h3>
        <p>更换模板后，原有的会议纪要内容将会被覆盖。</p>
        <p>确定要继续吗？</p>
      </div>
      <div class="modal-footer">
        <button class="cancel-btn" @click="showConfirmModal = false">取消</button>
        <button class="confirm-btn danger" @click="handleConfirmChange">确认更换</button>
      </div>
    </div>
  </div>

   <!-- 加载弹窗 -->
  <div v-if="showLoadingModal" class="modal-overlay loading-overlay" @click.self="false">
    <div class="modal-content loading-modal">
      <div class="loading-spinner"></div>
      <p>正在处理中，请稍候...</p>
    </div>
  </div>

  <!-- 结果提示弹窗 -->
  <div v-if="showResultModal" class="modal-overlay" @click.self="showResultModal = false">
    <div class="modal-content result-modal">
      <div class="result-icon" :class="resultType">{{ resultType === 'success' ? '✓' : '✗' }}</div>
      <h3>{{ resultType === 'success' ? '操作成功' : '操作失败' }}</h3>
      <p>{{ resultMessage }}</p>
      <div class="modal-footer">
        <button class="confirm-btn" @click="handleResultConfirm">确定</button>
      </div>
    </div>
  </div>

  <!-- 摘要模板选择模态框 -->
  <div v-if="showAbstractTemplateModal" class="modal-overlay" @click.self="showAbstractTemplateModal = false">
    <div class="modal-content">
      <div class="modal-header">
        <h3>选择摘要模板</h3>
        <button class="close-btn" @click="showAbstractTemplateModal = false">×</button>
      </div>
      <div class="modal-body">
        <div v-if="loadingAbstractTemplates" class="loading">加载模板中...</div>
        <div v-else-if="abstractTemplatesError" class="error">{{ abstractTemplatesError }}</div>
        <div v-else class="templates-list">
          <div 
            v-for="template in abstractTemplates" 
            :key="template.id"
            class="template-item"
            :class="{ selected: selectedAbstractTemplateId === template.id }"
            @click="selectedAbstractTemplateId = template.id"
          >
            <div class="template-info">
              <h4>{{ template.name }}</h4>
              <div class="template-actions">
                <a href="javascript:void(0)" class="view-details-link" @click.stop="showAbstractTemplateDetails(template)">
                  查看详情
                </a>
              </div>
            </div>
            <div class="template-select">
              <input 
                type="radio" 
                :name="'abstract-template'"
                :value="template.id"
                v-model="selectedAbstractTemplateId"
              />
            </div>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="cancel-btn" @click="showAbstractTemplateModal = false">取消</button>
        <button class="confirm-btn" @click="confirmAbstractTemplateChange" :disabled="!selectedAbstractTemplateId">
          确认更换
        </button>
      </div>
    </div>
  </div>

  <!-- 摘要确认覆盖弹窗 -->
  <div v-if="showAbstractConfirmModal" class="modal-overlay" @click.self="showAbstractConfirmModal = false">
    <div class="modal-content confirm-modal">
      <div class="modal-body">
        <div class="confirm-icon">⚠️</div>
        <h3>确认更换模板</h3>
        <p>更换模板后，原有的会议摘要内容将会被覆盖。</p>
        <p>确定要继续吗？</p>
      </div>
      <div class="modal-footer">
        <button class="cancel-btn" @click="showAbstractConfirmModal = false">取消</button>
        <button class="confirm-btn danger" @click="handleAbstractConfirmChange">确认更换</button>
      </div>
    </div>
  </div>

  <!-- 重新生成逐字稿确认弹窗 -->
  <div v-if="showRegenerateTranscriptConfirm" class="modal-overlay" @click.self="showRegenerateTranscriptConfirm = false">
    <div class="modal-content confirm-modal">
      <div class="modal-body">
        <div class="confirm-icon">⚠️</div>
        <h3>确认重新生成</h3>
        <p>重新生成后，原有的逐字稿内容将会被覆盖。</p>
        <p>确定要继续吗？</p>
      </div>
      <div class="modal-footer">
        <button class="cancel-btn" @click="showRegenerateTranscriptConfirm = false">取消</button>
        <button class="confirm-btn danger" @click="handleRegenerateTranscriptConfirm">确认生成</button>
      </div>
    </div>
  </div>

  <!-- 重新生成分段确认弹窗 -->
  <div v-if="showRegenerateSegmentsConfirm" class="modal-overlay" @click.self="showRegenerateSegmentsConfirm = false">
    <div class="modal-content confirm-modal">
      <div class="modal-body">
        <div class="confirm-icon">⚠️</div>
        <h3>确认重新生成</h3>
        <p>重新生成后，原有的时间轴分段内容将会被覆盖。</p>
        <p>确定要继续吗？</p>
      </div>
      <div class="modal-footer">
        <button class="cancel-btn" @click="showRegenerateSegmentsConfirm = false">取消</button>
        <button class="confirm-btn danger" @click="handleRegenerateSegmentsConfirm">确认生成</button>
      </div>
    </div>
  </div>

  <!-- 模板详情弹窗 -->
  <div v-if="showTemplateDetailsModal" class="modal-overlay" @click.self="showTemplateDetailsModal = false">
    <div class="modal-content template-details-modal">
      <div class="modal-header">
        <h3>模板详情</h3>
        <button class="close-btn" @click="showTemplateDetailsModal = false">×</button>
      </div>
      <div class="modal-body">
        <div v-if="loadingTemplateDetails" class="loading">加载中...</div>
        <div v-else-if="templateDetailsError" class="error">{{ templateDetailsError }}</div>
        <div v-else-if="currentTemplate" class="template-details-content">
          <!-- 模板名称和分类 -->
          <div class="detail-row">
            <div class="detail-col">
              <label>模板名称</label>
              <div class="readonly-input">{{ currentTemplate.name }}</div>
            </div>
            <div class="detail-col">
              <label>分类</label>
              <div class="readonly-input">{{ currentTemplate.category || '无' }}</div>
            </div>
          </div>
          
          <!-- 系统提示词和用户提示词 -->
          <div class="detail-row">
            <div class="detail-col">
              <label>系统提示词</label>
              <div class="readonly-textarea">{{ currentTemplate.system_prompt || '无' }}</div>
            </div>
            <div class="detail-col">
              <label>用户提示词</label>
              <div class="readonly-textarea">{{ currentTemplate.user_prompt || '无' }}</div>
            </div>
          </div>
          
          <!-- 类型 -->
          <div class="detail-row">
            <div class="detail-col full-width">
              <label>类型</label>
              <div class="readonly-input">{{ currentTemplate.template_type === 'summary' ? '纪要' : '摘要' }}</div>
            </div>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="confirm-btn" @click="showTemplateDetailsModal = false">关闭</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { meetingApi } from '../api/meetingApi';
import { fileApi } from '../api/fileApi';
import { promptApi } from '../api/promptApi';
import { ragApi } from '../api/ragApi';
import { exportApi } from '../api/exportApi';
import MeetingChatPanel from './meeting-detail/MeetingChatPanel.vue';
import { marked } from 'marked';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default {
  name: 'MeetingDetailView',
  components: {
    MeetingChatPanel
  },
  setup() {
    const router = useRouter();
    const route = useRoute();

    // 文件信息
    const file = ref({});

    // 聊天面板需要的ID
    const fileId = computed(() => {
      const id = file.value.id;
      console.log('📄 MeetingDetailView - fileId:', id, 'type:', typeof id);
      if (!id) return null;
      const numId = Number(id);
      return isNaN(numId) ? null : numId;
    });
    const userId = computed(() => {
      // 尝试从 localStorage 获取用户ID
      const userInfo = localStorage.getItem('userInfo');
      if (userInfo) {
        try {
          const user = JSON.parse(userInfo);
          const id = user.id;
          console.log('👤 MeetingDetailView - userId:', id, 'type:', typeof id);
          if (!id) return null;
          const numId = Number(id);
          return isNaN(numId) ? null : numId;
        } catch (e) {
          return null;
        }
      }
      return null;
    });

    // 标签页状态
    const activeTab = ref('summary');

    // 加载状态
    const loadingSummary = ref(false);
    const loadingAbstract = ref(false);
    const loadingSegments = ref(false);
    const loadingTranscription = ref(false);

    // 错误状态
    const summaryError = ref('');
    const abstractError = ref('');
    const segmentsError = ref('');
    const transcriptionError = ref('');

    // 数据状态
    const summaryData = ref({ meeting_summary: '' });
    const abstractData = ref({ meeting_abstract: '' });
    const segmentsData = ref({ segments: [] });
    const transcriptionData = ref({ segments: [], speaker_info: [] });
    
    // 计算属性：获取统一的逐字稿数据（优先新字段，兼容旧字段）
    const unifiedTranscription = computed(() => {
      // 强制依赖触发更新
      forceStatsUpdate.value;
      
      if (transcriptionData.value.segments?.length > 0) {
        return transcriptionData.value.segments;
      } else if (transcriptionData.value.speaker_info?.length > 0) {
        return transcriptionData.value.speaker_info;
      }
      return [];
    });

    // 编辑状态
    const isEditingSummary = ref(false);
    const isEditingAbstract = ref(false);
    const summaryEditText = ref('');
    const abstractEditText = ref('');

    // 模板相关状态
    const showTemplateModal = ref(false);
    const showConfirmModal = ref(false);
    const showTemplateDetailsModal = ref(false);
    const showLoadingModal = ref(false);
    const showResultModal = ref(false);
    const resultMessage = ref('');
    const resultType = ref('success'); // success, error
    const templates = ref([]);
    const loadingTemplates = ref(false);
    const loadingTemplateDetails = ref(false);
    const templatesError = ref('');
    const templateDetailsError = ref('');
    const selectedTemplateId = ref('');
    const currentTemplate = ref(null);
    
    // 摘要模板相关状态
    const showAbstractTemplateModal = ref(false);
    const showAbstractConfirmModal = ref(false);
    const abstractTemplates = ref([]);
    const loadingAbstractTemplates = ref(false);
    const abstractTemplatesError = ref('');
    const selectedAbstractTemplateId = ref('');
    const currentAbstractTemplate = ref(null);
    // 跟踪当前正在更换的模板类型
    const currentTemplateType = ref(''); // 'summary' 或 'abstract'
    
    // 逐字稿重新生成确认状态
    const showRegenerateTranscriptConfirm = ref(false);
    // 时间轴重新生成确认状态
    const showRegenerateSegmentsConfirm = ref(false);
    // 搜索相关状态
    const searchKeyword = ref('');
    const searchResults = ref([]);
    const currentSearchIndex = ref(0);
    const loadingSearch = ref(false);

    // 逐字稿编辑状态
    const editingIndex = ref(-1);
    const editingSpeaker = ref('');
    const editingText = ref('');
    
    // 时间轴编辑状态
    const editingSegmentId = ref(-1);
    const editingSegmentTitle = ref('');
    const editingSegmentSummary = ref('');
    
    // 媒体播放器相关
    const mediaPlayerRef = ref(null);
    const currentPlayingIndex = ref(-1);
    const highlightedSegmentIndex = ref(-1);
    const highlightedTranscriptIndex = ref(-1);
    
    // 当前字幕
    const currentSubtitle = ref(null);
    const isFullScreen = ref(false);
    const playerContainerRef = ref(null);
    
    // 全屏状态监听
    const handleFullScreenChange = () => {
      const fsElement = document.fullscreenElement || 
                        document.webkitFullscreenElement || 
                        document.mozFullScreenElement || 
                        document.msFullscreenElement;
      isFullScreen.value = !!fsElement;
      console.log('📺 全屏状态变化:', isFullScreen.value, '全屏元素:', fsElement);
      
      // 检测是否是视频元素直接进入全屏，如果是，我们也需要处理
      if (fsElement && mediaPlayerRef.value && fsElement === mediaPlayerRef.value) {
        console.log('📺 视频元素直接进入全屏');
        // 这里我们已经有了is-fullscreen类，CSS会处理显示
      }
    };
    
    // 切换全屏（全屏整个容器）
    const toggleFullScreen = () => {
      console.log('📺 切换全屏按钮被点击');
      if (!playerContainerRef.value) {
        console.error('❌ 播放器容器引用不存在');
        return;
      }
      
      if (!document.fullscreenElement && 
          !document.webkitFullscreenElement && 
          !document.mozFullScreenElement && 
          !document.msFullscreenElement) {
        // 进入全屏
        console.log('📺 进入全屏模式');
        if (playerContainerRef.value.requestFullscreen) {
          playerContainerRef.value.requestFullscreen().catch(err => {
            console.error('❌ 全屏请求失败:', err);
          });
        } else if (playerContainerRef.value.webkitRequestFullscreen) {
          playerContainerRef.value.webkitRequestFullscreen().catch(err => {
            console.error('❌ WebKit全屏请求失败:', err);
          });
        } else if (playerContainerRef.value.mozRequestFullScreen) {
          playerContainerRef.value.mozRequestFullScreen().catch(err => {
            console.error('❌ Mozilla全屏请求失败:', err);
          });
        } else if (playerContainerRef.value.msRequestFullscreen) {
          playerContainerRef.value.msRequestFullscreen().catch(err => {
            console.error('❌ IE全屏请求失败:', err);
          });
        }
      } else {
        // 退出全屏
        console.log('📺 退出全屏模式');
        if (document.exitFullscreen) {
          document.exitFullscreen().catch(err => {
            console.error('❌ 退出全屏失败:', err);
          });
        } else if (document.webkitExitFullscreen) {
          document.webkitExitFullscreen().catch(err => {
            console.error('❌ WebKit退出全屏失败:', err);
          });
        } else if (document.mozCancelFullScreen) {
          document.mozCancelFullScreen().catch(err => {
            console.error('❌ Mozilla退出全屏失败:', err);
          });
        } else if (document.msExitFullscreen) {
          document.msExitFullscreen().catch(err => {
            console.error('❌ IE退出全屏失败:', err);
          });
        }
      }
    };
    
    // 用户交互控制
    const lastUserActivity = ref(Date.now());
    const contentPanelRef = ref(null);
    const shouldAutoScroll = ref(true); // 是否应该自动滚动
    let reactivateTimer = null; // 重新激活自动滚动的定时器

    // 返回上一页
    const goBack = () => {
      router.back();
    };

    // 格式化日期
    const formatDate = (dateStr) => {
      if (!dateStr) return '';
      const date = new Date(dateStr);
      return date.toLocaleString('zh-CN');
    };

    // 格式化时间
    const formatTime = (seconds) => {
      if (!seconds && seconds !== 0) return '00:00';
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    // 判断是否为视频文件
    const isVideoFile = computed(() => {
      const fileType = file.value.file_type || '';
      return fileType.includes('video') || ['mp4', 'avi', 'mov', 'mkv'].includes(fileType);
    });

    // 文件URL
    const fileUrl = computed(() => {
        if (!file.value.id) return '';
        const url = fileApi.getDownloadUrl(file.value.id);
        console.log('🎵 [音频文件URL]', url);
        console.log('📄 [文件信息]', file.value);
        return url;
    });

    // 总时长（优先使用媒体文件实际时长）
    const totalDuration = ref('00:00');
    
    // 监听媒体播放器加载完成，获取实际时长
    const handleLoadedMetadata = () => {
      if (mediaPlayerRef.value && mediaPlayerRef.value.duration) {
        totalDuration.value = formatTime(mediaPlayerRef.value.duration);
      }
    };

    // 说话人数（去重）
    const speakerCount = computed(() => {
      // 强制依赖触发更新
      forceStatsUpdate.value;
      
      const data = unifiedTranscription.value;
      if (!data.length) {
        return 0;
      }
      
      const speakers = new Set();
      for (const item of data) {
        if (item.speaker) {
          speakers.add(item.speaker);
        } else if (item.spk) {
          speakers.add(item.spk);
        }
      }
      
      return speakers.size;
    });

    // 总句子数
    const totalSentences = computed(() => {
      // 强制依赖触发更新
      forceStatsUpdate.value;
      
      return unifiedTranscription.value.length || 0;
    });

    // 格式化会议纪要内容（Markdown 渲染）
    const summaryHtml = computed(() => {
      if (!summaryData.value.meeting_summary) return '';
      return marked.parse(summaryData.value.meeting_summary);
    });

    // 格式化会议摘要内容（Markdown 渲染）
    const abstractHtml = computed(() => {
      if (!abstractData.value.meeting_abstract) return '';
      return marked.parse(abstractData.value.meeting_abstract);
    });

    // 加载会议纪要
    const loadSummary = async () => {
      console.log('📋 [函数调用] loadSummary 开始');
      loadingSummary.value = true;
      summaryError.value = '';
      try {
        console.log('📋 [请求参数] fileId:', file.value.id);
        const response = await meetingApi.getSummary(file.value.id);
        console.log('📋 [响应] 完整响应:', response);
        
        if (response && response.status === 'success') {
          console.log('📋 [数据] 会议纪要数据:', response.meeting_summary);
          summaryData.value = response;
        } else {
          console.warn('📋 [警告] 响应状态不是 success，响应:', response);
          // 数据未存在，不显示错误，设置为空
          summaryData.value = { meeting_summary: '' };
        }
      } catch (error) {
        console.error('❌ [错误] 加载会议纪要失败:', error);
        // 数据未存在，不显示错误，设置为空
        summaryData.value = { meeting_summary: '' };
      } finally {
        loadingSummary.value = false;
      }
    };

    // 加载会议摘要
    const loadAbstract = async () => {
      loadingAbstract.value = true;
      abstractError.value = '';
      try {
        const response = await meetingApi.getAbstract(file.value.id);
        if (response.status === 'success') {
          abstractData.value = response;
        } else {
          // 数据未存在，不显示错误，设置为空
          abstractData.value = { meeting_abstract: '' };
        }
      } catch (error) {
        console.error('加载会议摘要失败:', error);
        // 数据未存在，不显示错误，设置为空
        abstractData.value = { meeting_abstract: '' };
      } finally {
        loadingAbstract.value = false;
      }
    };

    // 加载分段
    const loadSegments = async () => {
      loadingSegments.value = true;
      segmentsError.value = '';
      try {
        const response = await meetingApi.getSegments(file.value.id);
        if (response.status === 'success') {
          segmentsData.value = response;
        } else {
          // 数据未存在，不显示错误，设置为空
          segmentsData.value = { segments: [] };
        }
      } catch (error) {
        console.error('加载分段失败:', error);
        // 数据未存在，不显示错误，设置为空
        segmentsData.value = { segments: [] };
      } finally {
        loadingSegments.value = false;
      }
    };

    // 调试用的强制更新ref
    const forceStatsUpdate = ref(0);
    
    // 加载逐字稿
    const loadTranscription = async () => {
      loadingTranscription.value = true;
      transcriptionError.value = '';
      try {
        const response = await meetingApi.getTranscription(file.value.id);
        
        if (response.status === 'success') {
          // 使用Vue的响应式方式更新数据
          transcriptionData.value.segments = response.segments || [];
          transcriptionData.value.speaker_info = response.speaker_info || [];
          transcriptionData.value.raw_sentence_info = response.raw_sentence_info || [];
          
          // 强制触发统计更新
          await nextTick();
          forceStatsUpdate.value++;
        }
      } catch (error) {
        transcriptionError.value = '加载逐字稿失败';
        console.error('加载逐字稿失败:', error);
      } finally {
        loadingTranscription.value = false;
      }
    };

    // 生成会议纪要
    const generateSummary = async () => {
      try {
        const response = await meetingApi.generateSummary({ file_id: file.value.id });
        if (response.status === 'success') {
          summaryData.value = {
            meeting_summary: response.meeting_minutes,
            is_customized: response.is_customized,
            timestamp: response.timestamp
          };
        }
      } catch (error) {
        console.error('生成会议纪要失败:', error);
        alert('生成会议纪要失败');
      }
    };

    // 加载模板列表
    const loadTemplates = async () => {
      console.log('🔄 [开始加载模板列表]');
      loadingTemplates.value = true;
      templatesError.value = '';
      try {
        console.log('📞 [API调用] 调用promptApi.getList()');
        const response = await promptApi.getList();
        console.log('📥 [API响应] 完整响应:', response);
        
        if (response.status === 'success' && response.prompts) {
          console.log('✅ [成功] 原始模板列表:', response.prompts);
          console.log('📊 [统计] 原始模板数量:', response.prompts.length);
          
          // 过滤只显示纪要类型的模板，排除摘要类型
          const summaryTemplates = response.prompts.filter(template => {
            // 根据template_type字段区分，只保留summary类型的模板
            return template.template_type === 'summary';
          });
          
          console.log('✅ [过滤后] 纪要模板列表:', summaryTemplates);
          console.log('📊 [统计] 纪要模板数量:', summaryTemplates.length);
          
          templates.value = summaryTemplates;
        } else {
          console.warn('⚠️ [警告] 响应格式不正确:', response);
          templatesError.value = '模板列表获取失败';
        }
      } catch (error) {
        console.error('❌ [错误] 加载模板列表失败:', error);
        templatesError.value = '加载模板失败';
      } finally {
        loadingTemplates.value = false;
        console.log('🔚 [加载模板列表完成]');
      }
    };

    // 监听模板模态框显示，加载模板列表
    watch(showTemplateModal, (newValue) => {
      if (newValue) {
        loadTemplates();
        selectedTemplateId.value = '';
      }
    });

    // 确认模板更换
    const confirmTemplateChange = () => {
      if (!selectedTemplateId.value) return;
      // 如果已有纪要内容，显示确认弹窗
      if (summaryData.value.meeting_summary) {
        showConfirmModal.value = true;
      } else {
        // 没有内容，直接更换
        executeTemplateChange();
      }
    };

    // 处理结果弹窗确认
    const handleResultConfirm = () => {
      // 关闭结果弹窗
      showResultModal.value = false;
      
      if (resultType.value === 'error') {
        // 错误时回到确认更换弹窗
        if (currentTemplateType.value === 'summary') {
          showConfirmModal.value = true;
        } else if (currentTemplateType.value === 'abstract') {
          showAbstractConfirmModal.value = true;
        }
      } else {
        // 成功时关闭所有弹窗
        showTemplateModal.value = false;
        showConfirmModal.value = false;
        showAbstractTemplateModal.value = false;
        showAbstractConfirmModal.value = false;
        
        // 根据当前模板类型刷新相应内容
        if (currentTemplateType.value === 'summary') {
          loadSummary();
        } else if (currentTemplateType.value === 'abstract') {
          loadAbstract();
        }
        
        // 清空当前模板类型
        currentTemplateType.value = '';
      }
    };

    // 处理确认更换
    const handleConfirmChange = () => {
      // 先关闭确认弹窗
      showConfirmModal.value = false;
      // 执行模板更换
      executeTemplateChange();
    };

    // 执行模板更换
    const executeTemplateChange = async () => {
      if (!selectedTemplateId.value) return;
      
      // 设置当前正在更换的模板类型
      currentTemplateType.value = 'summary';
      
      // 显示加载弹窗
      showLoadingModal.value = true;
      
      try {
        const response = await meetingApi.generateSummary({
          file_id: file.value.id,
          prompt_id: selectedTemplateId.value,
          force_regenerate: true
        });
        
        if (response.status === 'success') {
          // 关闭模态框
          showTemplateModal.value = false;
          showConfirmModal.value = false;
          // 显示成功提示
          resultMessage.value = '模板更换成功，会议纪要已更新';
          resultType.value = 'success';
          showResultModal.value = true;
        } else {
          // 显示失败提示
          resultMessage.value = '模板更换失败: ' + (response.message || '未知错误');
          resultType.value = 'error';
          showResultModal.value = true;
        }
      } catch (error) {
        console.error('更换模板失败:', error);
        
        // 即使超时，也尝试重新获取纪要内容
        try {
          const summaryResponse = await meetingApi.getSummary(file.value.id);
          if (summaryResponse && summaryResponse.status === 'success') {
            summaryData.value = summaryResponse;
            // 显示成功提示
            resultMessage.value = '模板更换成功，会议纪要已更新';
            resultType.value = 'success';
            showResultModal.value = true;
            // 关闭模态框
            showTemplateModal.value = false;
            showConfirmModal.value = false;
            return;
          }
        } catch (retryError) {
          console.error('重试获取纪要失败:', retryError);
        }
        
        // 显示失败提示
        resultMessage.value = '更换模板失败: ' + error.message;
        resultType.value = 'error';
        showResultModal.value = true;
      } finally {
        // 关闭加载弹窗
        showLoadingModal.value = false;
      }
    };

    // 显示模板详情
    const showTemplateDetails = (template) => {
      console.log('🔍 [查看模板详情]', template);
      currentTemplate.value = template;
      showTemplateDetailsModal.value = true;
    };

    // 加载摘要模板列表
    const loadAbstractTemplates = async () => {
      console.log('🔄 [开始加载摘要模板列表]');
      loadingAbstractTemplates.value = true;
      abstractTemplatesError.value = '';
      
      try {
        console.log('📞 [API调用] 调用promptApi.getList()');
        const response = await promptApi.getList();
        console.log('📥 [API响应] 完整响应:', response);
        
        if (response.status === 'success' && response.prompts) {
          // 过滤出摘要类型的模板
          const abstractTemplatesList = response.prompts.filter(template => {
            return template.template_type === 'abstract';
          });
          
          console.log('✅ [过滤后] 摘要模板列表:', abstractTemplatesList);
          console.log('📊 [统计] 摘要模板数量:', abstractTemplatesList.length);
          
          abstractTemplates.value = abstractTemplatesList;
        } else {
          console.warn('⚠️ [警告] 响应格式不正确:', response);
          abstractTemplatesError.value = '模板列表获取失败';
        }
      } catch (error) {
        console.error('❌ [错误] 加载模板列表失败:', error);
        abstractTemplatesError.value = '加载模板失败';
      } finally {
        loadingAbstractTemplates.value = false;
        console.log('🔚 [加载摘要模板列表完成]');
      }
    };

    // 监听摘要模板模态框显示，加载模板列表
    watch(showAbstractTemplateModal, (newValue) => {
      if (newValue) {
        loadAbstractTemplates();
        selectedAbstractTemplateId.value = '';
      }
    });

    // 确认摘要模板更换
    const confirmAbstractTemplateChange = () => {
      if (!selectedAbstractTemplateId.value) return;
      // 如果已有摘要内容，显示确认弹窗
      if (abstractData.value.meeting_abstract) {
        showAbstractConfirmModal.value = true;
      } else {
        // 没有内容，直接更换
        executeAbstractTemplateChange();
      }
    };

    // 处理摘要确认更换
    const handleAbstractConfirmChange = () => {
      // 先关闭确认弹窗
      showAbstractConfirmModal.value = false;
      // 执行摘要模板更换
      executeAbstractTemplateChange();
    };

    // 执行摘要模板更换
    const executeAbstractTemplateChange = async () => {
      if (!selectedAbstractTemplateId.value) return;
      
      // 设置当前正在更换的模板类型
      currentTemplateType.value = 'abstract';
      
      // 显示加载弹窗
      showLoadingModal.value = true;
      
      try {
        const response = await meetingApi.generateAbstract({
          file_id: file.value.id,
          prompt_id: selectedAbstractTemplateId.value,
          force_regenerate: true
        });
        
        if (response.status === 'success') {
          // 关闭模态框
          showAbstractTemplateModal.value = false;
          showAbstractConfirmModal.value = false;
          // 显示成功提示
          resultMessage.value = '模板更换成功，会议摘要已更新';
          resultType.value = 'success';
          showResultModal.value = true;
        } else {
          // 显示失败提示
          resultMessage.value = '更换模板失败: ' + (response.message || '未知错误');
          resultType.value = 'error';
          showResultModal.value = true;
        }
      } catch (error) {
        console.error('更换摘要模板失败:', error);
        
        // 即使超时，也尝试重新获取摘要内容
        try {
          const abstractResponse = await meetingApi.getAbstract(file.value.id);
          if (abstractResponse && abstractResponse.status === 'success') {
            abstractData.value = abstractResponse;
            // 显示成功提示
            resultMessage.value = '模板更换成功，会议摘要已更新';
            resultType.value = 'success';
            showResultModal.value = true;
            // 关闭模态框
            showAbstractTemplateModal.value = false;
            showAbstractConfirmModal.value = false;
            return;
          }
        } catch (retryError) {
          console.error('重试获取摘要失败:', retryError);
        }
        
        // 显示失败提示
        resultMessage.value = '更换模板失败: ' + error.message;
        resultType.value = 'error';
        showResultModal.value = true;
      } finally {
        // 关闭加载弹窗
        showLoadingModal.value = false;
      }
    };

    // 显示摘要模板详情
    const showAbstractTemplateDetails = (template) => {
      console.log('🔍 [查看摘要模板详情]', template);
      currentTemplate.value = template;
      showTemplateDetailsModal.value = true;
    };

    // 生成会议摘要
    const generateAbstract = async () => {
      try {
        const response = await meetingApi.generateAbstract({ file_id: file.value.id });
        if (response.status === 'success') {
          abstractData.value = {
            meeting_abstract: response.meeting_abstract,
            timestamp: response.timestamp
          };
        }
      } catch (error) {
        console.error('生成会议摘要失败:', error);
        alert('生成会议摘要失败');
      }
    };

    // 生成分段
    const generateSegments = async (forceUpdate = false) => {
      showLoadingModal.value = true;
      try {
        const response = await meetingApi.generateSegments(file.value.id, forceUpdate);
        if (response.status === 'success') {
          segmentsData.value = response;
          showLoadingModal.value = false;
          showResultModal.value = true;
          resultMessage.value = '时间轴分段生成成功';
          resultType.value = 'success';
          // 自动刷新数据
          if (forceUpdate) {
            setTimeout(async () => {
              await loadSegments();
            }, 500);
          }
        }
      } catch (error) {
        console.error('生成分段失败:', error);
        showLoadingModal.value = false;
        showResultModal.value = true;
        resultMessage.value = '生成分段失败: ' + error.message;
        resultType.value = 'error';
      }
    };

    // 生成逐字稿
    const generateTranscription = async (forceRegenerate = false) => {
      showLoadingModal.value = true;
      try {
        const response = await meetingApi.generateTranscription(file.value.id, forceRegenerate);
        if (response.status === 'success') {
          transcriptionData.value = response;
          showLoadingModal.value = false;
          showResultModal.value = true;
          resultMessage.value = '逐字稿生成成功';
          resultType.value = 'success';
          // 自动刷新数据
          if (forceRegenerate) {
            setTimeout(async () => {
              await loadTranscription();
            }, 500);
          }
        }
      } catch (error) {
        console.error('生成逐字稿失败:', error);
        showLoadingModal.value = false;
        showResultModal.value = true;
        resultMessage.value = '生成逐字稿失败: ' + error.message;
        resultType.value = 'error';
      }
    };

    // 重新生成逐字稿
    const regenerateTranscription = async () => {
      showRegenerateTranscriptConfirm.value = true;
    };

    // 处理重新生成确认
    const handleRegenerateTranscriptConfirm = async () => {
      showRegenerateTranscriptConfirm.value = false;
      await generateTranscription(true);
    };

    // 重新生成分段
    const regenerateSegments = async () => {
      showRegenerateSegmentsConfirm.value = true;
    };

    // 处理重新生成分段确认
    const handleRegenerateSegmentsConfirm = async () => {
      showRegenerateSegmentsConfirm.value = false;
      await generateSegments(true);
    };
    
    // 搜索逐字稿或导航
    const lastSearchKeyword = ref('');
    
    const handleSearchOrNavigate = async () => {
      console.log('🔍 [搜索] 当前关键词:', searchKeyword.value, '上一次关键词:', lastSearchKeyword.value);
      
      // 判断搜索词是否变化了
      if (searchResults.value.length > 0 && 
          searchKeyword.value.trim() === lastSearchKeyword.value.trim()) {
        // 搜索词没变，按enter循环向下
        console.log('🔍 [搜索] 搜索词相同，向下导航');
        navigateToNext();
      } else {
        // 搜索词变了，重新搜索
        console.log('🔍 [搜索] 搜索词变化，重新搜索');
        lastSearchKeyword.value = searchKeyword.value;
        await handleSearch();
      }
    };

    // 搜索逐字稿
    const handleSearch = async () => {
      console.log('🔍 [搜索] 开始搜索, 关键词:', searchKeyword.value);
      
      if (!searchKeyword.value.trim()) {
        console.log('🔍 [搜索] 清空搜索结果');
        searchResults.value = [];
        currentSearchIndex.value = 0;
        highlightedTranscriptIndex.value = -1;
        lastSearchKeyword.value = '';
        window.__debuggedItems = false;
        window.__lastMatchedIndex = -1;
        return;
      }
      
      loadingSearch.value = true;
      try {
        console.log('🔍 [搜索] 调用API, fileId:', file.value.id);
        const response = await meetingApi.searchTranscription(file.value.id, searchKeyword.value);
        console.log('🔍 [搜索] API响应:', response);
        
        if (response.status === 'success') {
          searchResults.value = response.matches || [];
          currentSearchIndex.value = 0;
          console.log('🔍 [搜索] 搜索结果数量:', searchResults.value.length);
          console.log('🔍 [搜索] 搜索结果详情:', searchResults.value);
          
          // 如果有搜索结果，自动定位到第一个
          if (searchResults.value.length > 0) {
            navigateToResult(0);
          }
        }
      } catch (error) {
        console.error('❌ [搜索] 搜索失败:', error);
        showResultModal.value = true;
        resultType.value = 'error';
        resultMessage.value = error.response?.data?.detail || error.message || '搜索失败，请稍后重试';
      } finally {
        loadingSearch.value = false;
      }
    };
    
    // 判断当前逐字稿项是否是当前搜索结果
    const isCurrentSearchResult = (item) => {
      if (!searchResults.value.length || searchKeyword.value.trim() === '') return false;
      
      const currentResult = searchResults.value[currentSearchIndex.value];
      if (!currentResult) return false;
      
      // 调试：查看逐字稿项的结构
      if (!window.__debuggedItems) {
        window.__debuggedItems = true;
        console.log('🔍 [调试] 逐字稿项示例:', item);
        console.log('🔍 [调试] 逐字稿项keys:', Object.keys(item));
        console.log('🔍 [调试] 搜索结果示例:', currentResult);
        console.log('🔍 [调试] 搜索结果keys:', Object.keys(currentResult));
      }
      
      // 多种匹配方式
      const isMatch = (
        (currentResult.sentence_index && item.sentence_index === currentResult.sentence_index) ||
        (currentResult.id && item.id === currentResult.id) ||
        (currentResult.text && item.text === currentResult.text) ||
        (currentResult.speaker && item.speaker === currentResult.speaker && 
         currentResult.start_time && Math.abs(item.start_time - currentResult.start_time) < 0.1)
      );
      
      // 只在变化时输出，避免刷屏
      if (isMatch && window.__lastMatchedIndex !== currentSearchIndex.value) {
        window.__lastMatchedIndex = currentSearchIndex.value;
        console.log('🎯 [匹配] 匹配成功, 搜索索引:', currentSearchIndex.value, 
                    '匹配方式:', 
                    (currentResult.sentence_index && item.sentence_index === currentResult.sentence_index) ? 'sentence_index' :
                    (currentResult.id && item.id === currentResult.id) ? 'id' :
                    (currentResult.text && item.text === currentResult.text) ? 'text' : 'speaker+time');
      }
      
      return isMatch;
    };

    // 获取当前搜索匹配的高亮文本
    const getMatchedText = (item) => {
      const currentResult = searchResults.value[currentSearchIndex.value];
      if (!currentResult) return item.text;
      
      // 检查是否匹配
      const isMatch = (
        (currentResult.sentence_index && item.sentence_index === currentResult.sentence_index) ||
        (currentResult.id && item.id === currentResult.id) ||
        (currentResult.text && item.text === currentResult.text) ||
        (currentResult.speaker && item.speaker === currentResult.speaker && 
         currentResult.start_time && Math.abs(item.start_time - currentResult.start_time) < 0.1)
      );
      
      if (isMatch && currentResult.highlighted_text) {
        console.log('📝 [高亮] 使用高亮文本:', currentResult.highlighted_text);
        return currentResult.highlighted_text;
      }
      
      return item.text;
    };

    // 导航到指定的搜索结果
    const navigateToResult = (index) => {
      console.log('📍 [导航] 导航到索引:', index);
      
      if (index < 0 || index >= searchResults.value.length) {
        console.log('📍 [导航] 索引超出范围，返回');
        return;
      }
      
      currentSearchIndex.value = index;
      const result = searchResults.value[index];
      console.log('📍 [导航] 当前搜索结果:', result);
      
      // 首先尝试使用sentence_index匹配
      let transcriptIndex = result.sentence_index;
      console.log('📍 [导航] 使用sentence_index:', transcriptIndex);
      
      // 验证索引是否有效
      if (transcriptIndex < 0 || transcriptIndex >= unifiedTranscription.value.length) {
        console.log('📍 [导航] sentence_index无效，尝试其他匹配方式');
        
        // 尝试text匹配
        transcriptIndex = unifiedTranscription.findIndex(
          item => item.text === result.text
        );
        
        if (transcriptIndex === -1) {
          console.log('📍 [导航] text匹配失败，尝试speaker+start_time匹配');
          transcriptIndex = unifiedTranscription.findIndex(
            item => item.speaker === result.speaker && 
                    Math.abs(item.start_time - result.start_time) < 0.1
          );
        }
      }
      
      console.log('📍 [导航] 最终找到的逐字稿索引:', transcriptIndex);
      
      if (transcriptIndex !== -1 && transcriptIndex >= 0 && transcriptIndex < unifiedTranscription.value.length) {
        // 高亮显示该项目
        highlightedTranscriptIndex.value = transcriptIndex;
        console.log('📍 [导航] 设置高亮索引:', transcriptIndex);
        
        // 等待DOM更新后滚动
        nextTick(() => {
          // 滚动到该位置
          const transcriptItem = document.querySelectorAll('.transcript-item')[transcriptIndex];
          console.log('📍 [导航] 找到的DOM元素:', transcriptItem);
          
          if (transcriptItem) {
            transcriptItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
            console.log('📍 [导航] 执行滚动');
          }
        });
        
        // 跳转到视频播放位置
        if (mediaPlayerRef.value) {
          mediaPlayerRef.value.currentTime = result.start_time;
          console.log('📍 [导航] 跳转到视频时间:', result.start_time);
        }
      } else {
        console.log('⚠️ [导航] 所有匹配方式都失败，无法找到对应的逐字稿项');
      }
    };
    
    // 上一个搜索结果
    const navigateToPrevious = () => {
      console.log('⬆️ [导航] 上一个');
      
      if (searchResults.value.length === 0) {
        console.log('⬆️ [导航] 无搜索结果');
        return;
      }
      
      let newIndex = currentSearchIndex.value - 1;
      if (newIndex < 0) {
        newIndex = searchResults.value.length - 1;
      }
      console.log('⬆️ [导航] 从', currentSearchIndex.value, '到', newIndex);
      navigateToResult(newIndex);
    };
    
    // 下一个搜索结果（循环）
    const navigateToNext = () => {
      console.log('⬇️ [导航] 下一个');
      
      if (searchResults.value.length === 0) {
        console.log('⬇️ [导航] 无搜索结果');
        return;
      }
      
      let newIndex = currentSearchIndex.value + 1;
      if (newIndex >= searchResults.value.length) {
        newIndex = 0;
      }
      console.log('⬇️ [导航] 从', currentSearchIndex.value, '到', newIndex);
      navigateToResult(newIndex);
    };

    // 编辑会议纪要
    const editSummary = () => {
      summaryEditText.value = summaryData.value.meeting_summary || '';
      isEditingSummary.value = true;
    };

    // 取消编辑会议纪要
    const cancelEditSummary = () => {
      isEditingSummary.value = false;
      summaryEditText.value = '';
    };

    // 保存会议纪要
    const saveSummary = async () => {
      try {
        const response = await meetingApi.updateSummary(file.value.id, summaryEditText.value);
        if (response.status === 'success') {
          summaryData.value.meeting_summary = summaryEditText.value;
          isEditingSummary.value = false;
          summaryEditText.value = '';
        }
      } catch (error) {
        console.error('保存会议纪要失败:', error);
        alert('保存失败');
      }
    };

    // 编辑会议摘要
    const editAbstract = () => {
      abstractEditText.value = abstractData.value.meeting_abstract || '';
      isEditingAbstract.value = true;
    };

    // 取消编辑会议摘要
    const cancelEditAbstract = () => {
      isEditingAbstract.value = false;
      abstractEditText.value = '';
    };

    // 保存会议摘要
    const saveAbstract = async () => {
      try {
        const response = await meetingApi.updateAbstract(file.value.id, abstractEditText.value);
        if (response.status === 'success') {
          abstractData.value.meeting_abstract = abstractEditText.value;
          isEditingAbstract.value = false;
          abstractEditText.value = '';
        }
      } catch (error) {
        console.error('保存会议摘要失败:', error);
        alert('保存失败');
      }
    };

    // 开始编辑逐字稿
    const startEdit = (index, item) => {
      editingIndex.value = index;
      editingSpeaker.value = item.speaker || '';
      editingText.value = item.text || '';
    };

    // 取消编辑逐字稿
    const cancelTextEdit = () => {
      editingIndex.value = -1;
      editingSpeaker.value = '';
      editingText.value = '';
    };

    // 保存逐字稿文本编辑
    const saveTextEdit = async (index) => {
      try {
        const response = await meetingApi.editTranscription(
          file.value.id,
          index,
          editingText.value,
          editingSpeaker.value
        );
        if (response.status === 'success') {
          // 优先使用新字段
          transcriptionData.value.segments = response.segments || response.transcription;
          cancelTextEdit();
        }
      } catch (error) {
        console.error('保存逐字稿失败:', error);
        alert('保存失败');
      }
    };

    // ========== 导出Word文档功能 ==========
    
    // 导出会议纪要
    const exportSummaryToWord = async () => {
      try {
        const text = summaryData.value.meeting_summary || '';
        if (!text.trim()) {
          alert('会议纪要内容为空，无法导出');
          return;
        }
        
        const fileName = `${file.value.name || '会议'}_纪要`;
        await exportApi.exportToWord({
          transcription_text: text,
          file_name: fileName
        });
      } catch (error) {
        console.error('导出会议纪要失败:', error);
        alert('导出失败');
      }
    };

    // 导出会议摘要
    const exportAbstractToWord = async () => {
      try {
        const text = abstractData.value.meeting_abstract || '';
        if (!text.trim()) {
          alert('会议摘要内容为空，无法导出');
          return;
        }
        
        const fileName = `${file.value.name || '会议'}_摘要`;
        await exportApi.exportToWord({
          transcription_text: text,
          file_name: fileName
        });
      } catch (error) {
        console.error('导出会议摘要失败:', error);
        alert('导出失败');
      }
    };

    // 导出会议分段（时间轴）
    const exportTimelineToWord = async () => {
      try {
        const segments = segmentsData.value.segments || [];
        if (!segments.length) {
          alert('会议分段内容为空，无法导出');
          return;
        }
        
        // 格式化分段内容
        let content = '';
        segments.forEach((seg, index) => {
          content += `${seg.title || '分段' + (index + 1)}\n`;
          content += `时间: ${formatTime(seg.start_time)} - ${formatTime(seg.end_time)}\n`;
          if (seg.content) {
            content += `内容: ${seg.content}\n`;
          }
          if (seg.summary) {
            content += `小结: ${seg.summary}\n`;
          }
          content += '\n';
        });
        
        const fileName = `${file.value.name || '会议'}_时间轴`;
        await exportApi.exportToWord({
          transcription_text: content,
          file_name: fileName
        });
      } catch (error) {
        console.error('导出会议分段失败:', error);
        alert('导出失败');
      }
    };

    // 导出逐字稿
    const exportTranscriptToWord = async () => {
      try {
        const data = unifiedTranscription.value;
        if (!data.length) {
          alert('逐字稿内容为空，无法导出');
          return;
        }
        
        // 格式化逐字稿内容
        let content = '';
        data.forEach((item, index) => {
          const speaker = item.speaker || '未知说话人';
          const text = item.text || '';
          const startTime = item.start_time ? formatTime(item.start_time) : '';
          const endTime = item.end_time ? formatTime(item.end_time) : '';
          
          content += `${speaker}`;
          if (startTime && endTime) {
            content += ` [${startTime} - ${endTime}]`;
          }
          content += `: ${text}\n`;
        });
        
        const fileName = `${file.value.name || '会议'}_逐字稿`;
        await exportApi.exportToWord({
          transcription_text: content,
          file_name: fileName
        });
      } catch (error) {
        console.error('导出逐字稿失败:', error);
        alert('导出失败');
      }
    };

    // 保存说话人编辑
    const saveSpeakerEdit = async (index) => {
      await saveTextEdit(index);
    };

    // 开始编辑分段
    const startSegmentEdit = (segment) => {
      editingSegmentId.value = segment.id;
      editingSegmentTitle.value = segment.title || '';
      editingSegmentSummary.value = segment.summary || '';
      
      // 在下一个tick聚焦到标题输入框
      nextTick(() => {
        const titleInput = document.querySelector('.segment-title-input');
        if (titleInput) titleInput.focus();
      });
    };

    // 取消编辑分段
    const cancelSegmentEdit = () => {
      editingSegmentId.value = -1;
      editingSegmentTitle.value = '';
      editingSegmentSummary.value = '';
    };

    // 保存分段编辑
    const saveSegmentEdit = async (segmentId) => {
      try {
        const response = await meetingApi.updateSegment(segmentId, {
          title: editingSegmentTitle.value,
          summary: editingSegmentSummary.value
        });
        if (response.status === 'success') {
          // 更新本地数据
          const segment = segmentsData.value.segments.find(s => s.id === segmentId);
          if (segment) {
            segment.title = editingSegmentTitle.value;
            segment.summary = editingSegmentSummary.value;
          }
          cancelSegmentEdit();
          // 显示成功提示
          showResultModal.value = true;
          resultMessage.value = '分段更新成功';
          resultType.value = 'success';
        }
      } catch (error) {
        console.error('保存分段失败:', error);
        // 显示失败提示
        showResultModal.value = true;
        resultMessage.value = '保存失败，请重试';
        resultType.value = 'error';
      }
    };

    // 处理分段点击
    const handleSegmentClick = (segment, event) => {
      console.log('🚀 分段被点击', { 
        segment, 
        editingSegmentId: editingSegmentId.value,
        target: event.target,
        currentTarget: event.currentTarget,
        event
      });
      
      if (editingSegmentId.value !== -1) {
        console.log('⚠️ 正在编辑中，不执行跳转');
        return;
      }
      
      console.log('▶️ 执行跳转播放');
      jumpToSegment(segment);
    };

    // 播放分段
    const playSegment = (startTime, endTime) => {
      if (!mediaPlayerRef.value) return;
      
      mediaPlayerRef.value.currentTime = startTime;
      mediaPlayerRef.value.play();
    };
    
    // 跳转到时间轴分段
    const jumpToSegment = (segment) => {
      console.log('🎬 jumpToSegment 调用', { segment, mediaPlayerRef: mediaPlayerRef.value });
      
      if (!mediaPlayerRef.value || !segment) {
        console.log('❌ 缺少必要参数：', { hasPlayer: !!mediaPlayerRef.value, hasSegment: !!segment });
        return;
      }
      const player = mediaPlayerRef.value;

      // 媒体未加载完成，禁止跳转
      if (player.readyState < 1 || !player.duration || player.duration <= 0) {
        console.log('⚠️ 媒体未加载', { 
          readyState: player.readyState, 
          duration: player.duration 
        });
        alert("请等待音频/视频加载完成后再跳转");
        return;
      }

      // 安全计算目标时间，加微小偏移避免边界问题
      const duration = player.duration;
      let targetTime = Math.max(0, Math.min(segment.start_time + 0.01, duration));
      
      console.log('⏰ 跳转时间计算', { 
        segment_start: segment.start_time, 
        duration, 
        targetTime 
      });

      // 高亮 + 切换标签
      activeTab.value = "timeline";
      highlightedSegmentIndex.value = segment.id;
      nextTick(() => scrollToHighlighted(".segment-item.highlighted"));

      // 执行跳转播放
      console.log('▶️ 执行播放跳转', { targetTime });
      player.pause();
      player.currentTime = targetTime;
      player.play().catch(err => {
        console.warn("❌ 播放失败", err);
      });
    };

    // 跳转到逐字稿
    const jumpToTranscript = (item, index) => {
      if (!mediaPlayerRef.value || !item) return;
      const player = mediaPlayerRef.value;

      // 媒体未加载完成，禁止跳转
      if (player.readyState < 1 || !player.duration || player.duration <= 0) {
        alert("请等待音频/视频加载完成后再跳转");
        return;
      }

      // 安全计算目标时间，加微小偏移避免边界问题
      const duration = player.duration;
      let targetTime = Math.max(0, Math.min(item.start_time + 0.01, duration));

      // 高亮 + 切换标签
      activeTab.value = "transcript";
      highlightedTranscriptIndex.value = index;
      nextTick(() => scrollToHighlighted(".transcript-item.highlighted"));

      // 执行跳转播放
      player.pause();
      player.currentTime = targetTime;
      player.play().catch(err => console.warn("播放失败", err));
    };
    
    // 更新用户最后活动时间
    const updateUserActivity = () => {
      lastUserActivity.value = Date.now();
      
      // 用户有操作：立即停止自动滚动
      shouldAutoScroll.value = false;
      
      // 清除之前的定时器
      if (reactivateTimer) {
        clearTimeout(reactivateTimer);
      }
      
      // 1.5秒后重新激活自动滚动
      reactivateTimer = setTimeout(() => {
        shouldAutoScroll.value = true;
        // 重新激活后立即滚动到当前播放位置
        if (activeTab.value === 'transcript') {
          scrollToHighlighted('.transcript-item.highlighted');
        }
      }, 1500);
    };
    
    // 自动滚动到高亮项（仅逐字稿需要检查用户活动）
    const scrollToHighlighted = (selector) => {
      // 如果是逐字稿，检查是否应该自动滚动
      if (selector.includes('transcript') && !shouldAutoScroll.value) {
        return;
      }
      
      nextTick(() => {
        const highlightedElement = document.querySelector(selector);
        if (highlightedElement) {
          highlightedElement.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
          });
        }
      });
    };
    
    // 监听播放时间更新，自动高亮对应项
    const handleTimeUpdate = () => {
      if (!mediaPlayerRef.value) return;
      
      const currentTime = mediaPlayerRef.value.currentTime;
      
      // 找到当前播放时间对应的时间轴分段
      const segments = segmentsData.value.segments || [];
      let activeSegmentId = -1;
      for (let i = segments.length - 1; i >= 0; i--) {
        const segment = segments[i];
        if (currentTime >= segment.start_time) {
          activeSegmentId = segment.id;
          break;
        }
      }
      
      // 只有当高亮项改变时才更新
      if (highlightedSegmentIndex.value !== activeSegmentId) {
        highlightedSegmentIndex.value = activeSegmentId;
        // 如果当前在时间轴标签页，自动滚动
        if (activeTab.value === 'timeline') {
          scrollToHighlighted('.segment-item.highlighted');
        }
      }
      
      // 找到当前播放时间对应的逐字稿项
      const data = unifiedTranscription.value;
      let activeTranscriptIndex = -1;
      for (let i = data.length - 1; i >= 0; i--) {
        const item = data[i];
        if (currentTime >= item.start_time) {
          activeTranscriptIndex = i;
          break;
        }
      }
      
      // 即使高亮项没改变，也要确保滚动到正确位置（处理短暂句子）
      if (highlightedTranscriptIndex.value !== activeTranscriptIndex) {
        highlightedTranscriptIndex.value = activeTranscriptIndex;
      }
      
      // 更新字幕
      const oldSubtitle = currentSubtitle.value;
      if (activeTranscriptIndex !== -1 && data[activeTranscriptIndex]) {
        currentSubtitle.value = data[activeTranscriptIndex];
        if (oldSubtitle !== currentSubtitle.value) {
          console.log('🎬 字幕更新:', currentSubtitle.value);
        }
      } else {
        if (currentSubtitle.value) {
          console.log('🎬 清除字幕');
        }
        currentSubtitle.value = null;
      }
      
      // 每次播放时间更新都检查是否需要滚动（确保持续跟随）
      if (activeTab.value === 'transcript' && activeTranscriptIndex !== -1) {
        scrollToHighlighted('.transcript-item.highlighted');
      }
    };
    
    // 开始编辑说话人
    const startEditSpeaker = (index, item) => {
      editingIndex.value = index;
      editingSpeaker.value = item.speaker || '';
      editingText.value = item.text || '';
      
      // 在下一个tick聚焦到说话人输入框
      nextTick(() => {
        const speakerInput = document.querySelector('.speaker-input');
        if (speakerInput) speakerInput.focus();
      });
    };
    
    // 开始编辑文本
    const startEditText = (index, item) => {
      editingIndex.value = index;
      editingSpeaker.value = item.speaker || '';
      editingText.value = item.text || '';
      
      // 在下一个tick聚焦到文本编辑框
      nextTick(() => {
        const textEditarea = document.querySelector('.text-editarea');
        if (textEditarea) textEditarea.focus();
      });
    };

    onMounted(() => {
      console.log('🚀 [页面加载] MeetingDetailView 已挂载');
      console.log('📍 [路由参数] route.params:', route.params);
      
      // 监听全屏事件
      document.addEventListener('fullscreenchange', handleFullScreenChange);
      document.addEventListener('webkitfullscreenchange', handleFullScreenChange);
      document.addEventListener('mozfullscreenchange', handleFullScreenChange);
      document.addEventListener('MSFullscreenChange', handleFullScreenChange);
      
      // 尝试从 localStorage 中获取 fileData
      let fileData = localStorage.getItem('currentFileData');
      console.log('💾 [localStorage] currentFileData:', fileData);
      
      if (fileData) {
        try {
          file.value = typeof fileData === 'string' ? JSON.parse(fileData) : fileData;
          console.log('📂 [文件信息] file.value:', file.value);
          console.log('🆔 [文件ID] file.value.id:', file.value.id);
          console.log('🔍 [文件所有属性] Object.keys(file.value):', Object.keys(file.value));
          console.log('📌 [会议类型] file.value.meeting_type:', file.value.meeting_type);
          console.log('🎬 [是否视频文件] isVideoFile:', isVideoFile.value);
          
          // 确保我们有正确的文件ID才发起请求
          if (file.value.id) {
            // 等待一下，确保 file.value 已经更新
            setTimeout(() => {
              loadSummary();
              loadAbstract();
              loadSegments();
              loadTranscription();
            }, 100);
          } else {
            console.error('❌ [错误] 文件ID不存在');
          }
        } catch (error) {
          console.error('❌ [错误] 解析文件信息失败:', error);
        }
      } else {
        console.error('❌ [错误] 没有获取到 fileData');
        console.log('💡 [提示] 如果直接输入URL，可能需要先从文件列表进入');
      }
      
      // 等待DOM更新后检查播放器容器
      nextTick(() => {
        console.log('🎬 [播放器容器] playerContainerRef:', playerContainerRef.value);
        console.log('🎬 [媒体播放器] mediaPlayerRef:', mediaPlayerRef.value);
      });
    });
    
    // 监听媒体播放器的加载，添加事件监听器
    watch(mediaPlayerRef, (newPlayer) => {
      if (newPlayer) {
        newPlayer.addEventListener('timeupdate', handleTimeUpdate);
        
        // 拦截视频原生全屏请求，改为播放器容器全屏
        if (isVideoFile.value) {
          const handleEnterFullscreen = (e) => {
            console.log('🎬 拦截到视频原生全屏请求');
            e.preventDefault();
            e.stopPropagation();
            toggleFullScreen();
          };
          
          // 监听全屏相关事件
          newPlayer.addEventListener('webkitfullscreenchange', (e) => {
            console.log('🎬 视频全屏变化:', e);
          });
        }
      }
    }, { flush: 'post' });
    
    // 组件卸载时清理事件监听
    onUnmounted(() => {
      if (mediaPlayerRef.value) {
        mediaPlayerRef.value.removeEventListener('timeupdate', handleTimeUpdate);
      }
      // 移除全屏事件监听
      document.removeEventListener('fullscreenchange', handleFullScreenChange);
      document.removeEventListener('webkitfullscreenchange', handleFullScreenChange);
      document.removeEventListener('mozfullscreenchange', handleFullScreenChange);
      document.removeEventListener('MSFullscreenChange', handleFullScreenChange);
      // 清理定时器
      if (reactivateTimer) {
        clearTimeout(reactivateTimer);
      }
    });

    return {
      file,
      fileId,
      userId,
      activeTab,
      loadingSummary,
      loadingAbstract,
      loadingSegments,
      loadingTranscription,
      summaryError,
      abstractError,
      segmentsError,
      transcriptionError,
      summaryData,
      abstractData,
      segmentsData,
      transcriptionData,
      unifiedTranscription,
      isEditingSummary,
      isEditingAbstract,
      summaryEditText,
      abstractEditText,
      editingIndex,
      editingSpeaker,
      editingText,
      editingSegmentId,
      editingSegmentTitle,
      editingSegmentSummary,
      mediaPlayerRef,
      playerContainerRef,
      currentPlayingIndex,
      highlightedSegmentIndex,
      highlightedTranscriptIndex,
      currentSubtitle,
      isFullScreen,
      contentPanelRef,
      goBack,
      toggleFullScreen,
      formatDate,
      formatTime,
      isVideoFile,
      fileUrl,
      totalDuration,
      speakerCount,
      updateUserActivity,
      totalSentences,
      summaryHtml,
      abstractHtml,
      loadSummary,
      loadAbstract,
      loadSegments,
      loadTranscription,
      generateSummary,
      generateAbstract,
      generateSegments,
      generateTranscription,
      regenerateTranscription,
      editSummary,
      cancelEditSummary,
      saveSummary,
      editAbstract,
      cancelEditAbstract,
      saveAbstract,
      startEdit,
      cancelTextEdit,
      saveTextEdit,
      saveSpeakerEdit,
      // 导出Word文档相关
      exportSummaryToWord,
      exportAbstractToWord,
      exportTimelineToWord,
      exportTranscriptToWord,
      // 分段相关
      startSegmentEdit,
      cancelSegmentEdit,
      saveSegmentEdit,
      handleSegmentClick,
      playSegment,
      jumpToSegment,
      jumpToTranscript,
      scrollToHighlighted,
      startEditSpeaker,
      startEditText,
      handleLoadedMetadata,
      // 模板相关
      showTemplateModal,
      showConfirmModal,
      showTemplateDetailsModal,
      showLoadingModal,
      showResultModal,
      resultMessage,
      resultType,
      templates,
      loadingTemplates,
      loadingTemplateDetails,
      templatesError,
      templateDetailsError,
      selectedTemplateId,
      currentTemplate,
      currentTemplateType,
      confirmTemplateChange,
      executeTemplateChange,
      showTemplateDetails,
      handleResultConfirm,
      handleConfirmChange,
      // 摘要模板相关
      showAbstractTemplateModal,
      showAbstractConfirmModal,
      abstractTemplates,
      loadingAbstractTemplates,
      abstractTemplatesError,
      selectedAbstractTemplateId,
      currentAbstractTemplate,
      confirmAbstractTemplateChange,
      handleAbstractConfirmChange,
      executeAbstractTemplateChange,
      showAbstractTemplateDetails,
      // 逐字稿重新生成相关
      showRegenerateTranscriptConfirm,
      handleRegenerateTranscriptConfirm,
      // 时间轴重新生成相关
      showRegenerateSegmentsConfirm,
      regenerateSegments,
      handleRegenerateSegmentsConfirm,
      // 搜索相关
      searchKeyword,
      searchResults,
      currentSearchIndex,
      loadingSearch,
      handleSearch,
      navigateToResult,
      handleSearchOrNavigate,
      navigateToPrevious,
      navigateToNext,
      isCurrentSearchResult,
      getMatchedText,
      API_BASE_URL
    };
  }
};
</script>

<style scoped>
.meeting-detail-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: #f9fafc;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: white;
  border-bottom: 1px solid #eee;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: white;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  color: #666;
}

.back-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

.header-left h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
  font-weight: 600;
}

.file-info {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #999;
}

.detail-content {
  display: flex;
  flex: 1;
  overflow: hidden;
  padding: 0;
  gap: 0;
}

.left-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 0;
  overflow: hidden;
  border: none;
  border-right: 1px solid #eee;
  padding: 0;
}

.tabs {
  display: flex;
  padding: 16px;
  border-bottom: 1px solid #eee;
  gap: 8px;
}

.tab-btn {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  background: transparent;
  font-size: 14px;
  cursor: pointer;
  color: #666;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: #f5f7fa;
}

.tab-btn.active {
  background: #409eff;
  color: white;
}

.content-panel {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
}

/* 只针对逐字稿内容区，让头部固定，列表滚动 */
.transcript-content,
.summary-content,
.abstract-content,
.timeline-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* 所有页面的内容区域都可以独立滚动 */
.summary-text,
.abstract-text,
.segments-list {
  flex: 1;
  overflow-y: auto;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
  background: white;
  z-index: 10;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.template-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px solid #409eff;
  border-radius: 6px;
  background: white;
  font-size: 13px;
  cursor: pointer;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px solid #67c23a;
  border-radius: 6px;
  background: white;
  color: #67c23a;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.export-btn:hover {
  background: #f0f9eb;
}

.regenerate-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px solid #e6a23c;
  border-radius: 6px;
  background: white;
  color: #e6a23c;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.regenerate-btn:hover {
  background: #fdf6ec;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px solid #909399;
  border-radius: 6px;
  background: white;
  color: #909399;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover {
  background: #f5f7fa;
  transition: all 0.2s;
  color: #409eff;
}

.template-btn:hover {
  background: #ecf5ff;
  border-color: #66b1ff;
}

.content-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #ecf5ff;
  color: #409eff;
  border-radius: 6px;
  font-size: 13px;
}

.edit-btn,
.refresh-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  color: #666;
}

.edit-btn:hover,
.refresh-btn:hover {
  border-color: #409eff;
  color: #409eff;
}

.edit-actions {
  display: flex;
  gap: 8px;
}

.save-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  background: #67c23a;
  color: white;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.save-btn:hover {
  background: #85ce61;
}

.cancel-btn {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  color: #666;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-btn:hover {
  border-color: #f56c6c;
  color: #f56c6c;
}

.loading,
.error,
.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.error {
  color: #f56c6c;
}

.empty-state p {
  margin-bottom: 16px;
}

.generate-btn {
  padding: 10px 24px;
  border: none;
  border-radius: 8px;
  background: #409eff;
  color: white;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.generate-btn:hover {
  background: #66b1ff;
}

.formatted-content {
  line-height: 1.8;
  color: #333;
  font-size: 14px;
  padding: 0 8px;
}

/* 会议纪要内容区域 */
.summary-content,
.abstract-content {
  padding: 0 8px;
}

.edit-textarea {
  width: 100%;
  min-height: 300px;
  padding: 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.8;
  resize: vertical;
  box-sizing: border-box;
}

.edit-textarea:focus {
  outline: none;
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

/* 分段列表样式 */
.segments-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.segment-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #f9fafc;
  border-radius: 8px;
  border-left: 4px solid #409eff;
  cursor: pointer;
  transition: all 0.3s;
}

.segment-item:hover {
  background: #ecf5ff;
}

.segment-item.highlighted {
  border-left-color: #ff9800;
  background: #fff3e0;
  box-shadow: 0 2px 8px rgba(255, 152, 0, 0.3);
  transform: translateX(4px);
  transition: all 0.3s ease;
}

.segment-item.editing {
  background: #fff;
  border-color: #67c23a;
  cursor: default;
}

.segment-time {
  flex-shrink: 0;
  font-size: 13px;
  color: #409eff;
  font-weight: 500;
}

.segment-content {
  flex: 1;
  display: flex;
  align-items: flex-start;
}

.segment-display-wrapper {
  flex: 1;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.segment-display {
  flex: 1;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  margin: -4px -8px;
  transition: background 0.2s;
}

.segment-display:hover {
  background: rgba(64, 158, 255, 0.1);
}

.segment-display:hover .segment-title,
.segment-display:hover .segment-summary {
  color: #409eff;
}

.segment-edit-btn {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  background: transparent;
  font-size: 16px;
  cursor: pointer;
  opacity: 0;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.segment-item:hover .segment-edit-btn {
  opacity: 1;
  background: #ecf5ff;
}

.segment-edit-btn:hover {
  background: #409eff !important;
  color: white;
}

.segment-title {
  margin: 0 0 8px 0;
  font-size: 15px;
  color: #333;
  font-weight: 600;
}

.segment-summary {
  margin: 0;
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

.segment-title-input {
  width: 100%;
  padding: 8px 12px;
  margin-bottom: 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 15px;
  box-sizing: border-box;
}

.segment-title-input:focus {
  outline: none;
  border-color: #409eff;
}

.segment-summary-textarea {
  width: 120%;
  min-height: 150px;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  resize: vertical;
  line-height: 1.6;
  box-sizing: border-box;
  margin-bottom: 12px;
}

.segment-summary-textarea:focus {
  outline: none;
  border-color: #409eff;
}

/* 逐字稿样式 */
.transcript-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.transcript-item {
  padding: 16px;
  padding-left: 12px;
  background: #f9fafc;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border-left: 3px solid #409eff;
  box-sizing: border-box;
}

.transcript-item:hover {
  background: #ecf5ff;
}

.transcript-item.highlighted {
  border-left-color: #ff9800;
  background: #fff3e0;
  box-shadow: 0 2px 8px rgba(255, 152, 0, 0.3);
  transform: translateX(0);
  transition: all 0.3s ease;
}

.transcript-item.search-highlight {
  border-left-color: #67c23a;
  background: #f0f9eb;
  box-shadow: 0 2px 10px rgba(103, 194, 58, 0.3);
  transition: all 0.3s ease;
}

.highlight-yellow {
  background: #e8f5e9;
  color: #2e7d32;
  padding: 0 4px;
  border-radius: 3px;
  font-weight: 600;
}

.transcript-item.editing {
  background: #ecf5ff;
  border: 1px solid #409eff;
}

.speaker-name.clickable {
  cursor: pointer;
  transition: all 0.2s;
}

.speaker-name.clickable:hover {
  text-decoration: underline;
  color: #1976d2;
}

.transcript-text-content {
  cursor: text;
  transition: all 0.2s;
  padding: 4px 8px;
  border-radius: 4px;
  margin: -4px -8px;
}

.transcript-text-content:hover {
  background: rgba(64, 158, 255, 0.1);
}

.transcript-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.speaker-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.speaker-name {
  font-size: 14px;
  font-weight: 600;
  color: #409eff;
}

.transcript-time {
  font-size: 12px;
  color: #999;
  background: white;
  padding: 2px 8px;
  border-radius: 4px;
}



.transcript-text {
  font-size: 14px;
  color: #333;
  line-height: 1.8;
}

.speaker-input {
  width: 200px;
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  margin-bottom: 8px;
}

.speaker-input:focus {
  outline: none;
  border-color: #409eff;
}

.text-editarea {
  width: 100%;
  min-height: 80px;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
  box-sizing: border-box;
  margin-bottom: 8px;
}

.text-editarea:focus {
  outline: none;
  border-color: #409eff;
}

.edit-buttons {
  display: flex;
  gap: 8px;
}

.text-save-btn {
  padding: 4px 12px;
  border: none;
  border-radius: 4px;
  background: #67c23a;
  color: white;
  font-size: 12px;
  cursor: pointer;
}

.text-cancel-btn {
  padding: 4px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: white;
  color: #666;
  font-size: 12px;
  cursor: pointer;
}

/* 右侧面板 */
.right-panel {
  width: 50%;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  background: #f9fafc;
  overflow-y: auto; /* 允许滚动 */
}

.player-container {
  background: black;
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0; /* 防止被压缩 */
}

.player-container.audio-container {
  background: transparent;
  border-radius: 0;
  padding: 20px 0;
}

.media-player {
  width: 100%;
  display: block;
}

.media-player.audio-only {
  height: auto;
  background: transparent;
  min-height: 50px;
}

/* 隐藏视频原生全屏控件 */
.media-player::-webkit-media-controls-fullscreen-button {
  display: none !important;
}

/* 也可以尝试隐藏整个控制条的全屏按钮 */
.media-player::-webkit-media-controls {
  /* 确保我们的全屏按钮是可见的 */
}

/* Firefox */
.media-player::-moz-media-controls-fullscreen-button {
  display: none !important;
}

.stats-container {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #eee;
}

.stats-container h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #333;
  font-weight: 600;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: #f9fafc;
  border-radius: 8px;
  text-align: center;
}

/* 字幕样式 */
.player-container {
  position: relative;
}

/* 全屏模式下的容器样式 */
.player-container:fullscreen,
.player-container:-webkit-full-screen,
.player-container:-moz-full-screen,
.player-container:-ms-full-screen {
  width: 100vw !important;
  height: 100vh !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  background: black !important;
}

/* 全屏时视频样式 */
.player-container:fullscreen .media-player,
.player-container:-webkit-full-screen .media-player,
.player-container:-moz-full-screen .media-player,
.player-container:-ms-full-screen .media-player {
  width: 100% !important;
  height: 100% !important;
  max-width: none !important;
  max-height: none !important;
  object-fit: contain !important;
}

/* 非全屏模式：字幕在容器里 */
.subtitle-container {
  position: absolute;
  bottom: 70px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.75);
  border-radius: 8px;
  padding: 10px 16px;
  display: flex;
  gap: 10px;
  align-items: center;
  max-width: 90%;
  z-index: 10;
  backdrop-filter: blur(4px);
  pointer-events: none;
}

/* 全屏模式下字幕在容器里（跟随容器） */
.player-container:fullscreen .subtitle-container,
.player-container:-webkit-full-screen .subtitle-container,
.player-container:-moz-full-screen .subtitle-container,
.player-container:-ms-full-screen .subtitle-container {
  position: absolute !important;
  bottom: 10% !important;
  left: 50% !important;
  transform: translateX(-50%) !important;
  max-width: 80% !important;
  background: rgba(0, 0, 0, 0.85) !important;
  padding: 12px 18px !important;
  z-index: 9999 !important;
  display: flex !important;
}

/* 备用方案：通过类名控制全屏样式 */
.player-container.is-fullscreen {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  z-index: 9999 !important;
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  background: black !important;
  border-radius: 0 !important;
}

.player-container.is-fullscreen .media-player {
  width: 100% !important;
  height: 100% !important;
  max-width: none !important;
  max-height: none !important;
  object-fit: contain !important;
}

.player-container.is-fullscreen .subtitle-container {
  position: absolute !important;
  bottom: 10% !important;
  left: 50% !important;
  transform: translateX(-50%) !important;
  max-width: 80% !important;
  background: rgba(0, 0, 0, 0.85) !important;
  padding: 12px 18px !important;
  z-index: 9999 !important;
  display: flex !important;
}

.player-container.is-fullscreen .custom-fullscreen-btn {
  display: flex !important;
}

/* 自定义全屏按钮样式 */
.custom-fullscreen-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  width: 44px;
  height: 44px;
  font-size: 20px;
  cursor: pointer;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  backdrop-filter: blur(4px);
}

.custom-fullscreen-btn:hover {
  background: rgba(0, 0, 0, 0.9);
  border-color: rgba(255, 255, 255, 0.6);
  transform: scale(1.1);
}

/* 全屏时按钮应该保持可见，用于退出 */
.player-container:fullscreen .custom-fullscreen-btn,
.player-container:-webkit-full-screen .custom-fullscreen-btn,
.player-container:-moz-full-screen .custom-fullscreen-btn,
.player-container:-ms-full-screen .custom-fullscreen-btn {
  position: fixed !important;
  top: 20px;
  right: 20px;
  z-index: 100001 !important;
  display: flex !important;
  background: rgba(0, 0, 0, 0.8);
  border-color: rgba(255, 255, 255, 0.5);
}

.player-container.is-fullscreen .custom-fullscreen-btn {
  position: fixed !important;
  top: 20px;
  right: 20px;
  z-index: 100001 !important;
  display: flex !important;
  background: rgba(0, 0, 0, 0.8);
  border-color: rgba(255, 255, 255, 0.5);
}

.subtitle-container.subtitle-fullscreen .subtitle-avatar-img {
  width: 40px;
  height: 40px;
}

.subtitle-container.subtitle-fullscreen .subtitle-avatar-default {
  width: 40px;
  height: 40px;
  font-size: 20px;
}

.subtitle-container.subtitle-fullscreen .subtitle-speaker {
  font-size: 16px;
  font-weight: bold;
}

.subtitle-container.subtitle-fullscreen .subtitle-text {
  font-size: 18px;
  line-height: 1.5;
}

/* 全屏时更大的字幕容器 */
.player-container:fullscreen .subtitle-container,
.player-container:-webkit-full-screen .subtitle-container,
.player-container:-moz-full-screen .subtitle-container,
.player-container:-ms-full-screen .subtitle-container,
.player-container.is-fullscreen .subtitle-container {
  padding: 16px 24px !important;
  border-radius: 12px !important;
  gap: 14px !important;
}

.subtitle-avatar {
  flex-shrink: 0;
}

.subtitle-avatar-img {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid white;
}

.subtitle-avatar-default {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  border: 2px solid white;
}

.subtitle-content {
  flex: 1;
  min-width: 0;
}

.subtitle-speaker {
  font-size: 12px;
  font-weight: 600;
  color: #66b1ff;
  margin-bottom: 2px;
}

.subtitle-text {
  font-size: 13px;
  color: white;
  line-height: 1.4;
  word-break: break-word;
  /* 显示全部内容 */
  white-space: normal;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
}

.stat-label {
  font-size: 12px;
  color: #999;
}

.stat-value {
  font-size: 18px;
  color: #333;
  font-weight: 600;
}

.meeting-type-container {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #eee;
}

.meeting-type-container h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #333;
  font-weight: 600;
}

.meeting-type-tag {
  display: inline-block;
  padding: 8px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 14px;
  font-weight: 500;
  border-radius: 20px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

/* 聊天面板容器 */
.chat-panel-container {
  flex: 1;
  min-height: 300px;
}

/* 聊天内容区域 */
.chat-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-content :deep(.meeting-chat-panel) {
  border-radius: 0;
  border: none;
  box-shadow: none;
  flex: 1;
  height: 100%;
}

/* Markdown 样式 */
.markdown-body {
  line-height: 1.8;
  color: #333;
  font-size: 14px;
}

.markdown-body h1 {
  font-size: 24px;
  font-weight: 700;
  margin: 20px 0 12px 0;
  padding-bottom: 8px;
  border-bottom: 2px solid #409eff;
  color: #333;
}

.markdown-body h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 16px 0 10px 0;
  padding-bottom: 6px;
  border-bottom: 1px solid #e5e7eb;
  color: #333;
}

.markdown-body h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 14px 0 8px 0;
  color: #333;
}

.markdown-body h4 {
  font-size: 16px;
  font-weight: 600;
  margin: 12px 0 6px 0;
  color: #333;
}

.markdown-body p {
  margin: 10px 0;
  color: #4b5563;
}

.markdown-body ul, .markdown-body ol {
  padding-left: 24px;
  margin: 10px 0;
}

.markdown-body ul {
  list-style-type: disc;
}

.markdown-body ol {
  list-style-type: decimal;
}

.markdown-body li {
  margin: 6px 0;
  color: #4b5563;
}

.markdown-body blockquote {
  border-left: 4px solid #409eff;
  padding-left: 16px;
  margin: 12px 0;
  color: #6b7280;
  background: #f9fafc;
  padding: 12px 16px;
  border-radius: 0 8px 8px 0;
}

.markdown-body code {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: #d946ef;
}

.markdown-body pre {
  background: #1f2937;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}

.markdown-body pre code {
  background: none;
  padding: 0;
  color: #e5e7eb;
}

.markdown-body a {
  color: #409eff;
  text-decoration: none;
}

.markdown-body a:hover {
  text-decoration: underline;
}

.markdown-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
}

.markdown-body th, .markdown-body td {
  border: 1px solid #e5e7eb;
  padding: 8px 12px;
  text-align: left;
}

.markdown-body th {
  background: #f9fafc;
  font-weight: 600;
}

.markdown-body strong {
  font-weight: 600;
  color: #333;
}

.markdown-body em {
  font-style: italic;
}

.markdown-body hr {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 16px 0;
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
  z-index: 1000;
}

/* 加载弹窗需要更高的z-index */
.loading-overlay {
  z-index: 2000 !important;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
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

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px;
  border-top: 1px solid #f0f0f0;
}

/* 加载弹窗样式 */
.loading-modal {
  max-width: 350px;
  text-align: center;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #67c23a;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 20px auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-modal p {
  margin: 0 0 20px 0;
  color: #666;
  font-size: 14px;
}

/* 结果提示弹窗样式 */
.result-modal {
  max-width: 350px;
  text-align: center;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.result-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: bold;
  margin: 20px auto 20px;
}

.result-icon.success {
  background: #f0f9eb;
  color: #67c23a;
}

.result-icon.error {
  background: #fef0f0;
  color: #f56c6c;
}

.result-modal h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #333;
}

.result-modal p {
  margin: 0 0 20px 0;
  color: #666;
  font-size: 14px;
}

.result-modal .modal-footer {
  justify-content: center;
  padding-top: 0;
}

.modal-body {
  background: #fafafa;
}

/* 模板列表样式 */
.templates-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.template-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid #eee;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.template-item:hover {
  border-color: #409eff;
  background: #f5f7fa;
}

.template-item.selected {
  border-color: #409eff;
  background: #ecf5ff;
}

.template-info {
  flex: 1;
}

.template-info h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #333;
  font-weight: 600;
}

.template-description {
  margin: 0;
  font-size: 13px;
  color: #666;
  line-height: 1.4;
}

.template-select {
  margin-left: 16px;
}

.template-actions {
  margin-top: 8px;
}

.view-details-link {
  color: #409eff;
  font-size: 12px;
  text-decoration: none;
  cursor: pointer;
  transition: color 0.2s;
}

.view-details-link:hover {
  color: #66b1ff;
  text-decoration: underline;
}

/* 模板详情弹窗样式 */
.template-details-modal {
  max-width: 800px;
  width: 90%;
}

.template-details-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-row {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.detail-col {
  flex: 1;
  min-width: 300px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-col.full-width {
  flex: 1 1 100%;
  min-width: 100%;
}

.detail-col label {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.readonly-input {
  padding: 8px 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #f9fafc;
  font-size: 14px;
  color: #333;
  min-height: 36px;
  display: flex;
  align-items: center;
}

.readonly-textarea {
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  background: #f9fafc;
  font-size: 13px;
  color: #333;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
  height: 360px;
  overflow-y: auto;
  resize: none;
}

/* 确认弹窗样式 */
.confirm-modal {
  max-width: 400px;
  text-align: center;
}

.confirm-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.confirm-modal h3 {
  margin: 0 0 16px 0;
  color: #333;
}

.confirm-modal p {
  margin: 8px 0;
  color: #666;
  line-height: 1.6;
}

.confirm-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  background: #67c23a;
  color: white;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.confirm-btn:hover {
  background: #85ce61;
}

.confirm-btn:disabled {
  background: #c0c4cc;
  cursor: not-allowed;
}

.confirm-btn.danger {
  background: #f56c6c;
  border-color: #f56c6c;
}

.confirm-btn.danger:hover {
  background: #f78989;
  border-color: #f78989;
}

/* 逐字稿内容区域 */
.transcript-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
}

/* 标题栏置顶 */
.content-header {
  position: sticky;
  top: 0;
  background: white;
  z-index: 100;
  padding: 8px 0;
  border-bottom: 1px solid #e2e8f0;
}

/* 搜索容器 */
.search-container {
  flex-shrink: 0;
  background: white;
  z-index: 99;
  margin-bottom: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #e5e7eb;
}

.search-input-wrapper {
  display: flex;
  gap: 8px;
  max-width: 500px;
}

.search-input-container {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.search-input {
  flex: 1;
  padding: 8px 60px 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
  height: 36px;
  box-sizing: border-box;
}

.search-input:focus {
  border-color: #67c23a;
}

.search-counter {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 13px;
  color: #666;
  background: #f0f0f0;
  padding: 2px 8px;
  border-radius: 4px;
  pointer-events: none;
}

.search-btn {
  padding: 0 12px;
  background: #67c23a;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 逐字稿列表 */
.transcript-list {
  flex: 1;
  overflow-y: auto;
  max-height: calc(100vh - 240px);
}

/* 逐字稿条目 */
.transcript-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  background: #f8f9fa;
  transition: all 0.2s;
  cursor: pointer;
}

.transcript-item:hover {
  background: #f0f0f0;
}

.transcript-item.highlighted {
  background: #e6f7ff;
  border: 2px solid #409eff;
}

.transcript-item.search-highlight {
  background: #f6ffed;
  border: 2px solid #67c23a;
}

.transcript-item.editing {
  background: #fff7e6;
  border: 2px solid #fa8c16;
}

/* 发言人头像 */
.transcript-avatar {
  flex-shrink: 0;
  display: flex;
  align-items: flex-start;
  padding-top: 2px;
}

.transcript-avatar-img {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #eee;
}

.transcript-avatar-default {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f5f7fa;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  border: 2px solid #ddd;
}

/* 内容区域 */
.transcript-content-area {
  flex: 1;
  min-width: 0;
}

.search-btn:hover {
  background: #85ce61;
}
  
</style>

<!-- Markdown 专用样式（非 scoped） - 给 v-html 渲染的内容用 -->
<style>
.formatted-content.markdown-body table {
  width: 100% !important;
  border-collapse: collapse !important;
  margin: 12px 0 !important;
  font-size: 14px !important;
}

.formatted-content.markdown-body th,
.formatted-content.markdown-body td {
  border: 1px solid #e5e7eb !important;
  padding: 8px 12px !important;
  text-align: left !important;
}

.formatted-content.markdown-body th {
  background: #f9fafb !important;
  font-weight: 600 !important;
  color: #374151 !important;
}

.formatted-content.markdown-body tr:nth-child(even) {
  background: #f9fafb !important;
}

.formatted-content.markdown-body ul,
.formatted-content.markdown-body ol {
  padding-left: 24px !important;
  margin: 8px 0 !important;
  list-style-position: outside !important;
}

.formatted-content.markdown-body ul {
  list-style-type: disc !important;
}

.formatted-content.markdown-body ol {
  list-style-type: decimal !important;
}
</style>
