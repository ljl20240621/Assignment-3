from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from vehicle import RentalRecord


class Renter(ABC):
    """
    Abstract base class for a user (renter).

    Subclasses must implement discount rules via ``discount_factor`` and expose a
    human-readable ``kind``. Instances are identified by ``renter_id`` and carry
    basic profile fields ``name`` and ``contact_info``.
    """

    def __init__(self, renter_id: str, name: str, contact_info: str, username: str = None, password: str = None):
        self.__renter_id = renter_id
        self.__name = name
        self.__contact_info = contact_info
        self.__username = username or renter_id  # Default username to renter_id
        self.__password = password or "password123"  # Default password
        # Rental history will be managed by VehicleRental system
        self.__rental_history: List["RentalRecord"] = []

    # ---- Properties ----
    @property
    def renter_id(self) -> str:
        return self.__renter_id

    @renter_id.setter
    def renter_id(self, value: str) -> None:
        self.__renter_id = value

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str) -> None:
        self.__name = value

    @property
    def contact_info(self) -> str:
        return self.__contact_info
    
    @contact_info.setter
    def contact_info(self, value: str) -> None:
        self.__contact_info = value

    @property
    def username(self) -> str:
        return self.__username

    @username.setter
    def username(self, value: str) -> None:
        self.__username = value

    @property
    def password(self) -> str:
        return self.__password

    @password.setter
    def password(self, value: str) -> None:
        self.__password = value

    # ---- Rental History Access ----
    @property
    def rental_history(self) -> Tuple["RentalRecord", ...]:
        """Return a read-only view of this user's rental history."""
        return tuple(self.__rental_history)

    def add_rental_record(self, rental_record: "RentalRecord") -> None:
        """Add a rental record to this user's history. Called by VehicleRental system."""
        self.__rental_history.append(rental_record)

    def get_rentals_by_vehicle(self, vehicle_id: str) -> List["RentalRecord"]:
        """Get all rental records for a specific vehicle."""
        return [r for r in self.__rental_history if r.vehicle_id == vehicle_id]

    def get_active_rentals(self) -> List["RentalRecord"]:
        """Get all unreturned rental records."""
        return [r for r in self.__rental_history if not r.returned]

    def get_returned_rentals(self) -> List["RentalRecord"]:
        """Get all returned rental records."""
        return [r for r in self.__rental_history if r.returned]

    # ---- Discount API ----
    @abstractmethod
    def discount_factor(self, days: int) -> float:
        """
        Return a multiplier in the inclusive range [0.0, 1.0] reflecting the
        discount policy for this renter, given a rental duration in days.

        Examples:
          - 1.0 → no discount
          - 0.9 → 10% off
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def kind(self) -> str:
        """Human-readable type name (e.g., "Individual", "Corporate")."""
        raise NotImplementedError

    def __str__(self) -> str:
        return f"{self.kind}User(ID={self.renter_id}, Name={self.name}, Contact={self.contact_info})"