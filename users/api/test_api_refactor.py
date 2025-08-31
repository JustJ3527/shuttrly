"""
Test file to verify API refactoring works correctly.
This file tests the basic functionality of our refactored API views.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
import json

User = get_user_model()


class APIRefactorTestCase(TestCase):
    """Test case for refactored API views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.api_urls = {
            'register_step1': '/api/v1/auth/register/step1/',
            'register_step2': '/api/v1/auth/register/step2/',
            'register_complete': '/api/v1/auth/register/complete/',
            'login': '/api/v1/auth/login/',
            'check_username': '/api/v1/auth/check-username/',
        }
    
    def test_register_step1_validation(self):
        """Test that register step 1 properly validates data"""
        # Test with invalid email
        response = self.client.post(self.api_urls['register_step1'], {
            'email': 'invalid-email'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error']['code'], 'AUTH_301')  # VALIDATION_ERROR
        
        # Test with valid email
        response = self.client.post(self.api_urls['register_step1'], {
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_register_step1_duplicate_email(self):
        """Test that register step 1 prevents duplicate emails"""
        # Create a user first
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Try to register with same email
        response = self.client.post(self.api_urls['register_step1'], {
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error']['code'], 'AUTH_101')  # EMAIL_ALREADY_EXISTS
    
    def test_username_availability_check(self):
        """Test username availability checking"""
        # Test with invalid username
        response = self.client.post(self.api_urls['check_username'], {
            'username': 'a'  # Too short
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test with valid username
        response = self.client.post(self.api_urls['check_username'], {
            'username': 'testuser'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['available'])
    
    def test_login_validation(self):
        """Test that login properly validates credentials"""
        # Test with missing fields
        response = self.client.post(self.api_urls['login'], {
            'identifier': 'testuser'
            # Missing password
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test with non-existent user
        response = self.client.post(self.api_urls['login'], {
            'identifier': 'nonexistent',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error']['code'], 'AUTH_002')  # USER_NOT_FOUND
    
    def test_error_response_structure(self):
        """Test that error responses have the correct structure"""
        # Test validation error
        response = self.client.post(self.api_urls['register_step1'], {
            'email': 'invalid-email'
        })
        
        self.assertIn('success', response.data)
        self.assertFalse(response.data['success'])
        self.assertIn('error', response.data)
        self.assertIn('code', response.data['error'])
        self.assertIn('message', response.data['error'])
        self.assertIn('type', response.data['error'])
        self.assertEqual(response.data['error']['type'], 'authentication_error')


if __name__ == '__main__':
    # This allows running the tests directly
    import django
    django.setup()
    
    # Run the tests
    import unittest
    unittest.main()
