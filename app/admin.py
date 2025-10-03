from django.contrib import admin
from .models import CheckResult
@admin.register(CheckResult)
class CheckResultAdmin(admin.ModelAdmin):
    list_display = (
        'repo_path',
        'rule_id',
        'file_path',
        'line_number',
        'status',
        'checked_at',
        'is_latest'
    )

    list_filter = (
        'status',
        'rule_id',
        'is_latest',
        'checked_at'
    )

    search_fields = (
        'repo_path',
        'rule_id',
        'file_path',
        'commit_hash',
        'author',
        'secret_snippet',
    )

    ordering = ('repo_path', '-checked_at')

    fieldsets = (
        (None, {
            'fields': ('repo_path', 'status', 'is_latest', 'checked_at'),
        }),
        ('Vulnerability Details', {
            'fields': (
                'rule_id',
                'file_path',
                'line_number',
                'commit_hash',
                'author',
                'secret_snippet',
                'details'
            ),
        }),
    )