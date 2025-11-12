from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Debug user profiles'

    def handle(self, *args, **options):
        users = User.objects.all()
        self.stdout.write(f'Found {users.count()} users')
        
        for user in users:
            self.stdout.write(f'\nUser: {user.username}')
            self.stdout.write(f'Has profile attr: {hasattr(user, "profile")}')
            try:
                profile = UserProfile.objects.get(user=user)
                self.stdout.write(f'Found profile: {profile}')
            except UserProfile.DoesNotExist:
                self.stdout.write(f'No profile found - creating one')
                profile = UserProfile.objects.create(user=user)
                self.stdout.write(f'Created profile: {profile}')
            except Exception as e:
                self.stdout.write(f'Error: {str(e)}')