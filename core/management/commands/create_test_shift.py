# Quick Test Data Script - Creates one sample shift for presentation testing

from django.core.management.base import BaseCommand
from core.models import DrillShift, DrillingProgress, ActivityLog, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import time, date

class Command(BaseCommand):
    help = 'Creates a sample shift for testing graphs and presentation'

    def handle(self, *args, **kwargs):
        # Get or create manager user
        manager = User.objects.filter(is_staff=True, is_superuser=False).first()
        if not manager:
            manager = User.objects.filter(is_superuser=True).first()
        
        if not manager:
            self.stdout.write(self.style.ERROR('No user found! Please create a user first.'))
            return
        
        # Get or create client
        client = Client.objects.first()
        if not client:
            client = Client.objects.create(name='Test Client Ltd', is_active=True)
            self.stdout.write(f'Created test client: {client.name}')
        
        # Create test shift
        shift = DrillShift.objects.create(
            created_by=manager,
            client=client,
            date=date.today(),
            shift_type='day',
            rig='RIG-001',
            location='Test Site',
            supervisor_name='John Supervisor',
            driller_name='Mike Driller',
            helper1_name='Helper 1',
            helper2_name='Helper 2',
            start_time=time(7, 0),
            end_time=time(19, 0),
            status='approved',
            notes='Sample shift for presentation demo'
        )
        
        # Add drilling progress
        DrillingProgress.objects.create(
            shift=shift,
            hole_number='BH-001',
            size='HQ',
            start_depth=0.00,
            end_depth=15.50,
            meters_drilled=15.50,
            start_time=time(8, 0),
            end_time=time(12, 30),
            remarks='Good progress, stable formation'
        )
        
        DrillingProgress.objects.create(
            shift=shift,
            hole_number='BH-001',
            size='HQ',
            start_depth=15.50,
            end_depth=24.00,
            meters_drilled=8.50,
            start_time=time(13, 30),
            end_time=time(17, 0),
            remarks='Harder rock, slower penetration'
        )
        
        # Add activities
        ActivityLog.objects.create(
            shift=shift,
            activity_type='maintenance',
            description='Equipment inspection and lubrication',
            duration_minutes=45,
            performed_by=manager
        )
        
        ActivityLog.objects.create(
            shift=shift,
            activity_type='safety',
            description='Morning safety briefing',
            duration_minutes=30,
            performed_by=manager
        )
        
        ActivityLog.objects.create(
            shift=shift,
            activity_type='other',
            description='Core logging and documentation',
            duration_minutes=60,
            performed_by=manager
        )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created test shift: {shift.id}'))
        self.stdout.write(self.style.SUCCESS(f'✓ Added 2 drilling progress records (24m total)'))
        self.stdout.write(self.style.SUCCESS(f'✓ Added 3 activities'))
        self.stdout.write(self.style.SUCCESS('✓ Test data ready! Check shift detail page for graphs.'))
