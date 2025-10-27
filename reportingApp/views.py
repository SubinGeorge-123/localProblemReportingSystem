from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import IssueForm
from .models import Issue
from django.contrib import messages
from django.views.decorators.cache import never_cache
from .forms import IssueForm
from .models import Issue

@never_cache
@login_required(login_url='login')
def dashboard(request):
    user = request.user
    if user.is_superuser:
        issues = Issue.objects.all().order_by('-created_at')
    else:
        issues = Issue.objects.filter(user=user).order_by('-created_at')
    return render(request, 'dashboard.html', {'issues': issues})


@login_required(login_url='login')
def create_issue(request):
    if request.method == 'POST':
        form = IssueForm(request.POST, request.FILES)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.user = request.user
            issue.save()
            messages.success(request, 'Issue created successfully!')
            return redirect('dashboard')
    else:
        form = IssueForm()
    return render(request, 'create_issue.html', {'form': form})

@login_required(login_url='login')
def update_issue(request, issue_id):
    if request.user.is_superuser:
        issue = get_object_or_404(Issue, id=issue_id)
    else:
        issue = get_object_or_404(Issue, id=issue_id, user=request.user)

    if request.user.is_superuser:
        class AdminIssueForm(IssueForm):
            class Meta(IssueForm.Meta):
                fields = IssueForm.Meta.fields + ['status']
        form_class = AdminIssueForm
    else:
        form_class = IssueForm

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, instance=issue)
        if form.is_valid():
            form.save()
            messages.success(request, 'Issue updated successfully!')
            return redirect('dashboard')
    else:
        form = form_class(instance=issue)

    return render(request, 'update_issue.html', {'form': form, 'issue': issue})


@login_required(login_url='login')
def delete_issue(request, issue_id):
    if request.user.is_superuser:
        issue = get_object_or_404(Issue, id=issue_id)
    else:
        issue = get_object_or_404(Issue, id=issue_id, user=request.user)

    if request.method == 'POST':
        issue.delete()
        messages.success(request, 'Issue deleted successfully!')
        return redirect('dashboard')

    return render(request, 'delete_issue.html', {'issue': issue})
