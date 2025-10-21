import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from renter_model.renter import Renter


class CorporateUser(Renter):
    """
    Corporate user.

    Discount policy:
      - Always applies a fixed 15% discount (factor 0.85)
    """
    @property
    def kind(self) -> str:
        return "Corporate"

    def discount_factor(self, days: int) -> float:
        """Return the fixed corporate discount factor (0.85)."""
        return 0.85