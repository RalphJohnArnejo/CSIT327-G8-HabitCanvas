import re
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .models import LoginAttempt
from django.utils import timezone


# -------------------------------
# LANDING PAGE
# -------------------------------
def landing_view(request): 
    """Landing page shown before login.""" 
    if request.user.is_authenticated: 
        return redirect("dashboard") 
    return render(request, "main/landing.html")


# -------------------------------
# REGISTER
# -------------------------------
def register_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Email validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@(gmail\.com|yahoo\.com|outlook\.com|cit\.edu)$', email):
            return render(request, "main/register.html", {
                "error": "Email must be @gmail.com, @yahoo.com, @outlook.com, or @cit.edu"
            })

        # Password validation
        if not re.search(r'[A-Z]', password) or not re.search(r'[!@#$%^&*()_+{}\[\]:;<>,.?~\-]', password):
            return render(request, "main/register.html", {
                "error": "Password must contain at least 1 uppercase letter and 1 special character"
            })

        # Check if user already exists
        if User.objects.filter(username=email).exists():
            return render(request, "main/register.html", {"error": "User already exists"})

        # Create user
        User.objects.create_user(username=email, email=email, password=password)
        return redirect("login")

    return render(request, "main/register.html")


# -------------------------------
# LOGIN
# -------------------------------
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        remember_me = request.POST.get("remember_me")

        user = authenticate(request, username=email, password=password)

        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]

        # Login successful
        if user:
            login(request, user)

            # Save successful login attempt
            LoginAttempt.objects.create(
                user=user,
                email=email,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True,
                timestamp=timezone.now()
            )

            # Remember Me logic
            if remember_me:
                request.session.set_expiry(2592000)  # 30 days
            else:
                request.session.set_expiry(0)  # Until browser close

            return redirect("dashboard")

        # Login failed
        LoginAttempt.objects.create(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            timestamp=timezone.now()
        )

        return render(request, "main/login.html", {"error": "Invalid credentials"})

    return render(request, "main/login.html")


# -------------------------------
# DASHBOARD
# -------------------------------
def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect("login")
    return render(request, "main/dashboard.html", {"user": request.user})


# -------------------------------
# LOGOUT
# -------------------------------
def logout_view(request):
    logout(request)
    return redirect("login")
