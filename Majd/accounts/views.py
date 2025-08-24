from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm, UserProfileForm, UserUpdateForm
from .models import UserProfile

def role_selection_view(request):
    """View for the role selection page (Get Started)"""
    return render(request, 'accounts/role_selection.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    
    # Get pre-selected role from query parameter
    pre_selected_role = request.GET.get('role', '')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in after successful registration
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome, {user.first_name}!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = CustomUserCreationForm()
        # Pre-select the role if it was passed from role selection
        if pre_selected_role and pre_selected_role in dict(UserProfile.USER_TYPE_CHOICES):
            form.fields['user_type'].initial = pre_selected_role
    
    return render(request, 'accounts/register.html', {
        'form': form,
        'pre_selected_role': pre_selected_role
    })

def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            next_url = request.GET.get('next', 'accounts:profile')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('main:main_home_view')

@login_required
def profile_view(request):
    user = request.user
    profile = user.profile
    
    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def profile_edit_view(request):
    user = request.user
    profile = user.profile
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'accounts/profile_edit.html', context)

@login_required
def change_password_view(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        if not request.user.check_password(current_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password1) < 8:
            messages.error(request, 'New password must be at least 8 characters long.')
        else:
            request.user.set_password(new_password1)
            request.user.save()
            messages.success(request, 'Password changed successfully! Please log in again.')
            return redirect('accounts:login')
    
    return render(request, 'accounts/change_password.html')
