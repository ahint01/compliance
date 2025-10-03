import subprocess
import json
import os
import shutil
from django.utils import timezone
from app.models import CheckResult
import uuid

def run_gitleaks_scan(repo_url: str):
    """
    Clones a repo via URL, executes Gitleaks, records results, and cleans up.
    Returns: Tuple (repo_url: str, findings_count: int, success: bool, message: str)
    """
    unique_id = uuid.uuid4().hex
    repo_name = os.path.basename(repo_url.rstrip('/'))
    clone_dir = os.path.join('/tmp', f'scan_temp_{unique_id}_{repo_name}')
    output_file = os.path.join(clone_dir, 'gitleaks_scan_results.json')
    identifier = repo_url
    new_findings_count = 0
    message = "Scan incomplete."
    success = False

    try:
        os.makedirs(clone_dir, exist_ok=True)

        subprocess.run(
            ['git', 'clone', '--depth', '50', repo_url, clone_dir],
            check=True, capture_output=True, text=True, timeout=120
        )

        CheckResult.objects.filter(repo_path=identifier, is_latest=True).update(is_latest=False)

        gitleaks_command = [
            'gitleaks', 'detect',
            f'--source={clone_dir}',
            '--report-format=json',
            f'--report-path={output_file}',
            '--exit-code', '0'
        ]
        subprocess.run(gitleaks_command, check=True, capture_output=True, text=True)

        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                findings_data = json.load(f)

            for finding in findings_data:
                CheckResult.objects.create(
                    repo_path=identifier,
                    rule_id=finding.get('RuleID'),
                    file_path=finding.get('File'),
                    line_number=finding.get('StartLine', 0),
                    commit_hash=finding.get('Commit'),
                    author=finding.get('Author'),
                    secret_snippet=finding.get('Secret'),
                    status='FAIL',
                    is_latest=True,
                    checked_at=timezone.now()
                )
                new_findings_count += 1

            if new_findings_count == 0:
                CheckResult.objects.create(
                    repo_path=identifier,
                    status='PASS',
                    rule_id='GITLEAKS_SCAN_COMPLETE',
                    is_latest=True,
                    checked_at=timezone.now(),
                    file_path='/',
                    line_number=0,
                    commit_hash='N/A',
                    author='N/A',
                    secret_snippet='Clean scan.'
                )
                message = "Scan complete: 0 findings recorded (PASS)."
            else:
                message = f"Scan complete: {new_findings_count} findings recorded (FAIL)."
            success = True
        else:
            message = "Scan failed to generate an output file."

    except subprocess.CalledProcessError as e:
        message = f"Execution Error during cloning or Gitleaks run: {e.stderr.strip() or e.stdout.strip()}"
    except Exception as e:
        message = f"General Error: {str(e)}"

    finally:
        if os.path.exists(clone_dir):
            shutil.rmtree(clone_dir)

    return identifier, new_findings_count, success, message