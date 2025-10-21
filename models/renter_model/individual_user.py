import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from renter_model.renter import Renter


class IndividualUser(Renter):
    """
    Individual user.

    Discount policy:
      - Rentals of 7 days or more receive a 10% discount (factor 0.9)
      - Otherwise no discount (factor 1.0)
    """
    @property
    def kind(self) -> str:
        return "Individual"

    def discount_factor(self, days: int) -> float:
        """Return the discount factor based on rental duration in days."""
        return 0.9 if days >= 7 else 1.0