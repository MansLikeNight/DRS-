from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from accounts.models import UserProfile
from accounts.decorators import (
    role_required, supervisor_required, manager_required,
    client_required, supervisor_or_manager_required, can_approve_shifts
)


class DecoratorsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        
        # Create users with different roles
        self.supervisor = User.objects.create_user(
            username='supervisor', password='pass123'
        )
        self.supervisor.profile.role = UserProfile.ROLE_SUPERVISOR
        self.supervisor.profile.save()
        
        self.manager = User.objects.create_user(
            username='manager', password='pass123'
        )
        self.manager.profile.role = UserProfile.ROLE_MANAGER
        self.manager.profile.save()
        
        self.client_user = User.objects.create_user(
            username='client', password='pass123'
        )
        self.client_user.profile.role = UserProfile.ROLE_CLIENT
        self.client_user.profile.save()
        
        # Create a superuser
        self.admin = User.objects.create_superuser(
            username='admin', password='pass123', email='admin@test.com'
        )
        
        # Create a mock view for testing
        self.mock_view = lambda request: HttpResponse('OK')

    def test_role_required_decorator(self):
        """Test the base role_required decorator."""
        # Decorate our mock view
        decorated_view = role_required('supervisor')(self.mock_view)
        
        # Test with supervisor (should succeed)
        request = self.factory.get('/')
        request.user = self.supervisor
        response = decorated_view(request)
        self.assertEqual(response.status_code, 200)
        
        # Test with wrong role (should raise PermissionDenied)
        request.user = self.client_user
        with self.assertRaises(PermissionDenied):
            decorated_view(request)
        
        # Test with superuser (should always succeed)
        request.user = self.admin
        response = decorated_view(request)
        self.assertEqual(response.status_code, 200)
        
        # Test with multiple roles
        multi_role_view = role_required(['supervisor', 'manager'])(self.mock_view)
        
        # Test with manager (should succeed)
        request.user = self.manager
        response = multi_role_view(request)
        self.assertEqual(response.status_code, 200)
        
        # Test with client (should fail)
        request.user = self.client_user
        with self.assertRaises(PermissionDenied):
            multi_role_view(request)

    def test_specific_role_decorators(self):
        """Test the specific role decorators."""
        # Test supervisor_required
        supervisor_view = supervisor_required(self.mock_view)
        request = self.factory.get('/')
        
        # Should succeed for supervisor
        request.user = self.supervisor
        response = supervisor_view(request)
        self.assertEqual(response.status_code, 200)
        
        # Should fail for manager
        request.user = self.manager
        with self.assertRaises(PermissionDenied):
            supervisor_view(request)
        
        # Test manager_required
        manager_view = manager_required(self.mock_view)
        
        # Should succeed for manager
        request.user = self.manager
        response = manager_view(request)
        self.assertEqual(response.status_code, 200)
        
        # Should fail for supervisor
        request.user = self.supervisor
        with self.assertRaises(PermissionDenied):
            manager_view(request)
        
        # Test client_required
        client_view = client_required(self.mock_view)
        
        # Should succeed for client
        request.user = self.client_user
        response = client_view(request)
        self.assertEqual(response.status_code, 200)
        
        # Should fail for supervisor
        request.user = self.supervisor
        with self.assertRaises(PermissionDenied):
            client_view(request)

    def test_combined_role_decorators(self):
        """Test decorators that allow multiple roles."""
        # Test supervisor_or_manager_required
        view = supervisor_or_manager_required(self.mock_view)
        request = self.factory.get('/')
        
        # Should succeed for supervisor
        request.user = self.supervisor
        response = view(request)
        self.assertEqual(response.status_code, 200)
        
        # Should succeed for manager
        request.user = self.manager
        response = view(request)
        self.assertEqual(response.status_code, 200)
        
        # Should fail for client
        request.user = self.client_user
        with self.assertRaises(PermissionDenied):
            view(request)
        
        # Test can_approve_shifts (same as supervisor_or_manager_required)
        approve_view = can_approve_shifts(self.mock_view)
        
        # Should succeed for manager
        request.user = self.manager
        response = approve_view(request)
        self.assertEqual(response.status_code, 200)
        
        # Should fail for client
        request.user = self.client_user
        with self.assertRaises(PermissionDenied):
            approve_view(request)