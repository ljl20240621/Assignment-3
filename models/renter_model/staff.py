import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from renter_model.renter import Renter


class Staff(Renter):
    """
    Staff user (Administrator).
    
    Staff users have full administrative privileges:
    - Manage users (add/remove Corporate and Individual users)
    - Manage vehicles (add/remove vehicles)
    - View all rental histories
    - Access analytics
    
    Staff users don't rent vehicles themselves, so discount is irrelevant.
    """
    
    @property
    def kind(self) -> str:
        return "Staff"

    def discount_factor(self, days: int) -> float:
        """Staff users don't rent vehicles, so this always returns 1.0 (no discount)."""
        return 1.0

