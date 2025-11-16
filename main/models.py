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

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-priority', '-favorite', '-created_at']  # default ordering


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
