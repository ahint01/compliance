from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CheckResult
from .scan_service import run_gitleaks_scan

def dashboard_view(request):
    if request.method == 'POST':
        repo_url = request.POST.get('repo_url')
        if repo_url:
            repo_url_result, count, success, message = run_gitleaks_scan(repo_url)
            if success:
                messages.success(request, f"Scan of {repo_url_result} successful. {message}")
            else:
                messages.error(request, f"Scan of {repo_url_result} failed. {message}")
        return redirect('dashboard')
    else:
        results = CheckResult.objects.filter(is_latest=True).order_by('-checked_at')
        context = {
            'check_results': results,
            'public_ip': request.get_host().split(':')[0]
        }
        return render(request, 'app/dashboard.html', context)