# 导出所有视图类，保持引用一致性
from .base import HealthCheckView
from .asr import ASRTranscribeView
from .video import VideoASRTranscribeView
from .meeting import MeetingSummaryView, MeetingAbstractView, MeetingSummaryUpdateView, MeetingAbstractUpdateView, GetMeetingSummaryView, GetMeetingAbstractView
from .export import ExportTranscriptionWordView, ExportSummaryWordView, ExportAbstractWordView
from .voiceprint import VoiceprintAddView, VoiceprintListView, VoiceprintRenameView, VoiceprintDeleteView
from .user import UserRegisterView, UserLoginView, UserLogoutView, UserProfileView
from .file import FileUploadView, FileListView, FileRenameView, FileDeleteView
from .transcription import TranscriptionSearchView, TranscriptionGetView, TranscriptionEditView, TranscriptionGenerateView
from .upload_transcribe import FileUploadTranscribeView
from .prompt import PromptListView, PromptAddView, PromptUpdateView, PromptDeleteView, PromptCopyView

__all__ = [
    # 基础
    'HealthCheckView',
    # 语音识别-asr
    'ASRTranscribeView',
    # 视频识别-video-asr
    'VideoASRTranscribeView',
    # 会议纪要、会议摘要-meeting
    'MeetingSummaryView',
    'MeetingAbstractView',
    'MeetingSummaryUpdateView',
    'MeetingAbstractUpdateView',
    'GetMeetingSummaryView',
    'GetMeetingAbstractView',
    # 导出-export
    'ExportTranscriptionWordView',
    'ExportSummaryWordView',
    'ExportAbstractWordView',
    # 语音声纹-voiceprint
    'VoiceprintAddView',
    'VoiceprintListView',
    'VoiceprintRenameView',
    'VoiceprintDeleteView',
    # 用户管理-user
    'UserRegisterView',
    'UserLoginView',
    'UserLogoutView',
    'UserProfileView',
    # 文件管理-file
    'FileUploadView',
    'FileListView',
    'FileRenameView',
    'FileDeleteView',
    # 逐字稿-transcription
    'TranscriptionSearchView',
    'TranscriptionGetView',
    'TranscriptionEditView',
    'TranscriptionGenerateView',
    # 文件上传转录-upload_transcribe
    'FileUploadTranscribeView',
    # Prompt模板管理-prompt
    'PromptListView',
    'PromptAddView',
    'PromptUpdateView',
    'PromptDeleteView',
    'PromptCopyView',
]