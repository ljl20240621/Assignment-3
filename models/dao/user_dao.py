"""
User Data Access Object - handles user persistence.
"""
from typing import Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dao.base_dao import BaseDAO
from renter_model.renter import Renter


class UserDAO(BaseDAO[Renter]):
    """
    DAO for User (Renter) entities.
    """
    
    def get_entity_id(self, entity: Renter) -> str:
        return entity.renter_id
    
    def find_by_username(self, username: str) -> Optional[Renter]:
        """Find a user by username."""
        for user in self._data.values():
            if user.username == username:
                return user
        return None
    
    def authenticate(self, username: str, password: str) -> Optional[Renter]:
        """Authenticate a user with username and password."""
        user = self.find_by_username(username)
        if user and user.password == password:
            return user
        return None
    
    def find_by_type(self, user_type: str) -> list[Renter]:
        """Find users by type (Individual, Corporate, Staff)."""
        return [u for u in self._data.values() if u.kind == user_type]

