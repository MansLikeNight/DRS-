from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import date
from decimal import Decimal
from core.models import DrillShift, DrillingProgress, ActivityLog, MaterialUsed, ApprovalHistory


class DrillModelsTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_create_drill_shift_with_relations(self):
        """Test creating a drill shift with progress, activity and materials"""
        # Create shift
        shift = DrillShift.objects.create(
            created_by=self.user,
            date=date.today(),
            rig='Test Rig 1',
            location='Test Location',
            status=DrillShift.STATUS_DRAFT
        )
        self.assertEqual(shift.status, 'draft')
        self.assertEqual(shift.is_locked, False)

        # Add progress
        progress = DrillingProgress.objects.create(
            shift=shift,
            start_depth=Decimal('10.00'),
            end_depth=Decimal('15.50'),
            meters_drilled=Decimal('5.50')
        )
        self.assertEqual(progress.meters_drilled, Decimal('5.50'))

        # Add activity
        activity = ActivityLog.objects.create(
            shift=shift,
            activity_type='drilling',
            description='Test drilling activity',
            performed_by=self.user
        )
        self.assertEqual(activity.activity_type, 'drilling')

        # Add material
        material = MaterialUsed.objects.create(
            shift=shift,
            material_name='Diesel',
            quantity=Decimal('100.000'),
            unit='liters'
        )
        self.assertEqual(material.quantity, Decimal('100.000'))

        # Add approval
        approval = ApprovalHistory.objects.create(
            shift=shift,
            approver=self.user,
            role='Supervisor',
            decision=ApprovalHistory.DECISION_PENDING
        )
        self.assertEqual(approval.decision, 'pending')

        # Test relationships
        self.assertEqual(shift.progress.count(), 1)
        self.assertEqual(shift.activities.count(), 1)
        self.assertEqual(shift.materials.count(), 1)
        self.assertEqual(shift.approvals.count(), 1)