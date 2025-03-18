from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from ..utils.logging import log_user_action

def login_view(request):
    """Vue de connexion des utilisateurs"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            log_user_action(user, 'login', {'method': 'form'})
            return redirect('admin:index')
        else:
            messages.error(request, 'Identifiants invalides')
            log_user_action(None, 'login_failed', {'username': username})
    
    return render(request, 'core/login.html') 