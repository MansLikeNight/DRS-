from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import UserProfile


class AccountsTestCase(TestCase):
    def setUp(self):
        # Create test users with different roles
        self.client = Client()
        
        # Create a supervisor
        self.supervisor = User.objects.create_user(
            username='supervisor',
            password='testpass123',
            email='supervisor@test.com'
        )
        self.supervisor.profile.role = UserProfile.ROLE_SUPERVISOR
        self.supervisor.profile.save()
        
        # Create a manager
        self.manager = User.objects.create_user(
            username='manager',
            password='testpass123',
            email='manager@test.com'
        )
        self.manager.profile.role = UserProfile.ROLE_MANAGER
        self.manager.profile.save()
        
        # Create a client user
        self.client_user = User.objects.create_user(
            username='client',
            password='testpass123',
            email='client@test.com'
        )
        self.client_user.profile.role = UserProfile.ROLE_CLIENT
        self.client_user.profile.save()

    def test_user_registration(self):
        """Test user registration process."""
        # Test registration with valid data
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password1': 'complex_password123',
            'password2': 'complex_password123',
            'role': UserProfile.ROLE_SUPERVISOR,
            'company': 'Test Company',
            'phone': '1234567890'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # Verify profile was created with correct data
        user = User.objects.get(username='newuser')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.role, UserProfile.ROLE_SUPERVISOR)
        self.assertEqual(user.profile.company, 'Test Company')
        
        # Test registration with invalid data
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser2',
            'email': 'invalid_email',
            'password1': 'pass1',
            'password2': 'pass2',
            'role': 'invalid_role'
        })
        self.assertEqual(response.status_code, 200)  # Stay on form
        self.assertFalse(User.objects.filter(username='newuser2').exists())

    def test_login_required(self):
        """Test login required decorator."""
        # Try accessing profile page without login
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Login and try again
        self.client.login(username='supervisor', password='testpass123')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)

    def test_profile_update(self):
        """Test profile update functionality."""
        self.client.login(username='supervisor', password='testpass123')
        
        # Update profile
        response = self.client.post(reverse('accounts:profile'), {
            'role': UserProfile.ROLE_SUPERVISOR,
            'company': 'Updated Company',
            'phone': '0987654321'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verify changes
        profile = UserProfile.objects.get(user=self.supervisor)
        self.assertEqual(profile.company, 'Updated Company')
        self.assertEqual(profile.phone, '0987654321')

    def test_role_required_decorator(self):
        """Test role-based access control."""
        from core.views import shift_create  # Import the view that requires supervisor role
        
        # Try accessing supervisor-only view as client
        self.client.login(username='client', password='testpass123')
        response = self.client.get(reverse('core:shift_create'))
        self.assertEqual(response.status_code, 403)  # Permission denied
        
        # Try as supervisor
        self.client.login(username='supervisor', password='testpass123')
        response = self.client.get(reverse('core:shift_create'))
        self.assertEqual(response.status_code, 200)  # Access granted

    def test_user_roles_and_permissions(self):
        """Test role-based permissions system."""
        # Test supervisor permissions
        self.client.login(username='supervisor', password='testpass123')
        supervisor = User.objects.get(username='supervisor')
        self.assertTrue(supervisor.profile.is_supervisor)
        self.assertFalse(supervisor.profile.is_manager)
        self.assertFalse(supervisor.profile.is_client)
        
        # Test manager permissions
        self.client.login(username='manager', password='testpass123')
        manager = User.objects.get(username='manager')
        self.assertTrue(manager.profile.is_manager)
        self.assertFalse(manager.profile.is_supervisor)
        self.assertFalse(manager.profile.is_client)
        
        # Test client permissions
        self.client.login(username='client', password='testpass123')
        client = User.objects.get(username='client')
        self.assertTrue(client.profile.is_client)
        self.assertFalse(client.profile.is_supervisor)
        self.assertFalse(client.profile.is_manager)