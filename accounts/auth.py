from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.db import transaction
from .models import UserProfile


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                user = form.get_user()
                # Explicitly try to access the profile
                try:
                    profile = user.profile
                    self.request.session['profile_id'] = profile.id
                except UserProfile.DoesNotExist:
                    profile = UserProfile.objects.create(user=user)
                    self.request.session['profile_id'] = profile.id
                
                response = super().form_valid(form)
                return response
                
        except Exception as e:
            messages.error(self.request, f"Login error: {str(e)}")
            return redirect('accounts:login')

    def get_success_url(self):
        """Redirect users based on role/profile after login.
        - If ?next= is provided, honor it (handled by parent)
        - If user has a linked client profile, go to client dashboard
        - Managers/Supervisors go to shift list by default
        """
        # If Django has a 'next' redirect already resolved, use it
        redirect_to = self.get_redirect_url()
        if redirect_to:
            return redirect_to

        user = self.request.user
        # If linked to a Client (core.Client.user OneToOne), send to client dashboard
        if hasattr(user, 'client_profile') and user.client_profile is not None:
            return reverse_lazy('core:client_dashboard')

        # Otherwise, route by role if available
        try:
            if user.profile.role == UserProfile.ROLE_MANAGER or user.profile.role == UserProfile.ROLE_SUPERVISOR:
                return reverse_lazy('core:shift_list')
            if user.profile.role == UserProfile.ROLE_CLIENT:
                return reverse_lazy('core:client_dashboard')
        except Exception:
            # No profile or role; fall back
            pass

        return reverse_lazy('core:shift_list')