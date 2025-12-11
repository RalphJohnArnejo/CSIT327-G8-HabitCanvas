from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

# ===== TASK MODEL =====
class Task(models.Model):
    CATEGORY_CHOICES = [
        ("School", "School"),
        ("Personal", "Personal"),
        ("Work", "Work"),
    ]

    DIFFICULTY_CHOICES = [
        ("Easy", "Easy"),
        ("Medium", "Medium"),
        ("Hard", "Hard"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tasks"
    )
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    completed = models.BooleanField(default=False)
    favorite = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)
    due_date = models.DateField(null=True, blank=True)  # Added due_date
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Task-Calendar Sync fields
    add_to_calendar = models.BooleanField(default=False, help_text="Automatically sync this task to calendar")
    linked_calendar_event = models.ForeignKey(
        'CalendarEvent',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_task',
        help_text="Calendar event linked to this task"
    )

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-priority', '-favorite', '-created_at']  # default ordering

    def subtask_progress(self):
        """Returns (completed_count, total_count) for subtasks"""
        subtasks = self.subtasks.all()
        total = subtasks.count()
        completed = subtasks.filter(completed=True).count()
        return completed, total

    def subtask_progress_percent(self):
        """Returns progress percentage for subtasks"""
        completed, total = self.subtask_progress()
        if total == 0:
            return 0
        return int((completed / total) * 100)


# ===== SUBTASK MODEL =====
class SubTask(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="subtasks"
    )
    title = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({'Done' if self.completed else 'Pending'})"

    class Meta:
        ordering = ['created_at']


# ===== LOGIN ATTEMPT MODEL =====
# Regex pattern for allowed emails
email_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9._%+-]+@(gmail\.com|yahoo\.com|outlook\.com|cit\.edu)$',
    message='Email must be @gmail.com, @yahoo.com, @outlook.com, or @cit.edu'
)

class LoginAttempt(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='login_attempts'
    )
    email = models.EmailField(validators=[email_validator])
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)

    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.email} - {status} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


# ===== TIMER SESSION MODEL =====
class TimerSession(models.Model):
    MODE_CHOICES = [
        ('focus', 'Focus'),
        ('short', 'Short Break'),
        ('long', 'Long Break'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='timer_sessions')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    duration_minutes = models.IntegerField()
    mode = models.CharField(max_length=10, choices=MODE_CHOICES)
    completed = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.mode} ({self.duration_minutes} min)"


# ===== CALENDAR EVENT MODEL =====
class CalendarEvent(models.Model):
    CATEGORY_CHOICES = [
        ('Work', 'Work'),
        ('Personal', 'Personal'),
        ('School', 'School'),
        ('Meeting', 'Meeting'),
        ('Other', 'Other'),
    ]
    
    COLOR_CHOICES = [
        ('#1f6feb', 'Blue'),
        ('#22c55e', 'Green'),
        ('#f59e0b', 'Orange'),
        ('#ef4444', 'Red'),
        ('#8b5cf6', 'Purple'),
        ('#ec4899', 'Pink'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calendar_events')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Other')
    color = models.CharField(max_length=7, choices=COLOR_CHOICES, default='#1f6feb')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Recurring event fields
    is_recurring = models.BooleanField(default=False, help_text="Is this a recurring event?")
    recurrence_pattern = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
        ],
        help_text="How often this event repeats"
    )
    recurrence_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="When to stop creating recurring instances"
    )
    parent_event = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='recurring_instances',
        help_text="The original event this instance belongs to (for recurring events)"
    )
    
    # Notification/Reminder fields
    reminder_enabled = models.BooleanField(default=False, help_text="Enable reminder notification for this event")
    reminder_minutes_before = models.IntegerField(
        default=15,
        help_text="Minutes before event to show reminder (15, 30, 60, 1440 for 1 day)"
    )
    
    def get_category_color(self):
        """Return the default color for this event's category."""
        category_colors = {
            'School': '#1f6feb',    # Blue
            'Personal': '#8b5cf6',  # Purple
            'Work': '#f59e0b',      # Orange
            'Meeting': '#22c55e',   # Green
            'Other': '#ec4899',     # Pink
        }
        return category_colors.get(self.category, '#1f6feb')  # Default to blue
    
    def __str__(self):
        return f"{self.title} - {self.event_date}"
    
    class Meta:
        ordering = ['event_date', 'start_time']


# ===== USER STREAK MODEL =====
class UserStreak(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='streak_data')
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_focus_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.current_streak} day streak"
    
    
    def update_streak(self, session_date):
        """Update streak based on new focus session date."""
        from datetime import timedelta
        
        if not self.last_focus_date:
            # First session ever
            self.current_streak = 1
            self.last_focus_date = session_date
        elif session_date == self.last_focus_date:
            # Same day, no change
            pass
        elif session_date == self.last_focus_date + timedelta(days=1):
            # Consecutive day
            self.current_streak += 1
            self.last_focus_date = session_date
        elif session_date > self.last_focus_date + timedelta(days=1):
            # Streak broken
            self.current_streak = 1
            self.last_focus_date = session_date
        
        # Update longest streak
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        
        self.save()


# ===== USER PROFILE MODEL (AVATAR) =====
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', default='defaults/default_avatar.png', blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

# Signal to create UserProfile automatically
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


