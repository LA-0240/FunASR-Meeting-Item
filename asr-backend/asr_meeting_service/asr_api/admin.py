from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import messages
from .models import (
    User,
    AudioRecord,
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
    list_display = ('username', 'email', 'is_staff_display', 'is_superuser_display', 'file_count', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'created_at')
    search_fields = ('username', 'email')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    actions = ['make_staff', 'remove_staff']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('额外信息', {'fields': ('created_at', 'updated_at')}),
    )

    def file_count(self, obj):
        return obj.uploadedfile_set.count()
    file_count.short_description = '文件数量'

    def is_staff_display(self, obj):
        if obj.is_staff:
            return '✅ 是'
        return '❌ 否'
    is_staff_display.short_description = '管理员状态'

    def is_superuser_display(self, obj):
        if obj.is_superuser:
            return '✅ 是'
        return '❌ 否'
    is_superuser_display.short_description = '超级用户状态'

    @admin.action(description='设为管理员')
    def make_staff(self, request, queryset):
        updated = queryset.update(is_staff=True)
        self.message_user(request, f'成功将 {updated} 个用户设为管理员', messages.SUCCESS)

    @admin.action(description='取消管理员权限')
    def remove_staff(self, request, queryset):
        updated = queryset.update(is_staff=False)
        self.message_user(request, f'成功取消 {updated} 个用户的管理员权限', messages.SUCCESS)


admin.site.register(User, UserAdmin)


# ============== AudioRecord Admin ==============
@admin.register(AudioRecord)
class AudioRecordAdmin(admin.ModelAdmin):
    list_display = ('filename', 'file_size_display', 'upload_time')
    list_filter = ('upload_time',)
    search_fields = ('filename', 'transcription', 'summary')
    readonly_fields = ('upload_time',)
    ordering = ('-upload_time',)

    def file_size_display(self, obj):
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        else:
            return f"{obj.file_size / (1024 * 1024):.1f} MB"
    file_size_display.short_description = '文件大小'


# ============== Voiceprint Admin ==============
@admin.register(Voiceprint)
class VoiceprintAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at', 'updated_at')
    list_filter = ('user', 'created_at')
    search_fields = ('name', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


# ============== Inline Models ==============
class TranscriptionInline(admin.StackedInline):
    model = Transcription
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    verbose_name = '逐字稿'
    verbose_name_plural = '逐字稿'
    fieldsets = (
        ('逐字稿内容', {
            'fields': ('transcription_text', 'speaker_info'),
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


class MeetingSummaryInline(admin.StackedInline):
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
    list_display = (
        'original_name',
        'user',
        'file_type_display',
        'file_size_display',
        'status_display',
        'meeting_type',
        'upload_time',
    )
    list_filter = ('user', 'file_type', 'status', 'upload_time')
    search_fields = ('original_name', 'meeting_type', 'user__username')
    readonly_fields = ('stored_name', 'file_path', 'upload_time')
    inlines = [TranscriptionInline, MeetingSummaryInline, MeetingSegmentInline]
    ordering = ('-upload_time',)
    list_per_page = 20
    date_hierarchy = 'upload_time'
    actions = ['mark_as_processed', 'reset_to_original']

    def file_type_display(self, obj):
        if obj.file_type in ['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'] or 'video' in obj.file_type:
            return '🎬 视频'
        return '🎵 音频'
    file_type_display.short_description = '文件类型'

    def file_size_display(self, obj):
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        else:
            return f"{obj.file_size / (1024 * 1024):.1f} MB"
    file_size_display.short_description = '文件大小'

    def status_display(self, obj):
        if obj.status == 'processed':
            return '✅ 已处理'
        return '⏳ 原始'
    status_display.short_description = '状态'

    @admin.action(description='标记为已处理')
    def mark_as_processed(self, request, queryset):
        updated = queryset.update(status='processed')
        self.message_user(request, f'成功标记 {updated} 个文件为已处理', messages.SUCCESS)

    @admin.action(description='重置为原始状态')
    def reset_to_original(self, request, queryset):
        updated = queryset.update(status='original')
        self.message_user(request, f'成功重置 {updated} 个文件', messages.SUCCESS)


# ============== Transcription Admin ==============
@admin.register(Transcription)
class TranscriptionAdmin(admin.ModelAdmin):
    list_display = ('file', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('transcription_text', 'file__original_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 20


# ============== Prompt Admin ==============
@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'category_display', 'template_type_display', 'created_at', 'updated_at')
    list_filter = ('category', 'template_type', 'user', 'created_at')
    search_fields = ('name', 'system_prompt', 'user_prompt')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 20
    actions = ['duplicate_prompt', 'make_default']

    def category_display(self, obj):
        if obj.category == 'default':
            return '📋 默认'
        return '✏️ 自定义'
    category_display.short_description = '分类'

    def template_type_display(self, obj):
        if obj.template_type == 'summary':
            return '📝 纪要'
        return '📄 摘要'
    template_type_display.short_description = '模板类型'

    @admin.action(description='复制选中的模板')
    def duplicate_prompt(self, request, queryset):
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
        updated = queryset.update(category='default')
        self.message_user(request, f'成功将 {updated} 个模板设为默认', messages.SUCCESS)


# ============== MeetingSummary Admin ==============
@admin.register(MeetingSummary)
class MeetingSummaryAdmin(admin.ModelAdmin):
    list_display = ('file', 'is_customized_display', 'created_at', 'updated_at')
    list_filter = ('is_customized', 'created_at', 'updated_at')
    search_fields = ('summary_text', 'abstract_text', 'file__original_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    list_per_page = 20

    def is_customized_display(self, obj):
        if obj.is_customized:
            return '✏️ 已编辑'
        return '🤖 自动生成'
    is_customized_display.short_description = '是否自定义'


# ============== MeetingSegment Admin ==============
@admin.register(MeetingSegment)
class MeetingSegmentAdmin(admin.ModelAdmin):
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
        minutes = int(obj.start_time // 60)
        seconds = int(obj.start_time % 60)
        return f"{minutes:02d}:{seconds:02d}"
    start_time_display.short_description = '开始时间'

    def end_time_display(self, obj):
        minutes = int(obj.end_time // 60)
        seconds = int(obj.end_time % 60)
        return f"{minutes:02d}:{seconds:02d}"
    end_time_display.short_description = '结束时间'

    def is_edited_display(self, obj):
        if obj.is_edited:
            return '✏️ 已编辑'
        return '🤖 自动'
    is_edited_display.short_description = '是否编辑'


