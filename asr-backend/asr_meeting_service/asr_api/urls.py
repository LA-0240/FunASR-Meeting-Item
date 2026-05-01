from django.urls import path
from .views import (
    # 基础接口
    HealthCheckView,
    # ASR接口
    ASRTranscribeView,
    VideoASRTranscribeView,
    # LLM-api调用接口
    MeetingSummaryView,
    MeetingAbstractView,
    MeetingSummaryUpdateView,
    MeetingAbstractUpdateView,
    GetMeetingSummaryView,
    GetMeetingAbstractView,
    GenerateSegmentsView,
    SegmentsListView,
    SegmentUpdateView,
    # Word导出接口
    ExportTranscriptionWordView,
    ExportSummaryWordView,
    ExportAbstractWordView,
    # 声纹管理接口
    VoiceprintAddView,
    VoiceprintListView,
    VoiceprintRenameView,
    VoiceprintDeleteView,
    VoiceprintAudioView,
    VoiceprintAvatarUploadView,
    VoiceprintAvatarDeleteView,
    # Speaker管理接口（新增）
    SpeakerListView,
    SpeakerAddView,
    SpeakerUpdateView,
    SpeakerDeleteView,
    SpeakerAvatarUploadView,
    SpeakerAvatarDeleteView,
    SpeakerVoiceprintAddView,
    SpeakerVoiceprintDeleteView,
    SpeakerVoiceprintUpdateView,
    SpeakerVoiceprintAudioView,
    # 用户管理接口
    UserRegisterView,
    UserLoginView,
    UserLogoutView,
    UserProfileView,
    UserAvatarUploadView,
    UserAvatarDeleteView,
    # 文件管理接口
    FileUploadView,
    FileListView,
    FileRenameView,
    FileDeleteView,
    FileDownloadView,
    # 逐字稿接口
    TranscriptionSearchView,
    TranscriptionGetView,
    TranscriptionEditView,
    TranscriptionGenerateView,
    # 文件上传转录接口
    FileUploadTranscribeView,
    # Prompt模板管理接口
    PromptListView,
    PromptAddView,
    PromptUpdateView,
    PromptDeleteView,
    PromptCopyView,
    # 会议分析接口
    MeetingAnalysisView,
    # RAG接口（新增）
    ChatView,
    IndexFileView,
    IndexStatusView,
    TestRetrieveView,
)

urlpatterns = [
    # 基础接口
    path('', HealthCheckView.as_view(), name='health-check'),

    # ASR接口
    path('asr', ASRTranscribeView.as_view(), name='asr-transcribe'),    # ASR语音转文字
    path('video_asr', VideoASRTranscribeView.as_view(), name='video-asr-transcribe'),    # 视频ASR接口
    
    # LLM-api调用接口
    path('generate_summary', MeetingSummaryView.as_view(), name='generate-summary'),    # 会议纪要生成
    path("meeting_abstract", MeetingAbstractView.as_view(), name="meeting-abstract"),    # 会议摘要
    path("meeting/summary/update", MeetingSummaryUpdateView.as_view(), name="meeting-summary-update"),    # 会议纪要编辑
    path("meeting/abstract/update", MeetingAbstractUpdateView.as_view(), name="meeting-abstract-update"),    # 会议摘要编辑
    path("meeting/summary/get", GetMeetingSummaryView.as_view(), name="meeting-summary-get"),    # 获取会议纪要
    path("meeting/abstract/get", GetMeetingAbstractView.as_view(), name="meeting-abstract-get"),    # 获取会议摘要
    path("meeting/segments/generate", GenerateSegmentsView.as_view(), name="meeting-segments-generate"),    # 生成分段
    path("meeting/segments/list", SegmentsListView.as_view(), name="meeting-segments-list"),    # 获取分段列表
    path("meeting/segments/update/<int:segment_id>", SegmentUpdateView.as_view(), name="meeting-segment-update"),    # 编辑分段
    path("meeting/analysis/<int:file_id>", MeetingAnalysisView.as_view(), name="meeting-analysis"),    # 会议分析
    
    # Word导出接口
    path('export_transcription_word', ExportTranscriptionWordView.as_view(), name='export-transcription-word'),    # Word导出（转录文本）
    path('export_summary_word', ExportSummaryWordView.as_view(), name='export-summary-word'),    # Word导出（会议纪要）
    path('export_abstract_word', ExportAbstractWordView.as_view(), name='export-abstract-word'),    # Word导出（会议摘要）
    
    # 声纹管理接口
    path('voiceprint/add', VoiceprintAddView.as_view(), name='voiceprint-add'), # 声纹添加
    path('voiceprint/list', VoiceprintListView.as_view(), name='voiceprint-list'), # 声纹列表
    path('voiceprint/rename', VoiceprintRenameView.as_view(), name='voiceprint-rename'), # 声纹重命名
    path('voiceprint/delete', VoiceprintDeleteView.as_view(), name='voiceprint-delete'), # 声纹删除
    path('voiceprint/audio/<int:vp_id>', VoiceprintAudioView.as_view(), name='voiceprint-audio'), # 声纹音频文件获取
    path('voiceprint/avatar/upload/<int:vp_id>', VoiceprintAvatarUploadView.as_view(), name='voiceprint-avatar-upload'), # 声纹头像上传
    path('voiceprint/avatar/delete/<int:vp_id>', VoiceprintAvatarDeleteView.as_view(), name='voiceprint-avatar-delete'), # 声纹头像删除
    
    # Speaker管理接口（新增）
    path('speaker/list', SpeakerListView.as_view(), name='speaker-list'), # Speaker列表
    path('speaker/add', SpeakerAddView.as_view(), name='speaker-add'), # Speaker创建
    path('speaker/update', SpeakerUpdateView.as_view(), name='speaker-update'), # Speaker更新
    path('speaker/delete', SpeakerDeleteView.as_view(), name='speaker-delete'), # Speaker删除
    path('speaker/avatar/upload/<int:sp_id>', SpeakerAvatarUploadView.as_view(), name='speaker-avatar-upload'), # Speaker头像上传
    path('speaker/avatar/delete/<int:sp_id>', SpeakerAvatarDeleteView.as_view(), name='speaker-avatar-delete'), # Speaker头像删除
    path('speaker/<int:sp_id>/voiceprint/add', SpeakerVoiceprintAddView.as_view(), name='speaker-voiceprint-add'), # 给Speaker追加声纹
    path('speaker/<int:sp_id>/voiceprint/delete/<int:vp_id>', SpeakerVoiceprintDeleteView.as_view(), name='speaker-voiceprint-delete'), # 删除Speaker的声纹
    path('speaker/<int:sp_id>/voiceprint/update/<int:vp_id>', SpeakerVoiceprintUpdateView.as_view(), name='speaker-voiceprint-update'), # 更新Speaker的声纹
    path('speaker/<int:sp_id>/voiceprint/audio/<int:vp_id>', SpeakerVoiceprintAudioView.as_view(), name='speaker-voiceprint-audio'), # 获取Speaker声纹音频

    # 用户接口
    path('user/register', UserRegisterView.as_view(), name='user-register'), # 用户注册
    path('user/login', UserLoginView.as_view(), name='user-login'), # 用户登录
    path('user/logout', UserLogoutView.as_view(), name='user-logout'), # 用户退出登录
    path('user/profile', UserProfileView.as_view(), name='user-profile'),   # 用户信息
    path('user/avatar/upload', UserAvatarUploadView.as_view(), name='user-avatar-upload'), # 头像上传
    path('user/avatar/delete', UserAvatarDeleteView.as_view(), name='user-avatar-delete'), # 头像删除
    
    # 文件接口
    path('file/upload', FileUploadView.as_view(), name='file-upload'), # 文件上传
    path('file/list', FileListView.as_view(), name='file-list'), # 文件列表
    path('file/rename', FileRenameView.as_view(), name='file-rename'), # 文件重命名
    path('file/delete', FileDeleteView.as_view(), name='file-delete'), # 文件删除
    path('file/download/<int:file_id>', FileDownloadView.as_view(), name='file-download'), # 文件下载
    
    # 逐字稿接口
    path('transcription/search', TranscriptionSearchView.as_view(), name='transcription-search'), # 逐字稿搜索
    path('transcription/get/<int:file_id>', TranscriptionGetView.as_view(), name='transcription-get'), # 获取逐字稿
    path('transcription/edit', TranscriptionEditView.as_view(), name='transcription-edit'), # 编辑逐字稿
    path('transcription/generate', TranscriptionGenerateView.as_view(), name='transcription-generate'), # 生成逐字稿
    
    # 文件上传转录接口
    path('file/upload_transcribe', FileUploadTranscribeView.as_view(), name='file-upload-transcribe'), # 文件上传自动转录
    
    # Prompt模板管理接口
    path('prompt/list', PromptListView.as_view(), name='prompt-list'), # 获取模板列表
    path('prompt/add', PromptAddView.as_view(), name='prompt-add'), # 添加模板
    path('prompt/update/<int:prompt_id>', PromptUpdateView.as_view(), name='prompt-update'), # 更新模板
    path('prompt/delete/<int:prompt_id>', PromptDeleteView.as_view(), name='prompt-delete'), # 删除模板
    path('prompt/copy/<int:prompt_id>', PromptCopyView.as_view(), name='prompt-copy'), # 获取模板内容（用于前端复制到编辑窗口）
    
    # RAG接口（新增）
    path('rag/chat', ChatView.as_view(), name='rag-chat'),  # 聊天接口
    path('rag/index', IndexFileView.as_view(), name='rag-index'),  # 索引文件
    path('rag/status', IndexStatusView.as_view(), name='rag-status'),  # 索引状态
    path('rag/test', TestRetrieveView.as_view(), name='rag-test'),  # 测试检索
]