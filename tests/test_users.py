"""
Unit tests for User classes (Renter, CorporateUser, IndividualUser, Staff).
"""
import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models'))

from renter_model.corporate_user import CorporateUser
from renter_model.individual_user import IndividualUser
from renter_model.staff import Staff


class TestCorporateUser:
    """Test CorporateUser functionality."""
    
    def test_creation(self):
        """Test creating a corporate user."""
        user = CorporateUser("CORP001", "ABC Corp", "contact@abc.com", "corp001", "password123")
        assert user.renter_id == "CORP001"
        assert user.name == "ABC Corp"
        assert user.contact_info == "contact@abc.com"
        assert user.username == "corp001"
        assert user.kind == "Corporate"
    
    def test_discount_factor(self):
        """Test corporate discount is always 15%."""
        user = CorporateUser("CORP001", "ABC Corp", "contact@abc.com", "corp001", "password123")
        assert user.discount_factor(1) == 0.85
        assert user.discount_factor(7) == 0.85
        assert user.discount_factor(30) == 0.85
    
    def test_rental_history(self):
        """Test rental history starts empty."""
        user = CorporateUser("CORP001", "ABC Corp", "contact@abc.com", "corp001", "password123")
        assert len(user.rental_history) == 0


class TestIndividualUser:
    """Test IndividualUser functionality."""
    
    def test_creation(self):
        """Test creating an individual user."""
        user = IndividualUser("IND001", "John Doe", "john@example.com", "john001", "password123")
        assert user.renter_id == "IND001"
        assert user.name == "John Doe"
        assert user.kind == "Individual"
    
    def test_discount_short_rental(self):
        """Test no discount for rentals less than 7 days."""
        user = IndividualUser("IND001", "John Doe", "john@example.com", "john001", "password123")
        assert user.discount_factor(1) == 1.0
        assert user.discount_factor(6) == 1.0
    
    def test_discount_long_rental(self):
        """Test 10% discount for rentals 7+ days."""
        user = IndividualUser("IND001", "John Doe", "john@example.com", "john001", "password123")
        assert user.discount_factor(8) == 0.9
        assert user.discount_factor(14) == 0.9
        assert user.discount_factor(30) == 0.9


class TestStaff:
    """Test Staff functionality."""
    
    def test_creation(self):
        """Test creating a staff user."""
        user = Staff("STAFF001", "Admin User", "admin@system.com", "admin", "admin123")
        assert user.renter_id == "STAFF001"
        assert user.name == "Admin User"
        assert user.kind == "Staff"
    
    def test_discount_factor(self):
        """Test staff users have no discount (shouldn't rent)."""
        user = Staff("STAFF001", "Admin User", "admin@system.com", "admin", "admin123")
        assert user.discount_factor(1) == 1.0
        assert user.discount_factor(7) == 1.0


class TestUserProperties:
    """Test user property setters and getters."""
    
    def test_update_name(self):
        """Test updating user name."""
        user = IndividualUser("IND001", "John Doe", "john@example.com", "john001", "password123")
        user.name = "Jane Doe"
        assert user.name == "Jane Doe"
    
    def test_update_contact(self):
        """Test updating contact info."""
        user = IndividualUser("IND001", "John Doe", "john@example.com", "john001", "password123")
        user.contact_info = "jane@example.com"
        assert user.contact_info == "jane@example.com"
    
    def test_update_password(self):
        """Test updating password."""
        user = IndividualUser("IND001", "John Doe", "john@example.com", "john001", "password123")
        user.password = "newpassword456"
        assert user.password == "newpassword456"

