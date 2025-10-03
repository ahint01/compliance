from django.shortcuts import render, redirect # We need redirect for POST-redirect-GET pattern
from django.contrib import messages # Used for showing success/error messages
from .models import CheckResult, ComplianceTarget 
from .scan_service import run_gitleaks_scan # 🌟 NEW IMPORT 🌟

def dashboard_view(request):
    
    # --- A. Handle Form Submission (POST Request) ---
    if request.method == 'POST':
        repo_path = request.POST.get('repo_path')
        if repo_path:
            # Execute the core scanning logic
            target_name, count, success, message = run_gitleaks_scan(repo_path)
            
            # Use Django's messages framework to notify the user
            if success:
                messages.success(request, f"Scan of {target_name} successful. {message}")
            else:
                messages.error(request, f"Scan of {target_name} failed. {message}")

        # Always redirect after a POST to prevent duplicate submissions
        return redirect('dashboard') 

    # --- B. Handle Display (GET Request) ---
    else:
        results = CheckResult.objects.filter(is_latest=True).order_by('-checked_at')
        targets = ComplianceTarget.objects.all().order_by('name')
        
        context = {
            'check_results': results,
            'compliance_targets': targets,
            'public_ip': request.get_host().split(':')[0]
        }
        return render(request, 'app/dashboard.html', context)