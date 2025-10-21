"""
User Management Service - handles user CRUD operations (staff only).
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from renter_model.renter import Renter
from renter_model.corporate_user import CorporateUser
from renter_model.individual_user import IndividualUser
from renter_model.staff import Staff
from dao.user_dao import UserDAO


class UserManagementService:
    """
    Service for managing users (staff only operations).
    """
    
    def __init__(self, user_dao: UserDAO):
        self.user_dao = user_dao
    
    def create_user(self, user_type: str, renter_id: str, name: str, 
                   contact_info: str, username: str, password: str) -> Renter:
        """
        Create a new user.
        user_type: 'Individual', 'Corporate', or 'Staff'
        """
        if self.user_dao.exists(renter_id):
            raise ValueError(f"User with ID '{renter_id}' already exists.")
        
        if self.user_dao.find_by_username(username):
            raise ValueError(f"Username '{username}' already taken.")
        
        if user_type == "Individual":
            user = IndividualUser(renter_id, name, contact_info, username, password)
        elif user_type == "Corporate":
            user = CorporateUser(renter_id, name, contact_info, username, password)
        elif user_type == "Staff":
            user = Staff(renter_id, name, contact_info, username, password)
        else:
            raise ValueError(f"Invalid user type: {user_type}")
        
        self.user_dao.add(user)
        self.user_dao.save()
        
        return user
    
    def update_user(self, renter_id: str, name: str = None, 
                   contact_info: str = None, password: str = None) -> Renter:
        """Update user information."""
        user = self.user_dao.get_by_id(renter_id)
        if not user:
            raise ValueError(f"User with ID '{renter_id}' not found.")
        
        if name:
            user.name = name
        if contact_info:
            user.contact_info = contact_info
        if password:
            user.password = password
        
        self.user_dao.update(user)
        self.user_dao.save()
        
        return user
    
    def delete_user(self, renter_id: str) -> bool:
        """Delete a user."""
        success = self.user_dao.delete(renter_id)
        if success:
            self.user_dao.save()
        return success
    
    def get_user(self, renter_id: str) -> Renter:
        """Get a user by ID."""
        user = self.user_dao.get_by_id(renter_id)
        if not user:
            raise ValueError(f"User with ID '{renter_id}' not found.")
        return user
    
    def get_all_users(self):
        """Get all users."""
        return self.user_dao.get_all()
    
    def get_users_by_type(self, user_type: str):
        """Get users by type."""
        return self.user_dao.find_by_type(user_type)

