"""
Unit tests for AuthService.
"""
import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models'))

from services.auth_service import AuthService
from dao.user_dao import UserDAO
from renter_model.corporate_user import CorporateUser
from renter_model.individual_user import IndividualUser
from renter_model.staff import Staff


class TestAuthService:
    """Test authentication service."""
    
    @pytest.fixture
    def setup(self, tmp_path):
        """Setup test environment with users."""
        data_file = tmp_path / "test_users.pkl"
        user_dao = UserDAO(str(data_file))
        
        # Add test users
        staff = Staff("STAFF001", "Admin", "admin@test.com", "admin", "admin123")
        corporate = CorporateUser("CORP001", "ABC Corp", "corp@test.com", "corp001", "pass123")
        individual = IndividualUser("IND001", "John Doe", "john@test.com", "john001", "pass123")
        
        user_dao.add(staff)
        user_dao.add(corporate)
        user_dao.add(individual)
        
        auth_service = AuthService(user_dao)
        
        return auth_service, staff, corporate, individual
    
    def test_successful_authentication(self, setup):
        """Test successful user authentication."""
        auth_service, staff, corporate, individual = setup
        
        # Test staff authentication
        user = auth_service.authenticate("admin", "admin123")
        assert user is not None
        assert user.renter_id == "STAFF001"
        
        # Test corporate authentication
        user = auth_service.authenticate("corp001", "pass123")
        assert user is not None
        assert user.renter_id == "CORP001"
    
    def test_failed_authentication_wrong_password(self, setup):
        """Test failed authentication with wrong password."""
        auth_service, _, _, _ = setup
        
        user = auth_service.authenticate("admin", "wrongpassword")
        assert user is None
    
    def test_failed_authentication_wrong_username(self, setup):
        """Test failed authentication with wrong username."""
        auth_service, _, _, _ = setup
        
        user = auth_service.authenticate("nonexistent", "password")
        assert user is None
    
    def test_is_staff(self, setup):
        """Test staff role checking."""
        auth_service, staff, corporate, individual = setup
        
        assert auth_service.is_staff(staff) == True
        assert auth_service.is_staff(corporate) == False
        assert auth_service.is_staff(individual) == False
    
    def test_is_corporate(self, setup):
        """Test corporate role checking."""
        auth_service, staff, corporate, individual = setup
        
        assert auth_service.is_corporate(staff) == False
        assert auth_service.is_corporate(corporate) == True
        assert auth_service.is_corporate(individual) == False
    
    def test_can_rent(self, setup):
        """Test rental permission checking."""
        auth_service, staff, corporate, individual = setup
        
        assert auth_service.can_rent(staff) == False
        assert auth_service.can_rent(corporate) == True
        assert auth_service.can_rent(individual) == True
    
    def test_can_manage_users(self, setup):
        """Test user management permission checking."""
        auth_service, staff, corporate, individual = setup
        
        assert auth_service.can_manage_users(staff) == True
        assert auth_service.can_manage_users(corporate) == False
        assert auth_service.can_manage_users(individual) == False

