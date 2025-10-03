from django.db import models
from django.utils import timezone

STATUS_CHOICES = [
('PASS', 'Compliance Passed'),
('FAIL', 'Compliance Failed'),
('SKIP', 'Check Skipped'),
]

class CheckResult(models.Model):
    repo_path = models.CharField(
        max_length=500,
        help_text="The local file path of the repository that was scanned."
    )
    rule_id = models.CharField(
        max_length=100,
        help_text="The Gitleaks rule ID that matched the secret."
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='FAIL')
    details = models.TextField(blank=True, null=True, help_text="Full technical details or full Gitleaks JSON finding (optional).")
    checked_at = models.DateTimeField(default=timezone.now, db_index=True)
    is_latest = models.BooleanField(default=True, help_text="True if this is the most recent check.")
    file_path = models.CharField(max_length=500, help_text="The file path where the secret was found.")
    line_number = models.IntegerField(help_text="The line number.")
    commit_hash = models.CharField(max_length=40, help_text="The SHA-1 hash of the commit.")
    author = models.CharField(max_length=100, help_text="The author of the commit.")
    secret_snippet = models.TextField(help_text="A snippet of the leaked secret.")


    def __str__(self):
        return f"[{self.status}] {self.rule_id} in {self.repo_path} ({self.file_path}:{self.line_number})"

    class Meta:
        indexes = [
            models.Index(fields=['repo_path', 'checked_at']),
        ]