# vulnerability_scanner/admin.py

from django.contrib import admin
# Assuming your models are in the same app's models.py
from .models import ComplianceTarget, CheckResult

# 1. Register ComplianceTarget so you can manage your repositories
@admin.register(ComplianceTarget)
class ComplianceTargetAdmin(admin.ModelAdmin):
    list_display = ('name', 'resource_type', 'repo_path', 'is_active')
    list_filter = ('resource_type', 'is_active')
    search_fields = ('name', 'repo_path')
    ordering = ('name',)

# 2. Update CheckResultAdmin for Gitleaks data
@admin.register(CheckResult)
class CheckResultAdmin(admin.ModelAdmin):
    # Display the most critical information in the list view
    list_display = (
        'target', 
        'rule_id',        # New Gitleaks field
        'file_path',      # New Gitleaks field
        'line_number',    # New Gitleaks field
        'status', 
        'checked_at', 
        'is_latest'
    )
    
    # Allow filtering by the rule found and the commit status
    list_filter = (
        'status', 
        'rule_id',        # New filter for the type of secret
        'is_latest', 
        'checked_at'
    )
    
    # Allow searching by repository, rule, and the secret/commit details
    search_fields = (
        'target__name', 
        'rule_id', 
        'file_path',
        'commit_hash',
        'author',
        'secret_snippet', # Search on the actual (potentially redacted) secret
    )
    
    # Order by target, then by the most recent scan time
    ordering = ('target__name', '-checked_at')
    
    # Fields to display on the individual CheckResult detail page
    fieldsets = (
        (None, {
            'fields': ('target', 'status', 'is_latest', 'checked_at'),
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