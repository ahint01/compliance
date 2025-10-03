# app/scan_service.py

import subprocess
import json
import os
from django.utils import timezone
from app.models import ComplianceTarget, CheckResult 
# NOTE: Add logging here instead of stdout/stderr for web app use

def run_gitleaks_scan(repo_path: str):
    """
    Core function to execute Gitleaks and record results.
    Returns: Tuple (target_name: str, findings_count: int, success: bool, message: str)
    """
    output_file = 'gitleaks_scan_results.json'

    # --- 1. FETCH OR CREATE COMPLIANCETARGET ---
    try:
        friendly_name = os.path.basename(repo_path.rstrip(os.sep))
        target_object, _ = ComplianceTarget.objects.get_or_create(
            repo_path=repo_path,
            defaults={'name': friendly_name}
        )
    except Exception as e:
        return target_object.name if 'target_object' in locals() else 'Unknown Repo', 0, False, f"DB Error: {e}"

    # --- 2. CLEAR OLD 'IS_LATEST' FLAGS ---
    CheckResult.objects.filter(target=target_object, is_latest=True).update(is_latest=False)
    
    # --- 3. EXECUTE GITLEAKS ---
    gitleaks_command = [
        'gitleaks', 'detect', 
        f'--source={repo_path}', 
        '--report-format=json', 
        f'--report-path={output_file}',
        '--exit-code', '0'
    ]
    
    try:
        subprocess.run(gitleaks_command, check=True, capture_output=True, text=True)
    except Exception as e:
         # Log the error and proceed to create an ERROR result if needed
         return target_object.name, 0, False, f"Gitleaks Execution Error: {str(e)[:100]}"
    
    # --- 4. READ, PARSE, AND SAVE FINDINGS / RECORD SUCCESS ---
    new_findings_count = 0
    
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r') as f:
                findings_data = json.load(f)
        except json.JSONDecodeError:
            return target_object.name, 0, False, f"Gitleaks JSON Parse Error."

        # Process findings (Logic is the same as your script)
        for finding in findings_data:
            CheckResult.objects.create(target=target_object, rule_id=finding.get('RuleID'), file_path=finding.get('File'), line_number=finding.get('StartLine', 0), commit_hash=finding.get('Commit'), author=finding.get('Author'), secret_snippet=finding.get('Secret'), status='FAIL', is_latest=True, checked_at=timezone.now())
            new_findings_count += 1
            
        # Record final PASS/FAIL result
        if new_findings_count == 0:
            CheckResult.objects.create(target=target_object, status='PASS', rule_id='GITLEAKS_SCAN_COMPLETE', file_path='/', line_number=0, commit_latest=True, checked_at=timezone.now(), secret_snippet='Repository scan finished with 0 secrets found.')
            message = "Scan complete: 0 findings recorded (PASS)."
        else:
            message = f"Scan complete: {new_findings_count} findings recorded (FAIL)."
    else:
        # No file generated
        message = "Scan failed to generate an output file."
        
    # --- 5. CLEANUP ---
    if os.path.exists(output_file):
        os.remove(output_file)

    return target_object.name, new_findings_count, True, message