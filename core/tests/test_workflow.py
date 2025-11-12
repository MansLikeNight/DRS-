from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date
from decimal import Decimal
from core.models import DrillShift, ApprovalHistory
from accounts.models import UserProfile

User = get_user_model()

class ApprovalWorkflowTest(TestCase):
    def setUp(self):
        # Create users with different roles
        self.supervisor = User.objects.create_user(username='supervisor', password='test123')
        self.supervisor.profile.role = UserProfile.ROLE_SUPERVISOR
        self.supervisor.profile.save()
        
        self.manager = User.objects.create_user(username='manager', password='test123')
        self.manager.profile.role = UserProfile.ROLE_MANAGER
        self.manager.profile.save()
        
        self.client_user = User.objects.create_user(username='client', password='test123')
        self.client_user.profile.role = UserProfile.ROLE_CLIENT
        self.client_user.profile.save()
        
        # Create a test shift
        self.shift = DrillShift.objects.create(
            created_by=self.supervisor,
            date=date.today(),
            rig='Test Rig',
            status=DrillShift.STATUS_DRAFT
        )

    def test_submit_workflow(self):
        """Test the shift submission workflow"""
        # Client can't submit
        self.client.login(username='client', password='test123')
        response = self.client.post(reverse('core:shift_submit', args=[self.shift.pk]))
        self.assertEqual(response.status_code, 403)
        
        # Another supervisor can't submit
        other_supervisor = User.objects.create_user(username='other_sup', password='test123')
        other_supervisor.profile.role = UserProfile.ROLE_SUPERVISOR
        other_supervisor.profile.save()
        
        self.client.login(username='other_sup', password='test123')
        response = self.client.post(reverse('core:shift_submit', args=[self.shift.pk]))
        self.assertEqual(response.status_code, 302)  # Redirects with error message
        
        # Creator can submit
        self.client.login(username='supervisor', password='test123')
        response = self.client.post(reverse('core:shift_submit', args=[self.shift.pk]))
        self.assertEqual(response.status_code, 302)  # Successful redirect
        
        # Check shift status
        self.shift.refresh_from_db()
        self.assertEqual(self.shift.status, DrillShift.STATUS_SUBMITTED)
        
        # Check approval history
        self.assertEqual(self.shift.approvals.count(), 1)
        self.assertEqual(
            self.shift.approvals.first().role,
            'Pending Manager Review'
        )

    def test_approval_workflow(self):
        """Test the shift approval workflow"""
        # Set shift to submitted status
        self.shift.status = DrillShift.STATUS_SUBMITTED
        self.shift.save()
        
        # Client can't approve
        self.client.login(username='client', password='test123')
        response = self.client.post(reverse('core:shift_approve', args=[self.shift.pk]), {
            'decision': ApprovalHistory.DECISION_APPROVED,
            'comments': 'Test approval'
        })
        self.assertEqual(response.status_code, 403)
        
        # Manager can approve
        self.client.login(username='manager', password='test123')
        response = self.client.post(reverse('core:shift_approve', args=[self.shift.pk]), {
            'decision': ApprovalHistory.DECISION_APPROVED,
            'comments': 'Manager approval'
        })
        self.assertEqual(response.status_code, 302)  # Successful redirect
        
        # Check shift status
        self.shift.refresh_from_db()
        self.assertEqual(self.shift.status, DrillShift.STATUS_APPROVED)
        self.assertTrue(self.shift.is_locked)
        
        # Check approval history
        latest_approval = self.shift.approvals.latest('timestamp')
        self.assertEqual(latest_approval.approver, self.manager)
        self.assertEqual(latest_approval.decision, ApprovalHistory.DECISION_APPROVED)
        self.assertEqual(latest_approval.comments, 'Manager approval')

    def test_reject_workflow(self):
        """Test the shift rejection workflow"""
        # Set shift to submitted status
        self.shift.status = DrillShift.STATUS_SUBMITTED
        self.shift.save()
        
        # Manager can reject
        self.client.login(username='manager', password='test123')
        response = self.client.post(reverse('core:shift_approve', args=[self.shift.pk]), {
            'decision': ApprovalHistory.DECISION_REJECTED,
            'comments': 'Needs revision'
        })
        self.assertEqual(response.status_code, 302)
        
        # Check shift status
        self.shift.refresh_from_db()
        self.assertEqual(self.shift.status, DrillShift.STATUS_REJECTED)
        self.assertFalse(self.shift.is_locked)
        
        # Creator should be able to update rejected shift
        self.client.login(username='supervisor', password='test123')
        response = self.client.get(reverse('core:shift_update', args=[self.shift.pk]))
        self.assertEqual(response.status_code, 200)