import re
import json
import logging
from datetime import datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from django.db.models import Avg

from .models import (
    LoginAttempt, Task, SubTask,
    CalendarEvent, TimerSession, UserStreak,
)
from .forms import TaskForm


logger = logging.getLogger(__name__)

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
# LOGOUT
# ============================================================
@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


# ============================================================
# DASHBOARD
# ============================================================
@login_required
def dashboard_view(request):
    tasks = Task.objects.filter(user=request.user)

    category = request.GET.get("category")
    difficulty = request.GET.get("difficulty")
    sort = request.GET.get("sort", "default")

    if category:
        tasks = tasks.filter(category=category)
    if difficulty:
        tasks = tasks.filter(difficulty=difficulty)

    tasks = tasks.order_by("-priority", "-id") if sort == "priority" else tasks.order_by("-id")

    active_count = tasks.filter(completed=False).count()
    form = TaskForm()

    return render(request, "main/dashboard.html", {
        "tasks": tasks,
        "form": form,
        "active_count": active_count,
    })


# ============================================================
# TIMER PAGE
# ============================================================
@login_required
def timer_view(request):
    return render(request, "main/timer.html")


# ============================================================
# TASK CRUD + CALENDAR SYNC
# ============================================================
@login_required
def add_task(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user

            add_to_calendar = request.POST.get('add_to_calendar') == '1'
            task.add_to_calendar = add_to_calendar
            task.save()

            if add_to_calendar and task.due_date:
                event = CalendarEvent.objects.create(
                    user=request.user,
                    title=task.title,
                    description=f"Task: {task.title}",
                    event_date=task.due_date,
                    category=task.category,
                )
                event.color = event.get_category_color()
                event.save()
                task.linked_calendar_event = event
                task.save()

            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                html = render_to_string("main/partials/task_card.html", {"task": task}, request=request)
                return JsonResponse({"success": True, "task_html": html})

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors})

    return redirect("dashboard")


@login_required
def edit_task(request, task_id):
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        task = get_object_or_404(Task, id=task_id, user=request.user)
        old_event = task.linked_calendar_event

        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            add_to_calendar = request.POST.get("add_to_calendar") == "1"
            task.add_to_calendar = add_to_calendar
            form.save()

            if add_to_calendar and task.due_date:
                if old_event:
                    old_event.title = task.title
                    old_event.event_date = task.due_date
                    old_event.category = task.category
                    old_event.color = old_event.get_category_color()
                    old_event.save()
                else:
                    event = CalendarEvent.objects.create(
                        user=request.user,
                        title=task.title,
                        description=f"Task: {task.title}",
                        event_date=task.due_date,
                        category=task.category,
                    )
                    event.color = event.get_category_color()
                    event.save()
                    task.linked_calendar_event = event
                    task.save()

            elif old_event:
                task.linked_calendar_event = None
                task.save()

            html = render_to_string("main/partials/task_card.html", {"task": task}, request=request)
            return JsonResponse({"success": True, "task_html": html, "task_id": task.id})

        return JsonResponse({"success": False, "errors": form.errors})

    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)

    if task.linked_calendar_event:
        task.linked_calendar_event.delete()

    task.delete()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True, "task_id": task_id})

    return redirect("dashboard")


# ============================================================
# SUBTASK SYSTEM
# ============================================================
@login_required
def add_subtask(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)

    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        title = request.POST.get("title", "").strip()
        if not title:
            return JsonResponse({"success": False, "error": "Title required"})

        subtask = SubTask.objects.create(task=task, title=title)
        completed, total = task.subtask_progress()

        return JsonResponse({
            "success": True,
            "subtask_id": subtask.id,
            "title": subtask.title,
            "progress": {
                "completed": completed, "total": total,
                "percent": task.subtask_progress_percent()
            }
        })

    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def toggle_subtask(request, subtask_id):
    subtask = get_object_or_404(SubTask, id=subtask_id, task__user=request.user)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        subtask.completed = not subtask.completed
        subtask.save()

        task = subtask.task
        completed, total = task.subtask_progress()

        return JsonResponse({
            "success": True,
            "completed": subtask.completed,
            "subtask_id": subtask.id,
            "progress": {
                "completed": completed,
                "total": total,
                "percent": task.subtask_progress_percent()
            }
        })

    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def delete_subtask(request, subtask_id):
    subtask = get_object_or_404(SubTask, id=subtask_id, task__user=request.user)
    task = subtask.task

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        subtask.delete()
        completed, total = task.subtask_progress()

        return JsonResponse({
            "success": True,
            "subtask_id": subtask_id,
            "progress": {
                "completed": completed,
                "total": total,
                "percent": task.subtask_progress_percent()
            }
        })

    return JsonResponse({"success": False, "error": "Invalid request"})


# ============================================================
# TIMER + STREAK SYSTEM
# ============================================================
@login_required
@csrf_exempt
def save_session(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            session = TimerSession.objects.create(
                user=request.user,
                start_time=parse_datetime(data["startTime"]),
                end_time=parse_datetime(data["endTime"]),
                duration_minutes=data["duration"],
                mode=data["mode"],
                completed=True,
            )

            if data["mode"] == "focus":
                streak, _ = UserStreak.objects.get_or_create(user=request.user)
                streak.update_streak(session.start_time.date())

            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid method"})


@login_required
def get_timer_stats(request):
    today = timezone.now().date()

    streak_data, _ = UserStreak.objects.get_or_create(user=request.user)

    sessions = TimerSession.objects.filter(
        user=request.user, mode="focus", completed=True
    )

    avg_length = sessions.aggregate(avg=Avg("duration_minutes"))["avg"] or 0
    total_sessions = sessions.count()

    # Last 7 days
    daily_stats = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        day_sessions = sessions.filter(start_time__date=d)
        daily_stats.append({
            "date": d.strftime("%Y-%m-%d"),
            "minutes": sum(s.duration_minutes for s in day_sessions),
            "sessions": day_sessions.count(),
        })

    # Weekly / Monthly
    week_total = sum(s.duration_minutes for s in sessions.filter(start_time__date__gte=today - timedelta(days=6)))
    month_total = sum(s.duration_minutes for s in sessions.filter(start_time__date__gte=today.replace(day=1)))

    return JsonResponse({
        "streak": streak_data.current_streak,
        "longest_streak": streak_data.longest_streak,
        "daily_stats": daily_stats,
        "total_sessions": total_sessions,
        "average_session_minutes": round(avg_length, 1),
        "week_total_minutes": week_total,
        "month_total_minutes": month_total,
    })


# ============================================================
# CALENDAR SYSTEM (NEW)
# ============================================================
@login_required
def calendar_view(request):
    return render(request, "main/calendar.html")


@login_required
def get_events(request):
    year = int(request.GET.get("year", timezone.now().year))
    month = int(request.GET.get("month", timezone.now().month))

    def fmt(t):
        if t is None:
            return None
        return t.strftime("%H:%M")

    events = CalendarEvent.objects.filter(user=request.user)
    tasks = Task.objects.filter(user=request.user, due_date__isnull=False)

    result = []

    # Calendar events
    for e in events:
        result.append({
            "id": e.id,
            "title": e.title,
            "description": e.description,
            "date": e.event_date.strftime("%Y-%m-%d"),
            "start_time": fmt(e.start_time),
            "end_time": fmt(e.end_time),
            "category": e.category,
            "color": e.color,
            "type": "event",
            "reminder_enabled": e.reminder_enabled,
            "reminder_minutes_before": e.reminder_minutes_before,
            "is_recurring": e.is_recurring or (e.parent_event is not None),
        })

    # Tasks as calendar items
    for t in tasks:
        result.append({
            "id": t.id,
            "title": t.title,
            "date": t.due_date.strftime("%Y-%m-%d"),
            "category": t.category,
            "color": "#6366f1",
            "type": "task",
            "completed": t.completed,
        })

    return JsonResponse({"events": result})


# Helper for time parsing
def parse_time_field(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        try:
            return datetime.strptime(value, "%I:%M %p").time()
        except ValueError:
            return None


@login_required
@require_http_methods(["POST"])
def add_event(request):
    try:
        data = json.loads(request.body)

        start_time = parse_time_field(data.get("start_time"))
        end_time = parse_time_field(data.get("end_time"))
        category = data.get("category", "Other")

        # Determine color
        if data.get("color"):
            color = data["color"]
        else:
            tmp = CalendarEvent(category=category)
            color = tmp.get_category_color()

        event = CalendarEvent.objects.create(
            user=request.user,
            title=data["title"],
            description=data.get("description", ""),
            event_date=data["event_date"],
            start_time=start_time,
            end_time=end_time,
            category=category,
            color=color,
            reminder_enabled=data.get("reminder_enabled", False),
            reminder_minutes_before=data.get("reminder_minutes_before", 15),
            is_recurring=data.get("is_recurring", False),
            recurrence_pattern=data.get("recurrence_pattern"),
            recurrence_end_date=data.get("recurrence_end_date"),
        )

        # Create recurring instances
        if event.is_recurring and event.recurrence_end_date:
            curr = datetime.strptime(data["event_date"], "%Y-%m-%d").date()
            end = datetime.strptime(data["recurrence_end_date"], "%Y-%m-%d").date()
            pattern = data.get("recurrence_pattern", "weekly")

            while curr < end:
                if pattern == "daily":
                    curr += timedelta(days=1)
                elif pattern == "weekly":
                    curr += timedelta(weeks=1)
                elif pattern == "monthly":
                    month = curr.month + 1 if curr.month < 12 else 1
                    year = curr.year + (1 if curr.month == 12 else 0)
                    try:
                        curr = curr.replace(year=year, month=month)
                    except ValueError:
                        import calendar
                        curr = curr.replace(year=year, month=month, day=calendar.monthrange(year, month)[1])

                if curr <= end:
                    CalendarEvent.objects.create(
                        user=request.user,
                        title=event.title,
                        description=event.description,
                        event_date=curr,
                        start_time=start_time,
                        end_time=end_time,
                        category=event.category,
                        color=event.color,
                        reminder_enabled=event.reminder_enabled,
                        reminder_minutes_before=event.reminder_minutes_before,
                        parent_event=event,
                    )

        event.refresh_from_db()

        def fmt(t):
            return None if t is None else t.strftime("%H:%M")

        return JsonResponse({
            "success": True,
            "event": {
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "date": event.event_date.strftime("%Y-%m-%d"),
                "start_time": fmt(event.start_time),
                "end_time": fmt(event.end_time),
                "category": event.category,
                "color": event.color,
                "type": "event",
            }
        })

    except Exception as e:
        logger.error(f"Error adding event: {e}", exc_info=True)
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def edit_event(request, event_id):
    try:
        event = get_object_or_404(CalendarEvent, id=event_id, user=request.user)
        data = json.loads(request.body)

        event.title = data.get("title", event.title)
        event.description = data.get("description", event.description)
        event.event_date = data.get("event_date", event.event_date)
        event.start_time = parse_time_field(data.get("start_time"))
        event.end_time = parse_time_field(data.get("end_time"))

        old_category = event.category
        new_category = data.get("category", event.category)
        user_color = data.get("color")

        event.category = new_category

        if new_category != old_category:
            event.color = event.get_category_color()
        elif user_color:
            event.color = user_color

        event.reminder_enabled = data.get("reminder_enabled", event.reminder_enabled)
        event.reminder_minutes_before = data.get("reminder_minutes_before", event.reminder_minutes_before)

        event.save()

        # Update recurring instances
        if event.is_recurring:
            for inst in event.recurring_instances.all():
                inst.title = event.title
                inst.description = event.description
                inst.start_time = event.start_time
                inst.end_time = event.end_time
                inst.category = event.category
                inst.color = inst.get_category_color()
                inst.reminder_enabled = event.reminder_enabled
                inst.reminder_minutes_before = event.reminder_minutes_before
                inst.save()

        elif event.parent_event:
            parent = event.parent_event
            parent.title = event.title
            parent.description = event.description
            parent.start_time = event.start_time
            parent.end_time = event.end_time
            parent.category = event.category
            parent.color = parent.get_category_color()
            parent.reminder_enabled = event.reminder_enabled
            parent.reminder_minutes_before = event.reminder_minutes_before
            parent.save()

            for inst in parent.recurring_instances.all():
                inst.title = event.title
                inst.description = event.description
                inst.start_time = event.start_time
                inst.end_time = event.end_time
                inst.category = event.category
                inst.color = inst.get_category_color()
                inst.reminder_enabled = event.reminder_enabled
                inst.reminder_minutes_before = event.reminder_minutes_before
                inst.save()

        event.refresh_from_db()

        def fmt(t):
            return None if t is None else t.strftime("%H:%M")

        return JsonResponse({
            "success": True,
            "event": {
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "date": event.event_date.strftime("%Y-%m-%d"),
                "start_time": fmt(event.start_time),
                "end_time": fmt(event.end_time),
                "category": event.category,
                "color": event.color,
                "type": "event",
            }
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@login_required
@require_http_methods(["POST", "DELETE"])
def delete_event(request, event_id):
    try:
        event = get_object_or_404(CalendarEvent, id=event_id, user=request.user)

        if event.is_recurring:
            event.recurring_instances.all().delete()
            event.delete()
        elif event.parent_event:
            parent = event.parent_event
            parent.recurring_instances.all().delete()
            parent.delete()
        else:
            event.delete()

        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


# ============================================================
# DRAG-DROP MOVE EVENT
# ============================================================
@login_required
def reschedule_event(request, event_id):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid method"}, status=400)

    try:
        event = CalendarEvent.objects.get(id=event_id, user=request.user)
    except CalendarEvent.DoesNotExist:
        if CalendarEvent.objects.filter(id=event_id).exists():
            return JsonResponse({"status": "error", "message": "Event belongs to another user"}, status=403)
        return JsonResponse({"status": "error", "message": "Not found"}, status=404)

    try:
        data = json.loads(request.body)
        new_date = data.get("new_date")

        if not new_date:
            return JsonResponse({"status": "error", "message": "Missing date"}, status=400)

        event.event_date = new_date
        event.save()

        return JsonResponse({"status": "success"})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


# ============================================================
# TASK TOGGLE (COMPLETE / FAVORITE)
# ============================================================
@login_required
def toggle_complete(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)

    # Toggle task completion
    task.completed = not task.completed
    task.save()

    # Get all subtasks for this task
    subtasks = task.subtasks.all()

    if task.completed:
        # 🔥 MARK ALL SUBTASKS AS COMPLETED
        subtasks.update(completed=True)
    else:
        # 🔄 MARK ALL SUBTASKS AS INCOMPLETE
        subtasks.update(completed=False)

    # Calculate updated progress
    completed_count = subtasks.filter(completed=True).count()
    total_count = subtasks.count()
    percent = (completed_count / total_count * 100) if total_count > 0 else 0

    # AJAX response for your JS
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "completed": task.completed,
            "progress": {
                "completed": completed_count,
                "total": total_count,
                "percent": percent
            }
        })

    return redirect("dashboard")



@login_required
def toggle_favorite(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.favorite = not task.favorite
    task.save()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"success": True, "favorite": task.favorite})

    return redirect("dashboard")

@login_required
def get_subtasks(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        subtasks = task.subtasks.all()
        completed, total = task.subtask_progress()
        return JsonResponse({
            "success": True,
            "subtasks": [
                {"id": s.id, "title": s.title, "completed": s.completed}
                for s in subtasks
            ],
            "progress": {
                "completed": completed,
                "total": total,
                "percent": task.subtask_progress_percent()
            }
        })

    return JsonResponse({"success": False, "error": "Invalid request"})
