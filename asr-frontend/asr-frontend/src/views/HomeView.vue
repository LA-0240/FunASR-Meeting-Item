<template>
  <div class="tencent-meeting-page">
    <!-- 顶部导航栏 -->
    <div class="nav-bar">
      <div class="logo">
        <i class="el-icon-video-play"></i>
        <span>ASR智能会议纪要</span>
      </div>
      <div class="nav-actions">
        <el-button type="text">帮助</el-button>
        <el-button type="text">设置</el-button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-container">
      <!-- 左侧音频播放区 -->
      <div class="audio-panel">
        <div class="panel-header">
          <h3>音频播放</h3>
        </div>
        
        <!-- 音频/视频播放器 → 自动切换 -->
        <div class="audio-player">
          <!-- 视频播放器 -->
          <video
            v-if="fileType === 'video'"
            ref="videoRef"
            controls
            class="video-player"
            @timeupdate="handleTimeUpdate"
            @loadedmetadata="handleVideoLoadedMetadata"
            @error="handleVideoError"
          ></video>
          <!-- 音频播放器 -->
          <audio
            v-else
            ref="audioRef"
            controls
            class="audio-core"
            @timeupdate="handleTimeUpdate"
            @loadedmetadata="handleLoadedMetadata"
            @error="handleAudioError"
          >
            您的浏览器不支持音频播放
          </audio>

          <!-- 时间轴（不动） -->
          <div class="timeline-container">
            <div class="timeline" ref="timelineRef" @click="handleTimelineClick">
              <div class="progress" :style="{ width: progressPercent + '%' }"></div>
              <div
                class="time-mark"
                v-for="(item, idx) in transcriptionResult"
                :key="idx"
                :style="{ left: getTimeMarkPosition(item.start_time, audioDuration) + '%' }"
                @click.stop="jumpToTime(item.start_time)"
                :class="{ active: currentTime >= item.start_time && currentTime <= item.end_time }"
              ></div>
            </div>
            <div class="time-text">
              <span>{{ formatTime(currentTime) }}</span>
              <span>/</span>
              <span>{{ formatTime(audioDuration) }}</span>
            </div>
          </div>
        </div>

        <!-- 文件上传区 -->
        <div class="upload-area">
          <el-upload
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :file-list="fileList"
            accept=".wav,.mp3,.ogg,.flac,.mp4,.avi,.mov,.mkv,.flv,.wmv"
            class="upload-box"
            :before-upload="beforeUpload"
          >
            <i class="el-icon-upload"></i>
            <div class="el-upload__text">拖拽音频文件至此</div>
            <div class="tips">支持 .wav / .mp3 / .ogg / .flac / .mp4 / .avi / .mov / .mkv / .flv / .wmv</div>
          </el-upload>

          <div class="action-buttons">
            <!-- 音频转写：上传视频时禁用 -->
            <el-button 
              type="primary" 
              :loading="asrLoading" 
              @click="handleASR"
              :disabled="fileType === 'video'"
            >
              <i class="el-icon-microphone"></i> 音频转写
            </el-button>

            <!-- 视频转写：上传音频时禁用 -->
            <el-button 
              type="success" 
              :loading="videoAsrLoading" 
              @click="handleVideoASR"
              :disabled="fileType === 'audio'"
            >
              <i class="el-icon-video-play"></i> 视频转写
            </el-button>

            <el-button 
              :disabled="!transcriptionResult.length" 
              :loading="summaryLoading" 
              @click="handleGenerateSummary"
            >
              <i class="el-icon-notebook-2"></i> 生成纪要
            </el-button>
            <el-button 
              :disabled="!transcriptionResult.length" 
              :loading="abstractLoading" 
              @click="handleGenerateAbstract"
            >
              <i class="el-icon-document"></i> 生成摘要
            </el-button>
          </div>
        </div>
      </div>

      <!-- 右侧内容区 -->
      <div class="content-panel">
        <el-tabs v-model="activeTab" class="content-tabs">
          <el-tab-pane label="实时转写" name="transcript">
            <div class="transcript-container">
              <div class="transcript-header">
                <h4>语音转写结果（{{ transcriptionResult.length }}段）</h4>
                <el-button size="small" @click="exportTranscriptionWordHandler">
                  <i class="el-icon-download"></i> 导出Word
                </el-button>
                <!-- 新增：下载SRT字幕 -->
                <el-button 
                  size="small" 
                  type="warning"
                  :disabled="!subtitleDownloadUrl"
                  @click="downloadSubtitle"
                >
                  <i class="el-icon-download"></i> 下载字幕
                </el-button>
              </div>
              
              <div class="transcript-scroll-wrapper" ref="scrollWrapperRef">
                <div class="transcript-list">
                  <div 
                    class="transcript-item" 
                    v-for="(item, idx) in transcriptionResult" 
                    :key="idx"
                    :class="{ highlight: currentTime >= item.start_time && currentTime <= item.end_time }"
                    @click="jumpToTime(item.start_time)"
                  >
                    <div class="item-header">
                      <span class="speaker-tag">发言人 {{ item.spk }}</span>
                      <span class="time-tag">{{ formatTime(item.start_time) }} - {{ formatTime(item.end_time) }}</span>
                    </div>
                    <div class="item-content">{{ item.text }}</div>
                  </div>
                  
                  <div class="empty-tip" v-if="!transcriptionResult.length">
                    暂无转写内容，请先上传音频并开始转写
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="会议纪要" name="summary" :disabled="!summaryResult">
            <div class="summary-container">
              <div class="summary-header">
                <h4>智能会议纪要</h4>
                <el-button size="small" @click="exportSummaryWordHandler">
                  <i class="el-icon-download"></i> 导出Word
                </el-button>
              </div>
              
              <div class="summary-content">
                <pre v-if="summaryResult">{{ summaryResult }}</pre>
                <div class="empty-tip" v-else>
                  暂无会议纪要，请先完成语音转写并生成纪要
                </div>
              </div>
            </div>
          </el-tab-pane>
          <!-- 新增：会议摘要标签页 -->
          <el-tab-pane label="会议摘要" name="abstract" :disabled="!abstractResult">
            <div class="summary-container">
              <div class="summary-header">
                <h4>智能会议摘要</h4>
                <el-button size="small" @click="exportAbstractWordHandler">
                  <i class="el-icon-download"></i> 导出Word
                </el-button>
              </div>
              
              <div class="summary-content">
                <pre v-if="abstractResult">{{ abstractResult }}</pre>
                <div class="empty-tip" v-else>
                  暂无会议摘要，请先完成语音转写并生成摘要
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useAudio } from '@/composables/useAudio'
import { useASR } from '@/composables/useASR'
import { useVideoASR } from '@/composables/useVideoASR'
import { useSummary } from '@/composables/useSummary'
import '@/styles/HomeView.scss'

// 音频控制逻辑
const {
  audioRef,
  videoRef,
  timelineRef,
  scrollWrapperRef,
  audioDuration,
  currentTime,
  progressPercent,
  fileList,
  currentFile,
  fileType,
  formatTime,
  getTimeMarkPosition,
  handleLoadedMetadata,
  handleAudioError,
  handleVideoLoadedMetadata, // 👈 必须有
  handleVideoError,
  beforeUpload,
  handleFileChange,
  handleTimeUpdate,
  handleTimelineClick,
  jumpToTime,
} = useAudio()

// 音频转写（重命名，避免冲突）
const {
  asrLoading,
  transcriptionResult: audioTransResult,
  transcriptionText: audioTransText,
  handleASR
} = useASR(currentFile)

// 视频转写（重命名，避免冲突）
const {
  videoAsrLoading,
  transcriptionResult: videoTransResult,
  transcriptionText: videoTransText,
  subtitleDownloadUrl,
  handleVideoASR
} = useVideoASR(currentFile)

// 统一对外暴露：音频/视频共用一套视图变量
import { computed } from 'vue'
const transcriptionResult = computed(() => {
  return videoTransResult.value.length > 0 ? videoTransResult.value : audioTransResult.value
})
const transcriptionText = computed(() => {
  return videoTransText.value || audioTransText.value
})

// 会议摘要逻辑（现在正常传入 subtitleDownloadUrl）
const {
  summaryLoading,
  summaryResult,
  abstractLoading,
  abstractResult,
  activeTab,
  handleGenerateSummary,
  handleGenerateAbstract,
  exportTranscriptionWordHandler,
  exportSummaryWordHandler,
  exportAbstractWordHandler,
  downloadSubtitle
} = useSummary(transcriptionText, currentFile, subtitleDownloadUrl)
</script>