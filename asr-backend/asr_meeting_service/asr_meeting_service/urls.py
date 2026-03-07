"""
URL configuration for asr_meeting_service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from asr_api.views import (
    HealthCheckView,
    ASRTranscribeView,
    MeetingSummaryView,
    MeetingAbstractView,
    ExportTranscriptionWordView,
    ExportSummaryWordView,
    ExportAbstractWordView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # 基础接口
    path('', HealthCheckView.as_view(), name='health-check'),
    # ASR语音转文字
    path('asr', ASRTranscribeView.as_view(), name='asr-transcribe'),
    # 会议纪要生成
    path('generate_summary', MeetingSummaryView.as_view(), name='generate-summary'),
    # 会议摘要（新增）
    path("meeting_abstract", MeetingAbstractView.as_view(), name="meeting-abstract"),
    # Word导出（转录文本）
    path('export_transcription_word', ExportTranscriptionWordView.as_view(), name='export-transcription-word'),
    # Word导出（会议纪要）
    path('export_summary_word', ExportSummaryWordView.as_view(), name='export-summary-word'),
    # Word导出（会议摘要）
    path('export_abstract_word', ExportAbstractWordView.as_view(), name='export-abstract-word'),
]