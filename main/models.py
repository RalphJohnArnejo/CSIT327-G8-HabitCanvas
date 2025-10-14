from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

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
