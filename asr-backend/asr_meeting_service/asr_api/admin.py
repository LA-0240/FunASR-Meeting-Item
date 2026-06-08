"""
Django管理后台配置模块
配置所有模型在管理后台的展示和管理功能
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import messages
from .models import (
    User,
    AudioRecord,
    Speaker,
    Voiceprint,
    UploadedFile,
    Transcription,
    Prompt,
    MeetingSummary,
    MeetingSegment,
)


# ============== Admin 站点配置 ==============
admin.site.site_header = '🎙️ 智能会议纪要系统 - 管理后台'
admin.site.site_title = '智能会议纪要系统'
admin.site.index_title = '欢迎使用管理后台'


# ============== User Admin ==============
class UserAdmin(BaseUserAdmin):
    """用户管理后台配置"""
    list_display = (
        'username',
        'email',
        'is_staff_display',
        'is_superuser_display',
        'file_count',
        'speaker_count',
        'voiceprint_count',
        'created_at',
    )
    list_filter = ('is_staff', 'is_superuser', 'created_at')
    search_fields = ('username', 'email')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    actions = ['make_staff', 'remove_staff']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('额外信息', {'fields': ('avatar', 'created_at', 'updated_at')}),
    )

    def speaker_count(self, obj):
        """获取说话人数量"""
        return obj.speaker_set.count()
    speaker_count.short_description = '说话人数量'

    def voiceprint_count(self, obj):
        """获取声纹总数"""
        return obj.voiceprint_set.count()
    voiceprint_count.short_description = '声纹总数'

    def file_count(self, obj):
        """获取文件数量"""
        return obj.uploadedfile_set.count()
    file_count.short_description = '文件数量'

    def is_staff_display(self, obj):
        """显示管理员状态"""
        if obj.is_staff:
            return '✅ 是'
        return '❌ 否'
    is_staff_display.short_description = '管理员状态'

    def is_superuser_display(self, obj):
        """显示超级用户状态"""
        if obj.is_superuser:
            return '✅ 是'
        return '❌ 否'
    is_superuser_display.short_description = '超级用户状态'

    @admin.action(description='设为管理员')
    def make_staff(self, request, queryset):
        """批量设为管理员"""
        updated = queryset.update(is_staff=True)
        self.message_user(request, f'成功将 {updated} 个用户设为管理员', messages.SUCCESS)

    @admin.action(description='取消管理员权限')
    def remove_staff(self, request, queryset):
        """批量取消管理员权限"""
        updated = queryset.update(is_staff=False)
        self.message_user(request, f'成功取消 {updated} 个用户的管理员权限', messages.SUCCESS)


admin.site.register(User, UserAdmin)


# ============== AudioRecord Admin ==============
@admin.register(AudioRecord)
class AudioRecordAdmin(admin.ModelAdmin):
    """音频记录管理后台配置"""
    list_display = ('filename', 'file_size_display', 'upload_time')
    list_filter = ('upload_time',)
    search_fields = ('filename', 'transcription', 'summary')
    readonly_fields = ('upload_time',)
    ordering = ('-upload_time',)

    def file_size_display(self, obj):
        """格式化显示文件大小"""
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        else:
            return f"{obj.file_size / (1024 * 1024):.1f} MB"
    file_size_display.short_description = '文件大小'


# ============== Speaker Admin ==============
class VoiceprintInline(admin.TabularInline):
    """声纹内联编辑"""
    model = Voiceprint
    extra = 0
    readonly_fields = ('created_at', 'updated_at', 'source_type')
    fields = ('audio_file', 'source_type', 'source_meeting', 'created_at')
    ordering = ('-created_at',)
    verbose_name = '声纹'
    verbose_name_plural = '声纹列表'
    show_change_link = True


@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    """说话人管理后台配置"""
    list_display = ('name', 'user', 'avatar_display', 'voiceprint_count', 'manual_count', 'auto_count', 'created_at', 'updated_at')
    list_display_links = ('name',)
    list_filter = ('user', 'created_at')
    search_fields = ('name', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    inlines = [VoiceprintInline]
    list_per_page = 20
    date_hierarchy = 'created_at'

    def avatar_display(self, obj):
        """显示头像状态"""
        if obj.avatar:
            return '✅ 有头像'
        return '❌ 无头像'
    avatar_display.short_description = '头像状态'

    def voiceprint_count(self, obj):
        """显示声纹总数"""
        return obj.voiceprints.count()
    voiceprint_count.short_description = '声纹总数'

    def manual_count(self, obj):
        """显示手动注册声纹数量"""
        return obj.voiceprints.filter(source_type='manual').count()
    manual_count.short_description = '手动注册'

    def auto_count(self, obj):
        """显示会议自动采集声纹数量"""
        return obj.voiceprints.filter(source_type='auto').count()
    auto_count.short_description = '会议自动'


# ============== Voiceprint Admin ==============
@admin.register(Voiceprint)
class VoiceprintAdmin(admin.ModelAdmin):
    """声纹管理后台配置"""
    list_display = ('speaker_display', 'user', 'source_type_display', 'audio_file_status', 'source_meeting_display', 'created_at')
    list_display_links = ('speaker_display',)
    list_filter = ('speaker', 'user', 'source_type', 'created_at')
    search_fields = ('name', 'user__username', 'speaker__name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 20
    date_hierarchy = 'created_at'
    list_select_related = ('speaker', 'user', 'source_meeting')
    fieldsets = (
        ('基本信息', {'fields': ('speaker', 'user', 'name', 'avatar')}),
        ('声纹数据', {'fields': ('audio_file', 'file_path', 'feature')}),
        ('来源信息', {'fields': ('source_type', 'source_meeting')}),
        ('时间信息', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def speaker_display(self, obj):
        """显示关联的说话人"""
        if obj.speaker:
            return f'👤 {obj.speaker.name}'
        return '❌ 未关联'
    speaker_display.short_description = '说话人'
    speaker_display.admin_order_field = 'speaker__name'

    def source_type_display(self, obj):
        """显示来源类型"""
        if obj.source_type == 'manual':
            return '✏️ 手动注册'
        return '📹 会议自动'
    source_type_display.short_description = '来源类型'
    source_type_display.admin_order_field = 'source_type'

    def audio_file_status(self, obj):
        """显示音频文件状态"""
        if obj.audio_file:
            return '✅ 有音频'
        return '❌ 无音频'
    audio_file_status.short_description = '音频状态'

    def source_meeting_display(self, obj):
        """显示来源会议"""
        if obj.source_meeting:
            return f'📁 {obj.source_meeting.original_name[:20]}...'
        return '-'
    source_meeting_display.short_description = '来源会议'


# ============== Inline Models ==============
class TranscriptionInline(admin.StackedInline):
    """逐字稿内联编辑"""
    model = Transcription
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    verbose_name = '逐字稿'
    verbose_name_plural = '逐字稿'
    fieldsets = (
        ('逐字稿内容', {
            'fields': ('transcription_text', 'segments'),
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


class MeetingSummaryInline(admin.StackedInline):
    """会议纪要内联编辑"""
    model = MeetingSummary
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    verbose_name = '会议纪要'
    verbose_name_plural = '会议纪要'
    fieldsets = (
        ('纪要内容', {
            'fields': ('summary_text', 'abstract_text', 'is_customized'),
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


class MeetingSegmentInline(admin.TabularInline):
    """会议分段内联编辑"""
    model = MeetingSegment
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    verbose_name = '会议分段'
    verbose_name_plural = '会议分段列表'
    fields = ('segment_index', 'start_time', 'end_time', 'title', 'is_edited')
    ordering = ('segment_index',)


# ============== UploadedFile Admin (核心) ==============
@admin.register(UploadedFile)
class UploadedFileAdmin(admin.ModelAdmin):
    """上传文件管理后台配置"""
    list_display = (
        'original_name',
        'user',
        'file_type_display',
        'file_size_display',
        'status_display',
        'meeting_type',
        'has_transcription',
        'has_summary',
        'upload_time',
    )
    list_filter = ('user', 'file_type', 'status', 'upload_time', 'meeting_type')
    search_fields = ('original_name', 'meeting_type', 'user__username')
    readonly_fields = ('stored_name', 'file_path', 'upload_time')
    inlines = [TranscriptionInline, MeetingSummaryInline, MeetingSegmentInline]
    ordering = ('-upload_time',)
    list_per_page = 20
    date_hierarchy = 'upload_time'
    actions = ['mark_as_processed', 'reset_to_original', 'download_file']

    def has_transcription(self, obj):
        """检查是否有逐字稿"""
        return hasattr(obj, 'transcription')
    has_transcription.short_description = '逐字稿'
    has_transcription.boolean = True

    def has_summary(self, obj):
        """检查是否有会议纪要"""
        return hasattr(obj, 'meetingsummary')
    has_summary.short_description = '会议纪要'
    has_summary.boolean = True

    @admin.action(description='下载选中的文件')
    def download_file(self, request, queryset):
        """下载选中文件"""
        self.message_user(request, '下载功能需在前端实现', messages.INFO)

    def file_type_display(self, obj):
        """显示文件类型"""
        if obj.file_type in ['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'] or 'video' in obj.file_type:
            return '🎬 视频'
        return '🎵 音频'
    file_type_display.short_description = '文件类型'

    def file_size_display(self, obj):
        """格式化显示文件大小"""
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        else:
            return f"{obj.file_size / (1024 * 1024):.1f} MB"
    file_size_display.short_description = '文件大小'

    def status_display(self, obj):
        """显示文件处理状态"""
        if obj.status == 'processed':
            return '✅ 已处理'
        return '⏳ 原始'
    status_display.short_description = '状态'

    @admin.action(description='标记为已处理')
    def mark_as_processed(self, request, queryset):
        """批量标记为已处理"""
        updated = queryset.update(status='processed')
        self.message_user(request, f'成功标记 {updated} 个文件为已处理', messages.SUCCESS)

    @admin.action(description='重置为原始状态')
    def reset_to_original(self, request, queryset):
        """批量重置为原始状态"""
        updated = queryset.update(status='original')
        self.message_user(request, f'成功重置 {updated} 个文件', messages.SUCCESS)


# ============== Transcription Admin ==============
@admin.register(Transcription)
class TranscriptionAdmin(admin.ModelAdmin):
    """逐字稿管理后台配置"""
    list_display = ('file', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('transcription_text', 'file__original_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 20


# ============== Prompt Admin ==============
@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    """Prompt模板管理后台配置"""
    list_display = ('name', 'user', 'category_display', 'template_type_display', 'created_at', 'updated_at')
    list_filter = ('category', 'template_type', 'user', 'created_at')
    search_fields = ('name', 'system_prompt', 'user_prompt')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 20
    actions = ['duplicate_prompt', 'make_default']

    def category_display(self, obj):
        """显示分类"""
        if obj.category == 'default':
            return '📋 默认'
        return '✏️ 自定义'
    category_display.short_description = '分类'

    def template_type_display(self, obj):
        """显示模板类型"""
        if obj.template_type == 'summary':
            return '📝 纪要'
        return '📄 摘要'
    template_type_display.short_description = '模板类型'

    @admin.action(description='复制选中的模板')
    def duplicate_prompt(self, request, queryset):
        """批量复制模板"""
        for prompt in queryset:
            Prompt.objects.create(
                user=prompt.user,
                name=f'{prompt.name} (副本)',
                system_prompt=prompt.system_prompt,
                user_prompt=prompt.user_prompt,
                category='custom',
                template_type=prompt.template_type
            )
        self.message_user(request, f'成功复制 {queryset.count()} 个模板', messages.SUCCESS)

    @admin.action(description='设为默认模板')
    def make_default(self, request, queryset):
        """批量设为默认模板"""
        updated = queryset.update(category='default')
        self.message_user(request, f'成功将 {updated} 个模板设为默认', messages.SUCCESS)


# ============== MeetingSummary Admin ==============
@admin.register(MeetingSummary)
class MeetingSummaryAdmin(admin.ModelAdmin):
    """会议纪要管理后台配置"""
    list_display = ('file', 'is_customized_display', 'created_at', 'updated_at')
    list_filter = ('is_customized', 'created_at', 'updated_at')
    search_fields = ('summary_text', 'abstract_text', 'file__original_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 20

    def is_customized_display(self, obj):
        """显示是否自定义"""
        if obj.is_customized:
            return '✏️ 已编辑'
        return '🤖 自动生成'
    is_customized_display.short_description = '是否自定义'


# ============== MeetingSegment Admin ==============
@admin.register(MeetingSegment)
class MeetingSegmentAdmin(admin.ModelAdmin):
    """会议分段管理后台配置"""
    list_display = (
        'file',
        'segment_index',
        'title',
        'start_time_display',
        'end_time_display',
        'is_edited_display',
    )
    list_filter = ('file', 'is_edited', 'created_at')
    search_fields = ('title', 'content', 'summary', 'file__original_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('file', 'segment_index')
    list_per_page = 20

    def start_time_display(self, obj):
        """格式化显示开始时间"""
        minutes = int(obj.start_time // 60)
        seconds = int(obj.start_time % 60)
        return f"{minutes:02d}:{seconds:02d}"
    start_time_display.short_description = '开始时间'

    def end_time_display(self, obj):
        """格式化显示结束时间"""
        minutes = int(obj.end_time // 60)
        seconds = int(obj.end_time % 60)
        return f"{minutes:02d}:{seconds:02d}"
    end_time_display.short_description = '结束时间'

    def is_edited_display(self, obj):
        """显示是否已编辑"""
        if obj.is_edited:
            return '✏️ 已编辑'
        return '🤖 自动'
    is_edited_display.short_description = '是否编辑'


