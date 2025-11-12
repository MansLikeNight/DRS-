from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date
from decimal import Decimal
from core.models import DrillShift, DrillingProgress, ActivityLog, MaterialUsed, ApprovalHistory
from accounts.models import UserProfile

User = get_user_model()

class DrillShiftModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create users with different roles
        cls.supervisor = User.objects.create_user(username='supervisor', password='test123')
        cls.supervisor.profile.role = UserProfile.ROLE_SUPERVISOR
        cls.supervisor.profile.save()
        
        cls.manager = User.objects.create_user(username='manager', password='test123')
        cls.manager.profile.role = UserProfile.ROLE_MANAGER
        cls.manager.profile.save()

    def test_create_drill_shift(self):
        """Test creating a basic drill shift"""
        shift = DrillShift.objects.create(
            created_by=self.supervisor,
            date=date.today(),
            rig='Test Rig 1',
            location='Test Location',
            status=DrillShift.STATUS_DRAFT
        )
        self.assertEqual(shift.rig, 'Test Rig 1')
        self.assertEqual(shift.status, DrillShift.STATUS_DRAFT)
        self.assertFalse(shift.is_locked)

    def test_shift_status_transitions(self):
        """Test shift status transitions and locking behavior"""
        shift = DrillShift.objects.create(
            created_by=self.supervisor,
            date=date.today(),
            rig='Test Rig 1',
            status=DrillShift.STATUS_DRAFT
        )
        
        # Test submission
        shift.status = DrillShift.STATUS_SUBMITTED
        shift.save()
        self.assertEqual(shift.status, DrillShift.STATUS_SUBMITTED)
        self.assertFalse(shift.is_locked)
        
        # Test approval
        shift.status = DrillShift.STATUS_APPROVED
        shift.is_locked = True
        shift.save()
        self.assertEqual(shift.status, DrillShift.STATUS_APPROVED)
        self.assertTrue(shift.is_locked)

    def test_drill_shift_relationships(self):
        """Test relationships between DrillShift and related models"""
        shift = DrillShift.objects.create(
            created_by=self.supervisor,
            date=date.today(),
            rig='Test Rig 1',
            status=DrillShift.STATUS_DRAFT
        )
        
        # Add progress
        progress = DrillingProgress.objects.create(
            shift=shift,
            start_depth=Decimal('10.00'),
            end_depth=Decimal('15.50'),
            meters_drilled=Decimal('5.50'),
            penetration_rate=Decimal('2.75')
        )
        
        # Add activity
        activity = ActivityLog.objects.create(
            shift=shift,
            activity_type='drilling',
            description='Test drilling',
            duration_minutes=120,
            performed_by=self.supervisor
        )
        
        # Add material
        material = MaterialUsed.objects.create(
            shift=shift,
            material_name='Diesel',
            quantity=Decimal('100.00'),
            unit='liters'
        )
        
        # Test relationships
        self.assertEqual(shift.progress.first(), progress)
        self.assertEqual(shift.activities.first(), activity)
        self.assertEqual(shift.materials.first(), material)
        
        # Test cascade deletion
        shift.delete()
        self.assertEqual(DrillingProgress.objects.count(), 0)
        self.assertEqual(ActivityLog.objects.count(), 0)
        self.assertEqual(MaterialUsed.objects.count(), 0)