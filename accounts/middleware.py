from django.db import transaction
from django.contrib import messages
from .models import UserProfile


class UserProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only process if user is authenticated
        if request.user.is_authenticated:
            try:
                # Try to access the profile
                profile = request.user.profile
                request.user_profile = profile
            except UserProfile.DoesNotExist:
                with transaction.atomic():
                    # Create a profile if it doesn't exist
                    profile = UserProfile.objects.create(user=request.user)
                    request.user_profile = profile
                    messages.info(request, 'Profile created successfully.')

        response = self.get_response(request)
        return response