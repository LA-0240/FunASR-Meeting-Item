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
    # Word导出接口
    ExportTranscriptionWordView,
    ExportSummaryWordView,
    ExportAbstractWordView,
    # 声纹管理接口
    VoiceprintAddView,
    VoiceprintListView,
    VoiceprintRenameView,
    VoiceprintDeleteView,
    # 用户管理接口
    UserRegisterView,
    UserLoginView,
    UserLogoutView,
    UserProfileView,
    # 文件管理接口
    FileUploadView,
    FileListView,
    FileRenameView,
    FileDeleteView,
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
    
    # Word导出接口
    path('export_transcription_word', ExportTranscriptionWordView.as_view(), name='export-transcription-word'),    # Word导出（转录文本）
    path('export_summary_word', ExportSummaryWordView.as_view(), name='export-summary-word'),    # Word导出（会议纪要）
    path('export_abstract_word', ExportAbstractWordView.as_view(), name='export-abstract-word'),    # Word导出（会议摘要）
    
    # 声纹管理接口
    path('voiceprint/add', VoiceprintAddView.as_view(), name='voiceprint-add'), # 声纹添加
    path('voiceprint/list', VoiceprintListView.as_view(), name='voiceprint-list'), # 声纹列表
    path('voiceprint/rename', VoiceprintRenameView.as_view(), name='voiceprint-rename'), # 声纹重命名
    path('voiceprint/delete', VoiceprintDeleteView.as_view(), name='voiceprint-delete'), # 声纹删除

    # 用户接口
    path('user/register', UserRegisterView.as_view(), name='user-register'), # 用户注册
    path('user/login', UserLoginView.as_view(), name='user-login'), # 用户登录
    path('user/logout', UserLogoutView.as_view(), name='user-logout'), # 用户退出登录
    path('user/profile', UserProfileView.as_view(), name='user-profile'),   # 用户信息
    
    # 文件接口
    path('file/upload', FileUploadView.as_view(), name='file-upload'), # 文件上传
    path('file/list', FileListView.as_view(), name='file-list'), # 文件列表
    path('file/rename', FileRenameView.as_view(), name='file-rename'), # 文件重命名
    path('file/delete', FileDeleteView.as_view(), name='file-delete'), # 文件删除
    
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
]