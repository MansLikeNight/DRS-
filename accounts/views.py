from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserProfileForm
from .forms import UserRegistrationForm
from django.contrib.auth import login


@login_required
def profile_view(request):
    """
    View and update the current user's profile.
    
    Displays a form with the user's profile information (role, company, phone).
    Handles updating the profile on POST request.
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered profile template with form
        
    Requires:
        User must be authenticated (enforced by @login_required decorator)
    """
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user.profile)
    
    return render(request, 'accounts/profile.html', {'form': form})


def register_view(request):
    """
    Register a new user account.
    
    Handles new user registration with username, email, password, and
    profile information (role, company, phone). Automatically logs in
    the user after successful registration.
    
    Args:
        request: HTTP request object
        
    Returns:
        Rendered registration template (GET) or redirect to shift list (POST success)
        
    POST Process:
        1. Validates registration form
        2. Creates new User account
        3. Creates associated UserProfile (via signal)
        4. Logs in the new user
        5. Redirects to shift list
    """
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Automatically log the user in after registration
            login(request, user)
            messages.success(request, 'Registration successful. You are now logged in.')
            return redirect('core:shift_list')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})
