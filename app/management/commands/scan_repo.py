# vulnerability_scanner/management/commands/scan_repo.py

import subprocess
import json
import os
import shutil # Used for cleanup/temp file handling
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

# Import your models
from app.models import ComplianceTarget, CheckResult 

class Command(BaseCommand):
    help = 'Runs Gitleaks against a local repository path and saves results to the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            'repo_path',
            type=str,
            help='The local path to the Git repository to scan.',
        )

    def handle(self, *args, **options):
        repo_path = options['repo_path']
        
        # Define a consistent, temporary file name for Gitleaks output
        output_file = 'gitleaks_scan_results.json'

        self.stdout.write(f"Starting scan process for repository: {repo_path}")

        # -----------------------------------------------------------------
        # 1. FETCH OR CREATE COMPLIANCETARGET (Handle Foreign Key)
        # -----------------------------------------------------------------
        try:
            # Use os.path.basename to get a friendly name from the path (e.g., 'my_repo' from /tmp/my_repo)
            friendly_name = os.path.basename(repo_path.rstrip(os.sep))
            
            target_object, created = ComplianceTarget.objects.get_or_create(
                # Look up by the unique repo_path
                repo_path=repo_path,
                defaults={
                    'name': friendly_name,
                    'resource_type': 'Git Repository'
                }
            )
            
            if created:
                self.stdout.write(self.style.NOTICE(f"Created new ComplianceTarget: {target_object.name}"))
            else:
                self.stdout.write(f"Using existing ComplianceTarget: {target_object.name}")
                
        except Exception as e:
            raise CommandError(f"Could not fetch or create ComplianceTarget for '{repo_path}': {e}")
        
        # -----------------------------------------------------------------
        # 2. CLEAR OLD 'IS_LATEST' FLAGS
        # -----------------------------------------------------------------
        # Mark all previous findings for this target as non-latest
        CheckResult.objects.filter(target=target_object, is_latest=True).update(is_latest=False)
        self.stdout.write(f"Cleared 'is_latest' flag for previous scans of {target_object.name}.")
        
        # -----------------------------------------------------------------
        # 3. EXECUTE GITLEAKS
        # -----------------------------------------------------------------
        gitleaks_command = [
            'gitleaks', 'detect', 
            f'--source={repo_path}', 
            '--report-format=json', 
            f'--report-path={output_file}',
            '--exit-code', '0' # Ensures the script continues even if secrets are found (Gitleaks returns code 1 on findings)
        ]
        
        try:
            self.stdout.write("Running Gitleaks...")
            # Run the command
            subprocess.run(gitleaks_command, check=True, capture_output=True, text=True)
            self.stdout.write(self.style.SUCCESS("Gitleaks scan finished successfully."))

        except subprocess.CalledProcessError as e:
             # This block usually catches environment issues, not findings (due to --exit-code 0)
             self.stderr.write(self.style.ERROR(f"Error during Gitleaks execution:\n{e.stderr}"))
             
        except FileNotFoundError:
             raise CommandError("Gitleaks command not found. Ensure it is installed and in your system's PATH.")


        # -----------------------------------------------------------------
        # 4. READ, PARSE, AND SAVE FINDINGS / RECORD SUCCESS
        # -----------------------------------------------------------------
        new_findings_count = 0
        
        # Check if the output file was generated (it usually is, even if empty)
        if not os.path.exists(output_file):
            self.stdout.write(self.style.NOTICE("No output file generated. This might indicate an issue or no findings."))
            # Create a 'Skipped' or 'Error' result if no file exists
            CheckResult.objects.create(
                target=target_object,
                status='ERROR', # or 'SKIP' if you want a separate status for this case
                rule_id='GITLEAKS_FILE_ERROR',
                is_latest=True,
                checked_at=timezone.now(),
                secret_snippet='Gitleaks output file not found after execution.',
            )
            return

        try:
            with open(output_file, 'r') as f:
                findings_data = json.load(f)
        except json.JSONDecodeError:
            raise CommandError(f"Failed to parse JSON output from Gitleaks file: {output_file}")
        
        # --- A. Process all findings (Failures) ---
        for finding in findings_data:
            CheckResult.objects.create(
                # Foreign Key
                target=target_object, 
                
                # Gitleaks Fields
                rule_id=finding.get('RuleID'),
                file_path=finding.get('File'),
                line_number=finding.get('StartLine', 0),
                commit_hash=finding.get('Commit'),
                author=finding.get('Author'),
                secret_snippet=finding.get('Secret'),

                # Compliance Fields
                status='FAIL',        # A finding always means a check failure
                is_latest=True,
                checked_at=timezone.now(),
            )
            new_findings_count += 1

        # --- B. Record a single successful check if NO findings were processed ---
        if new_findings_count == 0:
            # Create a single 'PASS' entry to indicate the successful, clean scan
            CheckResult.objects.create(
                target=target_object,
                status='PASS',        # Set status to PASS for zero findings
                rule_id='GITLEAKS_SCAN_COMPLETE',
                file_path='/',        # Use a generic file path for the overall scan result
                line_number=0,
                commit_hash='N/A',
                author='N/A',
                secret_snippet='Repository scan finished with 0 secrets found.',
                is_latest=True,
                checked_at=timezone.now(),
            )
            self.stdout.write(self.style.SUCCESS(f"Successfully recorded a clean scan for {target_object.name}."))

        else:
            self.stdout.write(self.style.WARNING(f"Successfully processed and saved {new_findings_count} security findings (FAILURES) for {target_object.name}."))
        
        # -----------------------------------------------------------------
        # 5. CLEANUP
        # -----------------------------------------------------------------
        os.remove(output_file)
        self.stdout.write(self.style.SUCCESS(f"Successfully processed and saved {new_findings_count} security findings for {target_object.name}."))
