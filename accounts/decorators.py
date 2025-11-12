from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


def role_required(roles):
    """
    Decorator that checks if the user has any of the specified roles.
    Args:
        roles: String or list of role names
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Please login to continue.')
                return redirect('accounts:login')
            
            if not hasattr(request.user, 'profile'):
                messages.error(request, 'User profile not found.')
                return redirect('accounts:login')
            
            # Superusers can access everything
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            if isinstance(roles, str):
                allowed_roles = [roles]
            else:
                allowed_roles = roles
            
            if request.user.profile.role not in allowed_roles:
                messages.error(request, 'You do not have permission to perform this action.')
                raise PermissionDenied('Insufficient permissions')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def supervisor_required(view_func):
    """Decorator for views that require supervisor role."""
    return role_required('supervisor')(view_func)


def manager_required(view_func):
    """Decorator for views that require manager role."""
    return role_required('manager')(view_func)


def client_required(view_func):
    """Decorator for views that require client role."""
    return role_required('client')(view_func)


def supervisor_or_manager_required(view_func):
    """Decorator for views that require either supervisor or manager role."""
    return role_required(['supervisor', 'manager'])(view_func)


def can_approve_shifts(view_func):
    """Decorator for views that check if user can approve shifts."""
    return supervisor_or_manager_required(view_func)