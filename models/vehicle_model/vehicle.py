from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple

from rental_period import RentalPeriod
from exceptions import OverlappingBookingError


@dataclass
class RentalRecord:
    """
    Shared record of a single rental booking.
    This record is shared between vehicles and users for consistency.
    """
    vehicle_id: str
    renter_id: str
    period: RentalPeriod
    total_cost: float
    returned: bool = False
    
class Vehicle(ABC):
    """
    Abstract base class for all vehicles. 
    Attributes mirror Assignment 1's Car, but generalized for all vehicle types.
    """
    def __init__(self, vehicle_id: str, make: str, model: str, year: int, daily_rate: float):
        self.__vehicle_id = vehicle_id
        self.__make = make
        self.__model = model
        self.__year = year
        if daily_rate <= 0:
            raise ValueError("Daily rate must be positive")
        self.__daily_rate = daily_rate
        # History of rentals (past and future). Overlap checks will scan all.
        self.__rental_history: List[RentalRecord] = []

    # ---- Properties (encapsulated access) ----
    @property
    def vehicle_id(self) -> str:
        return self.__vehicle_id

    @vehicle_id.setter
    def vehicle_id(self, value: str) -> None:
        self.__vehicle_id = value

    @property
    def make(self) -> str:
        return self.__make

    @make.setter
    def make(self, value: str) -> None:
        self.__make = value

    @property
    def model(self) -> str:
        return self.__model

    @model.setter
    def model(self, value: str) -> None:
        self.__model = value

    @property
    def year(self) -> int:
        return self.__year

    @year.setter
    def year(self, value: int) -> None:
        self.__year = value
    @property
    def daily_rate(self) -> float:
        return self.__daily_rate

    @daily_rate.setter
    def daily_rate(self, value: float) -> None:
        if value <= 0:
            raise ValueError("Daily rate must be positive.")
        self.__daily_rate = value
        
    @property
    def rental_history(self) -> Tuple[RentalRecord, ...]:
        return tuple(self.__rental_history)     

    # ---- Core behaviour ----
    def is_available(self, new_period: RentalPeriod) -> bool:
        """
        True if the requested period does not overlap with any active (unreturned) rental.
        Only unreturned bookings block those dates; returned rentals do not.
        """
        for rec in self.__rental_history:
            if not rec.returned and rec.period.overlaps_with(new_period):
                return False
        return True
    
    def add_rental(self, renter_id: str, period: RentalPeriod, total_cost: float) -> None:
        """
        Record a new rental in history.
        Note: This method is called by VehicleRental system after creating shared RentalRecord.
        """
        # Defensive check: ensure vehicle is still available for this period
        if not self.is_available(period):
            raise OverlappingBookingError(f"Vehicle '{self.vehicle_id}' is no longer available for {period}.")
        
        # Create rental record (this will be the same reference as in VehicleRental)
        rental_record = RentalRecord(vehicle_id=self.vehicle_id, renter_id=renter_id, period=period, total_cost=total_cost)
        self.__rental_history.append(rental_record)


    def get_total_rental_days(self) -> int:
        """Get total rental days across all history (including returned rentals)."""
        return sum(rec.period.calculate_duration() for rec in self.__rental_history)

    def get_total_revenue(self) -> float:
        """Get total revenue from all rentals (including returned rentals)."""
        return sum(rec.total_cost for rec in self.__rental_history)

    def get_rental_count(self) -> int:
        """Get total number of rentals in history."""
        return len(self.__rental_history)

    def get_active_rentals(self) -> List[RentalRecord]:
        """Get all unreturned rental records."""
        return [rec for rec in self.__rental_history if not rec.returned]

    def get_returned_rentals(self) -> List[RentalRecord]:
        """Get all returned rental records."""
        return [rec for rec in self.__rental_history if rec.returned]

    def return_rental(self, renter_id: str, period: Optional[RentalPeriod] = None) -> bool:
        """
        Mark a matching rental as returned. If period is None, return the most recent
        unreturned rental for this renter. Returns True if something was marked returned.
        """
        candidates = [r for r in self.__rental_history if r.renter_id == renter_id and not r.returned]
        if period is not None:
            for r in candidates:
                if r.period.start_date == period.start_date and r.period.end_date == period.end_date:
                    r.returned = True
                    return True
            return False
        # No period given: pick the last outstanding rental for that renter
        if candidates:
            candidates[-1].returned = True
            return True
        return False
    
    # ----- Abstract methods -----
    @abstractmethod
    def calculate_rental(self, period: RentalPeriod, discount_factor: float) -> float:
        """
        Compute the base cost for this vehicle and period, then apply a discount factor.
        Subclasses must define their own base-cost logic.
        Return the final (discounted) cost.
        """
        raise NotImplementedError

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError