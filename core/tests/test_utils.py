from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import date, timedelta
from decimal import Decimal
from core.models import DrillShift, DrillingProgress, MaterialUsed
from accounts.models import UserProfile
from core.utils import (
    generate_shift_summary,
    calculate_daily_progress
)

User = get_user_model()

class ExportUtilsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.supervisor = User.objects.create_user(username='supervisor', password='test123')
        cls.supervisor.profile.role = UserProfile.ROLE_SUPERVISOR
        cls.supervisor.profile.save()

        # Create test shifts spanning multiple days
        today = date.today()
        for i in range(3):
            shift = DrillShift.objects.create(
                created_by=cls.supervisor,
                date=today - timedelta(days=i),
                rig=f'Rig {i+1}',
                location='Test Location',
                status=DrillShift.STATUS_APPROVED
            )
            
            # Add progress
            DrillingProgress.objects.create(
                shift=shift,
                start_depth=Decimal('10.00'),
                end_depth=Decimal('15.50'),
                meters_drilled=Decimal('5.50'),
                penetration_rate=Decimal('2.75')
            )
            
            # Add materials
            MaterialUsed.objects.create(
                shift=shift,
                material_name='Diesel',
                quantity=Decimal('100.00'),
                unit='liters'
            )
            MaterialUsed.objects.create(
                shift=shift,
                material_name='Water',
                quantity=Decimal('500.00'),
                unit='liters'
            )

    def test_generate_shift_summary(self):
        """Test shift summary generation"""
        shift = DrillShift.objects.first()
        summary = generate_shift_summary(shift)
        
        self.assertEqual(summary['shift_id'], shift.id)
        self.assertEqual(summary['total_meters'], Decimal('5.50'))
        self.assertEqual(summary['avg_penetration'], Decimal('2.75'))
        
        # Test materials in summary
        self.assertEqual(len(summary['materials']), 2)
        self.assertEqual(summary['materials']['Diesel'], Decimal('100.00'))
        self.assertEqual(summary['materials']['Water'], Decimal('500.00'))

    def test_calculate_daily_progress(self):
        """Test daily progress calculations"""
        shifts = DrillShift.objects.all()
        stats = calculate_daily_progress(shifts)
        
        # Should have 3 days of data
        self.assertEqual(len(stats), 3)
        
        # Each day should have 5.50 meters
        for day_stat in stats:
            self.assertEqual(day_stat['total_meters'], Decimal('5.50'))
            self.assertEqual(day_stat['avg_penetration'], Decimal('2.75'))

    def test_empty_shifts_handling(self):
        """Test handling of empty or invalid shifts"""
        DrillShift.objects.all().delete()
        
        # Test with no shifts
        empty_shift_stats = calculate_daily_progress([])
        self.assertEqual(len(empty_shift_stats), 0)
        
        # Create shift with no progress data
        shift = DrillShift.objects.create(
            created_by=self.supervisor,
            date=date.today(),
            rig='Test Rig',
            status=DrillShift.STATUS_DRAFT
        )
        
        # Summary should handle missing data gracefully
        summary = generate_shift_summary(shift)
        self.assertEqual(summary['total_meters'], Decimal('0.00'))
        self.assertEqual(summary['avg_penetration'], Decimal('0.00'))
        self.assertEqual(len(summary['materials']), 0)