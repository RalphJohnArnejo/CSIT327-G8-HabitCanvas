import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required

from .models import LoginAttempt, Task
from .forms import TaskForm


# ============================================================
# LANDING PAGE
# ============================================================
def landing_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "main/landing.html")


# ============================================================
# REGISTER
# ============================================================
def register_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not re.match(r'^[a-zA-Z0-9._%+-]+@(gmail\.com|yahoo\.com|outlook\.com|cit\.edu)$', email):
            return render(request, "main/register.html", {
                "error": "Email must be @gmail.com, @yahoo.com, @outlook.com, or @cit.edu"
            })

        if not re.search(r'[A-Z]', password) or not re.search(r'[!@#$%^&*()_+{}\[\]:;<>,.?~\-]', password):
            return render(request, "main/register.html", {
                "error": "Password must contain at least 1 uppercase letter and 1 special character"
            })

        if User.objects.filter(username=email).exists():
            return render(request, "main/register.html", {"error": "User already exists"})

        User.objects.create_user(username=email, email=email, password=password)
        return redirect("login")

    return render(request, "main/register.html")


# ============================================================
# LOGIN
# ============================================================
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        remember_me = request.POST.get("remember_me")

        user = authenticate(request, username=email, password=password)
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]

        if user:
            login(request, user)
            LoginAttempt.objects.create(
                user=user,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True,
                timestamp=timezone.now()
            )
            request.session.set_expiry(2592000 if remember_me else 0)
            return redirect("dashboard")

        LoginAttempt.objects.create(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            timestamp=timezone.now()
        )
        return render(request, "main/login.html", {"error": "Invalid credentials"})

    return render(request, "main/login.html")


# ============================================================
# DASHBOARD
# ============================================================
@login_required
def dashboard_view(request):
    tasks = Task.objects.filter(user=request.user)

    # --- FILTERS ---
    category = request.GET.get("category")
    difficulty = request.GET.get("difficulty")
    sort = request.GET.get("sort", "default")

    if category:
        tasks = tasks.filter(category=category)
    if difficulty:
        tasks = tasks.filter(difficulty=difficulty)

    # --- SORTING ---
    if sort == "priority":
        tasks = tasks.order_by("-priority", "-id")  # High priority first
    else:
        tasks = tasks.order_by("-id")  # Default: newest first

    # --- OTHER CONTEXT ---
    active_count = tasks.filter(completed=False).count()
    form = TaskForm()

    context = {
        "tasks": tasks,
        "form": form,
        "active_count": active_count,
    }
    return render(request, "main/dashboard.html", context)





# ============================================================
# LOGOUT
# ============================================================
@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


# ============================================================
# TASK ACTIONS
# ============================================================

@login_required
def add_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()

            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                task_html = render_to_string("main/partials/task_card.html", {"task": task}, request=request)
                return JsonResponse({"success": True, "task_html": task_html})

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors})

    return redirect("dashboard")


@login_required
def edit_task(request, task_id):
    """
    Edit Task via AJAX modal. Expects POST with form data.
    Returns JSON with updated task card HTML.
    """
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        task = get_object_or_404(Task, id=task_id, user=request.user)
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            task_html = render_to_string("main/partials/task_card.html", {"task": task}, request=request)
            return JsonResponse({"success": True, "task_html": task_html, "task_id": task.id})
        else:
            return JsonResponse({"success": False, "errors": form.errors})

    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True, "task_id": task_id})
    return redirect("dashboard")


@login_required
def toggle_complete(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.completed = not task.completed
    task.save()
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True, "completed": task.completed, "task_id": task.id})
    return redirect("dashboard")


@login_required
def toggle_favorite(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.favorite = not task.favorite
    task.save()
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True, "favorite": task.favorite, "task_id": task.id})
    return redirect("dashboard")
