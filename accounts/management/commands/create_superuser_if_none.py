from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decouple import config

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser if none exists and environment variables are set'

    def handle(self, *args, **options):
        # Check if any superuser already exists
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.SUCCESS('Superuser already exists. Skipping creation.'))
            return

        # Get credentials from environment variables
        username = config('DJANGO_SUPERUSER_USERNAME', default=None)
        email = config('DJANGO_SUPERUSER_EMAIL', default=None)
        password = config('DJANGO_SUPERUSER_PASSWORD', default=None)

        if not all([username, email, password]):
            self.stdout.write(self.style.WARNING(
                'Superuser environment variables not set. Skipping automatic creation.'
            ))
            return

        # Create the superuser
        try:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {e}'))
