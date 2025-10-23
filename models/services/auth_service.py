"""
Authentication Service - handles user authentication and session management.
"""
from typing import Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from renter_model.renter import Renter
from dao.user_dao import UserDAO


class AuthService:
    """
    Service for handling user authentication.
    """
    
    def __init__(self, user_dao: UserDAO):
        self.user_dao = user_dao
    
    def authenticate(self, username: str, password: str) -> Optional[Renter]:
        """
        Authenticate a user with username and password.
        Returns the user object if successful, None otherwise.
        """
        return self.user_dao.authenticate(username, password)
    
    def is_staff(self, user: Renter) -> bool:
        """Check if a user is staff."""
        if user is None:
            return False
        return user.kind == "Staff"
    
    def is_corporate(self, user: Renter) -> bool:
        """Check if a user is a corporate user."""
        if user is None:
            return False
        return user.kind == "Corporate"
    
    def is_individual(self, user: Renter) -> bool:
        """Check if a user is an individual user."""
        if user is None:
            return False
        return user.kind == "Individual"
    
    def can_rent(self, user: Renter) -> bool:
        """Check if a user can rent vehicles (staff cannot)."""
        if user is None:
            return False
        return user.kind in ["Corporate", "Individual"]
    
    def can_manage_users(self, user: Renter) -> bool:
        """Check if a user can manage other users (staff only)."""
        if user is None:
            return False
        return user.kind == "Staff"
    
    def can_manage_vehicles(self, user: Renter) -> bool:
        """Check if a user can manage vehicles (staff only)."""
        if user is None:
            return False
        return user.kind == "Staff"
    
    def can_view_all_rentals(self, user: Renter) -> bool:
        """Check if a user can view all rental histories (staff only)."""
        if user is None:
            return False
        return user.kind == "Staff"

