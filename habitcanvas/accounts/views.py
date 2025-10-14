from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

#1.12 Redirect on login success
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")  #2.4 Logout confirmation (toast)
            return redirect('dashboard')  #Redirect to homepage/dashboard
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')


#2.1–2.4 Logout features
def logout_view(request):
    logout(request)  #Clears session/token
    messages.info(request, "You have been logged out.")  #Toast message
    return redirect('login')  #Redirect to login page


#Dashboard (homepage after login)
def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'dashboard.html')

