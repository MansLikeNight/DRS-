from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date
from decimal import Decimal
from core.models import DrillShift, DrillingProgress, ActivityLog, MaterialUsed
from accounts.models import UserProfile

User = get_user_model()

class ShiftDetailViewTest(TestCase):
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
        
        # Create test shift with related data
        self.shift = DrillShift.objects.create(
            created_by=self.supervisor,
            date=date.today(),
            rig='Test Rig',
            location='Test Location',
            status=DrillShift.STATUS_DRAFT
        )
        
        # Add progress data
        self.progress = DrillingProgress.objects.create(
            shift=self.shift,
            start_depth=Decimal('100.00'),
            end_depth=Decimal('150.00'),
            meters_drilled=Decimal('50.00')
        )
        
        # Add activity log
        self.activity = ActivityLog.objects.create(
            shift=self.shift,
            activity_type='drilling',
            description='Test drilling',
            duration_minutes=120,
            performed_by=self.supervisor
        )
        
        # Add material usage
        self.material = MaterialUsed.objects.create(
            shift=self.shift,
            material_name='Diesel',
            quantity=Decimal('100.00'),
            unit='liters'
        )

    def test_view_url_exists_at_desired_location(self):
        self.client.login(username='supervisor', password='test123')
        response = self.client.get(f'/shifts/{self.shift.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        self.client.login(username='supervisor', password='test123')
        response = self.client.get(reverse('core:shift_detail', args=[self.shift.pk]))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        self.client.login(username='supervisor', password='test123')
        response = self.client.get(reverse('core:shift_detail', args=[self.shift.pk]))
        self.assertTemplateUsed(response, 'core/shift_detail.html')

    def test_client_cannot_view_draft_shift(self):
        self.client.login(username='client', password='test123')
        response = self.client.get(reverse('core:shift_detail', args=[self.shift.pk]))
        self.assertEqual(response.status_code, 302)  # Redirects with error

    def test_manager_cannot_view_draft_shift(self):
        self.client.login(username='manager', password='test123')
        response = self.client.get(reverse('core:shift_detail', args=[self.shift.pk]))
        self.assertEqual(response.status_code, 302)  # Redirects with error

    def test_supervisor_can_view_own_draft(self):
        self.client.login(username='supervisor', password='test123')
        response = self.client.get(reverse('core:shift_detail', args=[self.shift.pk]))
        self.assertEqual(response.status_code, 200)
        
        # Check context data
        self.assertEqual(response.context['shift'], self.shift)
        self.assertEqual(response.context['total_meters'], Decimal('50.00'))
        self.assertTrue(response.context['can_edit'])
        self.assertTrue(response.context['can_submit'])
        self.assertFalse(response.context['can_approve'])

    def test_all_users_can_view_approved_shift(self):
        # Change shift status to approved
        self.shift.status = DrillShift.STATUS_APPROVED
        self.shift.save()
        
        # Test client access
        self.client.login(username='client', password='test123')
        response = self.client.get(reverse('core:shift_detail', args=[self.shift.pk]))
        self.assertEqual(response.status_code, 200)
        
        # Test manager access
        self.client.login(username='manager', password='test123')
        response = self.client.get(reverse('core:shift_detail', args=[self.shift.pk]))
        self.assertEqual(response.status_code, 200)


class ShiftUpdateViewTest(TestCase):
    def setUp(self):
        # Create users
        self.supervisor = User.objects.create_user(username='supervisor', password='test123')
        self.supervisor.profile.role = UserProfile.ROLE_SUPERVISOR
        self.supervisor.profile.save()
        
        self.other_supervisor = User.objects.create_user(username='other_sup', password='test123')
        self.other_supervisor.profile.role = UserProfile.ROLE_SUPERVISOR
        self.other_supervisor.profile.save()
        
        # Create test shift
        self.shift = DrillShift.objects.create(
            created_by=self.supervisor,
            date=date.today(),
            rig='Test Rig',
            location='Test Location',
            status=DrillShift.STATUS_DRAFT
        )

    def test_only_creator_can_update_shift(self):
        # Test other supervisor cannot update
        self.client.login(username='other_sup', password='test123')
        response = self.client.get(reverse('core:shift_update', args=[self.shift.pk]))
        self.assertEqual(response.status_code, 302)  # Redirects with error

        # Test creator can update
        self.client.login(username='supervisor', password='test123')
        response = self.client.get(reverse('core:shift_update', args=[self.shift.pk]))
        self.assertEqual(response.status_code, 200)

    def test_cannot_update_locked_shift(self):
        # Lock the shift
        self.shift.is_locked = True
        self.shift.save()
        
        self.client.login(username='supervisor', password='test123')
        response = self.client.get(reverse('core:shift_update', args=[self.shift.pk]))
        self.assertEqual(response.status_code, 302)  # Redirects with error

    def test_update_shift_with_formsets(self):
        self.client.login(username='supervisor', password='test123')
        
        # Add initial data
        progress = DrillingProgress.objects.create(
            shift=self.shift,
            start_depth=Decimal('100.00'),
            end_depth=Decimal('150.00'),
            meters_drilled=Decimal('50.00')
        )
        
        # Prepare update data
        data = {
            'date': '2025-11-03',
            'rig': 'Updated Rig',
            'location': 'Updated Location',
            'notes': 'Updated notes',
            
            # Progress formset
            'progress-TOTAL_FORMS': '1',
            'progress-INITIAL_FORMS': '1',
            'progress-MIN_NUM_FORMS': '0',
            'progress-MAX_NUM_FORMS': '1000',
            'progress-0-id': progress.id,
            'progress-0-shift': self.shift.id,
            'progress-0-start_depth': '150.00',
            'progress-0-end_depth': '200.00',
            'progress-0-meters_drilled': '50.00',
            
            # Empty activity formset
            'activity-TOTAL_FORMS': '0',
            'activity-INITIAL_FORMS': '0',
            'activity-MIN_NUM_FORMS': '0',
            'activity-MAX_NUM_FORMS': '1000',
            
            # Empty material formset
            'material-TOTAL_FORMS': '0',
            'material-INITIAL_FORMS': '0',
            'material-MIN_NUM_FORMS': '0',
            'material-MAX_NUM_FORMS': '1000',
        }
        
        response = self.client.post(reverse('core:shift_update', args=[self.shift.pk]), data)
        self.assertEqual(response.status_code, 302)  # Redirect on success
        
        # Check if shift was updated
        self.shift.refresh_from_db()
        self.assertEqual(self.shift.rig, 'Updated Rig')
        self.assertEqual(self.shift.location, 'Updated Location')
        
        # Check if progress was updated
        progress.refresh_from_db()
        self.assertEqual(progress.start_depth, Decimal('150.00'))
        self.assertEqual(progress.end_depth, Decimal('200.00'))