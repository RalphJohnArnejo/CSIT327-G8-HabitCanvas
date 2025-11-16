from django import forms
from .models import Task

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["title", "category", "difficulty", "due_date", "priority", "completed", "favorite"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"})
        }
