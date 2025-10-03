from django.db import models
from django.utils import timezone

class ComplianceTarget(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="A unique, human-readable name for this target (e.g., 'Core Application Repo')."
    )

    resource_type = models.CharField(
        max_length=50,
        default='Git Repository', # Set a default for this specific project type
        help_text="The type of resource being checked (e.g., 'Git Repository', 'AWS S3', 'K8s')."
    )

    # CRITICAL CHANGE: Rename and clarify the purpose for Gitleaks
    repo_path = models.CharField(
        max_length=500,
        unique=True,
        # This is the path passed to your management command (e.g., /tmp/repo_clone or git URL)
        help_text="The local file path or URL of the repository to be scanned by Gitleaks."
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Set to False to exclude this target from future scans."
    )

    def __str__(self):
        return self.name



STATUS_CHOICES = [
('PASS', 'Compliance Passed'),
('FAIL', 'Compliance Failed'),
('SKIP', 'Check Skipped'),
]

class CheckResult(models.Model):
    # --- Existing Fields (Modified for Clarity) ---
    target = models.ForeignKey(ComplianceTarget, on_delete=models.CASCADE, help_text="The repository that was scanned.")

    # Changed from 'ruleid' to 'rule_id' for standard Python style and clarity
    rule_id = models.CharField(
        max_length=100, 
        help_text="The Gitleaks rule ID that matched the secret (e.g., 'GitHub-Token', 'AWS-Key')."
    )
    
    # Still useful, 'FAIL' for a secret found, 'PASS' if rule was run and nothing was found (less common)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='FAIL')
    
    # Used to store the full Gitleaks result or extra context
    details = models.TextField(
        blank=True, 
        null=True, 
        help_text="Full technical details or full Gitleaks JSON finding (optional)."
    )
    
    checked_at = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Still useful for filtering to the most recent scan
    is_latest = models.BooleanField(
        default=True, 
        help_text="True if this is the most recent check for this target."
    )
    
    # --- NEW GITLEAKS-SPECIFIC FIELDS ---
    
    file_path = models.CharField(
        max_length=500, 
        help_text="The file path in the repository where the secret was found."
    )
    
    line_number = models.IntegerField(
        help_text="The line number in the file where the secret was found."
    )
    
    commit_hash = models.CharField(
        max_length=40, 
        help_text="The SHA-1 hash of the commit that introduced the secret."
    )
    
    author = models.CharField(
        max_length=100, 
        help_text="The author of the commit that introduced the secret."
    )
    
    secret_snippet = models.TextField(
        help_text="A snippet of the leaked secret (often redacted by Gitleaks)."
    )


    def __str__(self):
        return f"[{self.status}] {self.rule_id} in {self.target.name} ({self.file_path}:{self.line_number})"

    class Meta:
        # A good index for querying recent findings
        indexes = [
            models.Index(fields=['target', 'checked_at']),
        ]
