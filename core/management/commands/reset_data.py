# Quick Data Reset Script
# Deletes all shift reports but keeps users

from django.core.management.base import BaseCommand
from core.models import DrillShift, DrillingProgress, ActivityLog, MaterialUsed, Survey, Casing, ApprovalHistory
from django.contrib.auth.models import User
from accounts.models import UserProfile

class Command(BaseCommand):
    help = 'Deletes all shift reports but keeps users and profiles'

    def handle(self, *args, **kwargs):
        # Count before deletion
        shift_count = DrillShift.objects.count()
        progress_count = DrillingProgress.objects.count()
        activity_count = ActivityLog.objects.count()
        
        self.stdout.write(f'Found {shift_count} shifts to delete...')
        
        # Delete all report data (cascades will handle related records)
        DrillShift.objects.all().delete()
        
        # Verify deletion
        remaining_shifts = DrillShift.objects.count()
        remaining_users = User.objects.count()
        remaining_profiles = UserProfile.objects.count()
        
        self.stdout.write(self.style.SUCCESS(f'✓ Deleted {shift_count} shifts'))
        self.stdout.write(self.style.SUCCESS(f'✓ Remaining shifts: {remaining_shifts}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Users preserved: {remaining_users}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Profiles preserved: {remaining_profiles}'))
        self.stdout.write(self.style.SUCCESS('Data reset complete! Ready for presentation.'))
