import json
import os
import subprocess
import tempfile

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from app.models import CheckResult


class Command(BaseCommand):
    help = "Run Gitleaks against a local repository path and save results to the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "repo_path",
            type=str,
            help="Local path to the Git repository to scan.",
        )

    def handle(self, *args, **options):
        repo_path = os.path.abspath(options["repo_path"])

        if not os.path.isdir(repo_path):
            raise CommandError(f"Repository path does not exist: {repo_path}")

        if not os.path.isdir(os.path.join(repo_path, ".git")):
            raise CommandError(f"Not a Git repository: {repo_path}")

        self.stdout.write(f"Scanning repository: {repo_path}")

        CheckResult.objects.filter(repo_path=repo_path, is_latest=True).update(
            is_latest=False
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as output:
            output_file = output.name

        try:
            try:
                subprocess.run(
                    [
                        "gitleaks",
                        "detect",
                        f"--source={repo_path}",
                        "--report-format=json",
                        f"--report-path={output_file}",
                        "--exit-code",
                        "0",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                raise CommandError(
                    f"Gitleaks failed: {e.stderr.strip() or e.stdout.strip()}"
                ) from e
            except FileNotFoundError as e:
                raise CommandError(
                    "Gitleaks not found. Install it and ensure it is on your PATH."
                ) from e

            new_findings_count = 0

            if os.path.exists(output_file):
                with open(output_file, encoding="utf-8") as f:
                    findings_data = json.load(f)

                for finding in findings_data:
                    CheckResult.objects.create(
                        repo_path=repo_path,
                        rule_id=finding.get("RuleID"),
                        file_path=finding.get("File"),
                        line_number=finding.get("StartLine", 0),
                        commit_hash=finding.get("Commit"),
                        author=finding.get("Author"),
                        secret_snippet=finding.get("Secret"),
                        status="FAIL",
                        is_latest=True,
                        checked_at=timezone.now(),
                    )
                    new_findings_count += 1

            if new_findings_count == 0:
                CheckResult.objects.create(
                    repo_path=repo_path,
                    status="PASS",
                    rule_id="GITLEAKS_SCAN_COMPLETE",
                    is_latest=True,
                    checked_at=timezone.now(),
                    file_path="/",
                    line_number=0,
                    commit_hash="N/A",
                    author="N/A",
                    secret_snippet="Clean scan.",
                )
                self.stdout.write(
                    self.style.SUCCESS("Scan complete: no secrets found (PASS).")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Scan complete: {new_findings_count} finding(s) recorded (FAIL)."
                    )
                )
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)
