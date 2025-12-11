import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from .models import LoginAttempt, Task, CalendarEvent, TimerSession, UserStreak, SubTask
from .forms import TaskForm, CalendarEventForm


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
        tasks = tasks.order_by("-priority", "-id")
    else:
        tasks = tasks.order_by("-id")

    active_count = tasks.filter(completed=False).count()
    form = TaskForm()

    context = {
        "tasks": tasks,
        "form": form,
        "active_count": active_count,
    }
    return render(request, "main/dashboard.html", context)


# ============================================================
# TIMER PAGE (NEW)
# ============================================================
@login_required
def timer_view(request):
    """Renders the Pomodoro Timer page."""
    return render(request, "main/timer.html")


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
            
            # Check if user wants to add to calendar
            add_to_calendar = request.POST.get('add_to_calendar') == '1'
            task.add_to_calendar = add_to_calendar
            
            task.save()
            
            # Create calendar event if requested and has due date
            if add_to_calendar and task.due_date:
                calendar_event = CalendarEvent.objects.create(
                    user=request.user,
                    title=task.title,
                    description=f"Task: {task.title}",
                    event_date=task.due_date,
                    category=task.category,
                    start_time=None,
                    end_time=None
                )
                # Auto-assign color based on category
                calendar_event.color = calendar_event.get_category_color()
                calendar_event.save()
                
                # Link the task to the calendar event
                task.linked_calendar_event = calendar_event
                task.save()

            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                task_html = render_to_string("main/partials/task_card.html", {"task": task}, request=request)
                return JsonResponse({"success": True, "task_html": task_html})

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors})

    return redirect("dashboard")


@login_required
def edit_task(request, task_id):
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        task = get_object_or_404(Task, id=task_id, user=request.user)
        old_linked_event = task.linked_calendar_event
        
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            # Check if user wants to add to calendar
            add_to_calendar = request.POST.get('add_to_calendar') == '1'
            task.add_to_calendar = add_to_calendar
            
            form.save()
            
            # Handle calendar sync
            if add_to_calendar and task.due_date:
                if old_linked_event:
                    # Update existing linked event
                    old_linked_event.title = task.title
                    old_linked_event.event_date = task.due_date
                    old_linked_event.category = task.category
                    old_linked_event.color = old_linked_event.get_category_color()
                    old_linked_event.save()
                else:
                    # Create new calendar event
                    calendar_event = CalendarEvent.objects.create(
                        user=request.user,
                        title=task.title,
                        description=f"Task: {task.title}",
                        event_date=task.due_date,
                        category=task.category,
                        start_time=None,
                        end_time=None
                    )
                    calendar_event.color = calendar_event.get_category_color()
                    calendar_event.save()
                    task.linked_calendar_event = calendar_event
                    task.save()
            elif old_linked_event:
                # User unchecked "add to calendar" - remove link but keep event
                task.linked_calendar_event = None
                task.save()
            
            task_html = render_to_string("main/partials/task_card.html", {"task": task}, request=request)
            return JsonResponse({"success": True, "task_html": task_html, "task_id": task.id})
        else:
            return JsonResponse({"success": False, "errors": form.errors})

    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    # Delete linked calendar event if exists
    if task.linked_calendar_event:
        task.linked_calendar_event.delete()
    
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



# ============================================================
# TIMER API
# ============================================================
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from datetime import timedelta
from django.db.models import Sum, Avg, Count

@login_required
@csrf_exempt
def save_session(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            session = TimerSession.objects.create(
                user=request.user,
                start_time=parse_datetime(data['startTime']),
                end_time=parse_datetime(data['endTime']),
                duration_minutes=data['duration'],
                mode=data['mode'],
                completed=True
            )
            
            # Update streak if it's a focus session
            if data['mode'] == 'focus':
                streak, created = UserStreak.objects.get_or_create(user=request.user)
                session_date = session.start_time.date()
                streak.update_streak(session_date)
            
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid method"})



@login_required
def get_timer_stats(request):
    """Get advanced timer statistics including streaks and analytics."""
    today = timezone.now().date()
    
    # Get or create streak data
    streak_data, created = UserStreak.objects.get_or_create(user=request.user)
    
    # Get all focus sessions
    all_focus_sessions = TimerSession.objects.filter(
        user=request.user, 
        mode='focus',
        completed=True
    )
    
    # Calculate total sessions and average length
    total_sessions = all_focus_sessions.count()
    avg_session_length = all_focus_sessions.aggregate(
        avg=Avg('duration_minutes')
    )['avg'] or 0
    
    # Daily stats for last 7 days
    daily_stats = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        day_sessions = all_focus_sessions.filter(start_time__date=d)
        minutes = sum(s.duration_minutes for s in day_sessions)
        daily_stats.append({
            "date": d.strftime("%Y-%m-%d"),
            "minutes": minutes,
            "sessions": day_sessions.count()
        })
    
    # Week total
    week_start = today - timedelta(days=6)
    week_sessions = all_focus_sessions.filter(start_time__date__gte=week_start)
    week_total_minutes = sum(s.duration_minutes for s in week_sessions)
    
    # Month total (current month)
    month_start = today.replace(day=1)
    month_sessions = all_focus_sessions.filter(start_time__date__gte=month_start)
    month_total_minutes = sum(s.duration_minutes for s in month_sessions)

    return JsonResponse({
        "streak": streak_data.current_streak,
        "longest_streak": streak_data.longest_streak,
        "daily_stats": daily_stats,
        "total_sessions": total_sessions,
        "average_session_minutes": round(avg_session_length, 1),
        "week_total_minutes": week_total_minutes,
        "month_total_minutes": month_total_minutes,
    })



# ============================================================
# CALENDAR VIEWS
# ============================================================
import json
from datetime import datetime, timedelta
from django.views.decorators.http import require_http_methods

@login_required
def calendar_view(request):
    """Renders the calendar page."""
    return render(request, 'main/calendar.html')


@login_required
def get_events(request):
    """API endpoint to get all events and tasks for the calendar."""
    # Get month/year from query params (default to current month)
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    
    # Helper function to safely format time
    def safe_time_format(time_obj):
        if time_obj is None:
            return None
        if isinstance(time_obj, str):
            return time_obj  # If it's already a string, return as is
        return time_obj.strftime('%H:%M')  # Otherwise format it
    
    # Get all events for the user
    events = CalendarEvent.objects.filter(user=request.user)
    
    # Get all tasks with due dates
    tasks = Task.objects.filter(user=request.user, due_date__isnull=False)
    
    # Format events
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'date': event.event_date.strftime('%Y-%m-%d'),
            'start_time': safe_time_format(event.start_time),
            'end_time': safe_time_format(event.end_time),
            'category': event.category,
            'color': event.color,
            'type': 'event',
            'reminder_enabled': event.reminder_enabled,
            'reminder_minutes_before': event.reminder_minutes_before,
            'is_recurring': event.is_recurring or (event.parent_event is not None)
        })
    
    # Format tasks
    for task in tasks:
        events_data.append({
            'id': task.id,
            'title': task.title,
            'date': task.due_date.strftime('%Y-%m-%d'),
            'category': task.category,
            'color': '#6366f1',  # Indigo for tasks
            'type': 'task',
            'completed': task.completed
        })
    
    return JsonResponse({'events': events_data})


@login_required
@require_http_methods(["POST"])
def add_event(request):
    """Add a new calendar event."""
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        from datetime import datetime
        data = json.loads(request.body)
        
        logger.info(f"Received event data: {data}")
        
        # Handle time fields - convert empty strings to None and parse time strings
        start_time = data.get('start_time')
        logger.info(f"Raw start_time: {start_time} (type: {type(start_time)})")
        
        if start_time == '' or not start_time:
            start_time = None
        elif isinstance(start_time, str):
            # Parse time string to time object
            try:
                start_time = datetime.strptime(start_time, '%H:%M').time()
                logger.info(f"Parsed start_time (24h): {start_time}")
            except ValueError:
                # Try 12-hour format
                try:
                    start_time = datetime.strptime(start_time, '%I:%M %p').time()
                    logger.info(f"Parsed start_time (12h): {start_time}")
                except ValueError:
                    logger.warning(f"Could not parse start_time: {start_time}")
                    start_time = None
            
        end_time = data.get('end_time')
        logger.info(f"Raw end_time: {end_time} (type: {type(end_time)})")
        
        if end_time == '' or not end_time:
            end_time = None
        elif isinstance(end_time, str):
            # Parse time string to time object
            try:
                end_time = datetime.strptime(end_time, '%H:%M').time()
                logger.info(f"Parsed end_time (24h): {end_time}")
            except ValueError:
                # Try 12-hour format
                try:
                    end_time = datetime.strptime(end_time, '%I:%M %p').time()
                    logger.info(f"Parsed end_time (12h): {end_time}")
                except ValueError:
                    logger.warning(f"Could not parse end_time: {end_time}")
                    end_time = None
        
        logger.info(f"Creating event with start_time={start_time} (type: {type(start_time)}), end_time={end_time} (type: {type(end_time)})")
        
        # Get category and determine color
        category = data.get('category', 'Other')
        user_color = data.get('color')
        
        # Determine which color to use
        if user_color:
            color_to_use = user_color
        else:
            # Create a temporary event object to get category color
            temp_event = CalendarEvent(category=category)
            color_to_use = temp_event.get_category_color()
        
        event = CalendarEvent.objects.create(
            user=request.user,
            title=data['title'],
            description=data.get('description', ''),
            event_date=data['event_date'],
            start_time=start_time,
            end_time=end_time,
            category=category,
            color=color_to_use,
            reminder_enabled=data.get('reminder_enabled', False),
            reminder_minutes_before=data.get('reminder_minutes_before', 15),
            is_recurring=data.get('is_recurring', False),
            recurrence_pattern=data.get('recurrence_pattern') if data.get('is_recurring') else None,
            recurrence_end_date=data.get('recurrence_end_date') if data.get('is_recurring') else None
        )
        
        # Generate recurring instances if recurring event
        if data.get('is_recurring') and data.get('recurrence_end_date'):
            from datetime import timedelta
            from datetime import datetime as dt
            
            current_date = dt.strptime(data['event_date'], '%Y-%m-%d').date()
            end_date = dt.strptime(data['recurrence_end_date'], '%Y-%m-%d').date()
            pattern = data.get('recurrence_pattern', 'weekly')
            
            while current_date < end_date:
                # Increment date based on pattern
                if pattern == 'daily':
                    current_date += timedelta(days=1)
                elif pattern == 'weekly':
                    current_date += timedelta(weeks=1)
                elif pattern == 'monthly':
                    # Add approximately one month
                    month = current_date.month
                    year = current_date.year
                    if month == 12:
                        month = 1
                        year += 1
                    else:
                        month += 1
                    # Handle day overflow (e.g., Jan 31 -> Feb 28)
                    try:
                        current_date = current_date.replace(year=year, month=month)
                    except ValueError:
                        # Day doesn't exist in new month, use last day of month
                        import calendar
                        last_day = calendar.monthrange(year, month)[1]
                        current_date = current_date.replace(year=year, month=month, day=last_day)
                
                if current_date <= end_date:
                    # Create recurring instance
                    CalendarEvent.objects.create(
                        user=request.user,
                        title=event.title,
                        description=event.description,
                        event_date=current_date,
                        start_time=event.start_time,
                        end_time=event.end_time,
                        category=event.category,
                        color=event.color,
                        reminder_enabled=event.reminder_enabled,
                        reminder_minutes_before=event.reminder_minutes_before,
                        is_recurring=False,  # Instances are not recurring themselves
                        parent_event=event  # Link to parent
                    )
        
        # Reload from database to get properly typed fields
        event.refresh_from_db()
        
        logger.info(f"Event created successfully: {event.id}")
        logger.info(f"Event start_time from DB: {event.start_time} (type: {type(event.start_time)})")
        logger.info(f"Event end_time from DB: {event.end_time} (type: {type(event.end_time)})")
        
        # Safely format time fields
        def safe_time_format(time_obj):
            if time_obj is None:
                return None
            if isinstance(time_obj, str):
                return time_obj  # If it's already a string, return as is
            try:
                return time_obj.strftime('%H:%M')  # Otherwise format it
            except AttributeError as e:
                logger.error(f"Error formatting time {time_obj} (type: {type(time_obj)}): {e}")
                return str(time_obj)  # Fallback to string conversion
        
        try:
            response_data = {
                'success': True,
                'event': {
                    'id': event.id,
                    'title': event.title,
                    'description': event.description,
                    'date': event.event_date.strftime('%Y-%m-%d'),
                    'start_time': safe_time_format(event.start_time),
                    'end_time': safe_time_format(event.end_time),
                    'category': event.category,
                    'color': event.color,
                    'type': 'event'
                }
            }
            logger.info(f"Response data: {response_data}")
            return JsonResponse(response_data)
        except Exception as format_error:
            logger.error(f"Error formatting response: {format_error}", exc_info=True)
            return JsonResponse({'success': False, 'error': f'Error formatting response: {str(format_error)}'}, status=400)
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in add_event: {e}", exc_info=True)
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def edit_event(request, event_id):
    """Edit an existing calendar event."""
    try:
        from datetime import datetime
        event = get_object_or_404(CalendarEvent, id=event_id, user=request.user)
        data = json.loads(request.body)
        
        event.title = data.get('title', event.title)
        event.description = data.get('description', event.description)
        event.event_date = data.get('event_date', event.event_date)
        
        # Handle time fields - convert empty strings to None and parse time strings
        start_time = data.get('start_time', event.start_time)
        if start_time == '' or not start_time:
            start_time = None
        elif isinstance(start_time, str):
            # Parse time string to time object
            try:
                start_time = datetime.strptime(start_time, '%H:%M').time()
            except ValueError:
                # Try 12-hour format
                try:
                    start_time = datetime.strptime(start_time, '%I:%M %p').time()
                except ValueError:
                    start_time = event.start_time  # Keep existing value if parse fails
        event.start_time = start_time
        
        end_time = data.get('end_time', event.end_time)
        if end_time == '' or not end_time:
            end_time = None
        elif isinstance(end_time, str):
            # Parse time string to time object
            try:
                end_time = datetime.strptime(end_time, '%H:%M').time()
            except ValueError:
                # Try 12-hour format
                try:
                    end_time = datetime.strptime(end_time, '%I:%M %p').time()
                except ValueError:
                    end_time = event.end_time  # Keep existing value if parse fails
        event.end_time = end_time
        
        # Handle category and color
        old_category = event.category
        new_category = data.get('category', event.category)
        user_color = data.get('color')
        
        event.category = new_category
        
        # If category changed, always recalculate color based on category
        # This takes priority over user-provided color to ensure consistency
        if new_category != old_category:
            event.color = event.get_category_color()
        elif user_color:
            # Only use user color if category didn't change
            event.color = user_color
        
        # Handle reminder fields
        event.reminder_enabled = data.get('reminder_enabled', event.reminder_enabled)
        event.reminder_minutes_before = data.get('reminder_minutes_before', event.reminder_minutes_before)
            
        event.save()
        
        # If this is a recurring event or part of a recurring series, update all instances
        if event.is_recurring:
            # This is the parent - update all child instances
            for instance in event.recurring_instances.all():
                instance.title = event.title
                instance.description = event.description
                instance.start_time = event.start_time
                instance.end_time = event.end_time
                instance.category = event.category
                instance.color = instance.get_category_color()  # Recalculate color based on category
                instance.reminder_enabled = event.reminder_enabled
                instance.reminder_minutes_before = event.reminder_minutes_before
                instance.save()
        elif event.parent_event:
            # This is an instance - update the parent and all siblings
            parent = event.parent_event
            parent.title = event.title
            parent.description = event.description
            parent.start_time = event.start_time
            parent.end_time = event.end_time
            parent.category = event.category
            parent.color = parent.get_category_color()  # Recalculate color based on category
            parent.reminder_enabled = event.reminder_enabled
            parent.reminder_minutes_before = event.reminder_minutes_before
            parent.save()
            
            # Update all sibling instances
            for sibling in parent.recurring_instances.all():
                sibling.title = event.title
                sibling.description = event.description
                sibling.start_time = event.start_time
                sibling.end_time = event.end_time
                sibling.category = event.category
                sibling.color = sibling.get_category_color()  # Recalculate color based on category
                sibling.reminder_enabled = event.reminder_enabled
                sibling.reminder_minutes_before = event.reminder_minutes_before
                sibling.save()
        
        # Reload from database to get properly typed fields
        event.refresh_from_db()
        
        # Safely format time fields
        def safe_time_format(time_obj):
            if time_obj is None:
                return None
            if isinstance(time_obj, str):
                return time_obj  # If it's already a string, return as is
            return time_obj.strftime('%H:%M')  # Otherwise format it
        
        return JsonResponse({
            'success': True,
            'event': {
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'date': event.event_date.strftime('%Y-%m-%d'),
                'start_time': safe_time_format(event.start_time),
                'end_time': safe_time_format(event.end_time),
                'category': event.category,
                'color': event.color,
                'type': 'event'
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST", "DELETE"])
def delete_event(request, event_id):
    """Delete a calendar event."""
    try:
        event = get_object_or_404(CalendarEvent, id=event_id, user=request.user)
        
        # If this is a recurring event or part of a recurring series, delete all instances
        if event.is_recurring:
            # This is the parent event - delete all child instances
            event.recurring_instances.all().delete()
            event.delete()
        elif event.parent_event:
            # This is an instance - delete the parent and all siblings
            parent = event.parent_event
            parent.recurring_instances.all().delete()
            parent.delete()
        else:
            # Regular event - just delete it
            event.delete()
            
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def reschedule_event(request, event_id):
    """Reschedule an event to a new date (for drag-and-drop)"""
    if request.method == 'POST':
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Reschedule request for event {event_id} by user {request.user}")
            
            # Try to get the event
            try:
                event = CalendarEvent.objects.get(id=event_id, user=request.user)
            except CalendarEvent.DoesNotExist:
                logger.error(f"Event {event_id} not found for user {request.user}")
                # Check if event exists at all
                if CalendarEvent.objects.filter(id=event_id).exists():
                    logger.error(f"Event {event_id} exists but belongs to different user")
                    return JsonResponse({'status': 'error', 'message': 'Event belongs to different user'}, status=403)
                return JsonResponse({'status': 'error', 'message': 'Event not found'}, status=404)
            
            data = json.loads(request.body)
            new_date = data.get('new_date')
            
            if not new_date:
                return JsonResponse({'status': 'error', 'message': 'No date provided'}, status=400)
            
            logger.info(f"Updating event {event_id} from {event.event_date} to {new_date}")
            
            # Update event date (preserves start_time and end_time)
            event.event_date = new_date
            event.save()
            
            logger.info(f"Successfully rescheduled event {event_id}")
            return JsonResponse({'status': 'success', 'message': 'Event rescheduled successfully'})
        except CalendarEvent.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Event not found'}, status=404)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error rescheduling event: {e}", exc_info=True)
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
# ============================================================
# SUBTASK ACTIONS
# ============================================================
@login_required
def add_subtask(request, task_id):
    """Add a subtask to a task"""
    task = get_object_or_404(Task, id=task_id, user=request.user)
    
    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        title = request.POST.get("title", "").strip()
        if title:
            subtask = SubTask.objects.create(task=task, title=title)
            completed, total = task.subtask_progress()
            return JsonResponse({
                "success": True,
                "subtask_id": subtask.id,
                "title": subtask.title,
                "completed": subtask.completed,
                "progress": {"completed": completed, "total": total, "percent": task.subtask_progress_percent()}
            })
        return JsonResponse({"success": False, "error": "Title is required"})
    
    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def toggle_subtask(request, subtask_id):
    """Toggle subtask completion status"""
    subtask = get_object_or_404(SubTask, id=subtask_id, task__user=request.user)
    
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        subtask.completed = not subtask.completed
        subtask.save()
        task = subtask.task
        completed, total = task.subtask_progress()
        return JsonResponse({
            "success": True,
            "subtask_id": subtask.id,
            "completed": subtask.completed,
            "progress": {"completed": completed, "total": total, "percent": task.subtask_progress_percent()}
        })
    
    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def delete_subtask(request, subtask_id):
    """Delete a subtask"""
    subtask = get_object_or_404(SubTask, id=subtask_id, task__user=request.user)
    task = subtask.task
    
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        subtask.delete()
        completed, total = task.subtask_progress()
        return JsonResponse({
            "success": True,
            "subtask_id": subtask_id,
            "progress": {"completed": completed, "total": total, "percent": task.subtask_progress_percent()}
        })
    
    return JsonResponse({"success": False, "error": "Invalid request"})


@login_required
def get_subtasks(request, task_id):
    """Get all subtasks for a task"""
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
            "progress": {"completed": completed, "total": total, "percent": task.subtask_progress_percent()}
        })
    
    return JsonResponse({"success": False, "error": "Invalid request"})

@login_required
def reschedule_event(request, event_id):
    """Reschedule an event to a new date (for drag-and-drop)"""
    if request.method == 'POST':
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Reschedule request for event {event_id} by user {request.user}")
            
            # Try to get the event
            try:
                event = CalendarEvent.objects.get(id=event_id, user=request.user)
            except CalendarEvent.DoesNotExist:
                logger.error(f"Event {event_id} not found for user {request.user}")
                # Check if event exists at all
                if CalendarEvent.objects.filter(id=event_id).exists():
                    logger.error(f"Event {event_id} exists but belongs to different user")
                    return JsonResponse({'status': 'error', 'message': 'Event belongs to different user'}, status=403)
                return JsonResponse({'status': 'error', 'message': 'Event not found'}, status=404)
            
            data = json.loads(request.body)
            new_date = data.get('new_date')
            
            if not new_date:
                return JsonResponse({'status': 'error', 'message': 'No date provided'}, status=400)
            
            logger.info(f"Updating event {event_id} from {event.event_date} to {new_date}")
            
            # Update event date (preserves start_time and end_time)
            event.event_date = new_date
            event.save()
            
            logger.info(f"Successfully rescheduled event {event_id}")
            return JsonResponse({'status': 'success', 'message': 'Event rescheduled successfully'})
        except CalendarEvent.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Event not found'}, status=404)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error rescheduling event: {e}", exc_info=True)
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
