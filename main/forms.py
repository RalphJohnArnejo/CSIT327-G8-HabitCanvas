from django import forms
from .models import Task, CalendarEvent, UserProfile

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "category", "difficulty", "due_date", "priority", "completed", "favorite"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"})
        }

class CalendarEventForm(forms.ModelForm):
    class Meta:
        model = CalendarEvent
        fields = ['title', 'description', 'event_date', 'start_time', 'end_time', 'category', 'color']
        widgets = {
            'event_date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class ProfileAvatarForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['avatar']

