from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple
import sys
import os
import uuid
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.rental_period import RentalPeriod
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Define custom exception locally to avoid import issues
class OverlappingBookingError(Exception):
    """Raised when a requested rental period overlaps with an existing booking."""
    def __init__(self, message: str):
        super().__init__(message)


@dataclass
class RentalRecord:
    """
    Shared record of a single rental booking.
    This record is shared between vehicles and users for consistency.
    """
    rental_id: str  # Unique identifier for this rental
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
    
    def add_rental(self, renter_id: str, period: RentalPeriod, total_cost: float) -> str:
        """
        Record a new rental in history.
        Returns the unique rental ID.
        """
        # Defensive check: ensure vehicle is still available for this period
        if not self.is_available(period):
            raise OverlappingBookingError(f"Vehicle '{self.vehicle_id}' is no longer available for {period}.")
        
        # Generate unique rental ID
        rental_id = self._generate_rental_id()
        
        # Create rental record
        rental_record = RentalRecord(
            rental_id=rental_id,
            vehicle_id=self.vehicle_id, 
            renter_id=renter_id, 
            period=period, 
            total_cost=total_cost
        )
        self.__rental_history.append(rental_record)
        return rental_id
    
    def _generate_rental_id(self) -> str:
        """Generate a unique rental ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"RENT_{timestamp}_{unique_id}"


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
    
    def get_rental_by_id(self, rental_id: str) -> Optional[RentalRecord]:
        """Get a rental record by its ID."""
        for rental in self.__rental_history:
            if rental.rental_id == rental_id:
                return rental
        return None

    def return_rental(self, rental_id: str) -> bool:
        """
        Mark a rental as returned by rental ID.
        Returns True if the rental was found and marked as returned.
        """
        for rental in self.__rental_history:
            if rental.rental_id == rental_id and not rental.returned:
                rental.returned = True
                return True
        return False
    
    def return_rental_by_renter(self, renter_id: str, period: Optional[RentalPeriod] = None) -> bool:
        """
        Mark a matching rental as returned by renter ID and optional period.
        This is a backward compatibility method.
        """
        candidates = [r for r in self.__rental_history if r.renter_id == renter_id and not r.returned]
        
        if not candidates:
            return False
            
        if period is not None:
            # Try exact match first
            for r in candidates:
                if r.period.start_date == period.start_date and r.period.end_date == period.end_date:
                    r.returned = True
                    return True
            
            # If no exact match, try to find the most recent rental that overlaps
            for r in candidates:
                if (r.period.start_date == period.start_date or 
                    (r.period.start_date <= period.start_date and r.period.end_date >= period.start_date)):
                    r.returned = True
                    return True
            return False
        else:
            # No period given: pick the most recent outstanding rental for that renter
            candidates.sort(key=lambda x: x.period.start_date, reverse=True)
            candidates[0].returned = True
            return True
    
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