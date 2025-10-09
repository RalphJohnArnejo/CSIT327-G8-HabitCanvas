"""
URL configuration for HabitCanvas project.

The `urlpatterns` list routes URLs to views.
"""

from django.contrib import admin
from django.urls import path, include  

urlpatterns = [
    path('admin/', admin.site.urls),  
    path('', include('main.urls')),    
]
