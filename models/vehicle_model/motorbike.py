import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vehicle_model.vehicle import Vehicle
from services.rental_period import RentalPeriod

class Motorbike(Vehicle):
    """
    Motorbike vehicle. Adds engine displacement (cc) and a simple helmet fee.
    """
    def __init__(self, vehicle_id: str, make: str, model: str, year: int, daily_rate: float, engine_cc: int = 150):
        super().__init__(vehicle_id, make, model, year, daily_rate)
        if engine_cc < 0:
            raise ValueError("engine_cc must be non-negative.")
        self.__engine_cc = engine_cc

    @property
    def engine_cc(self) -> int:
        return self.__engine_cc

    @engine_cc.setter
    def engine_cc(self, value: int) -> None:
        if value < 0:
            raise ValueError("engine_cc must be non-negative.")
        self.__engine_cc = value
        
    def calculate_rental(self, period: RentalPeriod, discount_factor: float) -> float:
        """
        Calculate rental cost for a motorbike.

        Base per day: daily_rate + helmet_fee_per_day (5.0).
        If engine_cc >= 600: +5% premium on the base.

        Apply discount_factor to the final amount.
        """
        days = period.calculate_duration()
        helmet_fee_per_day = 5.0
        base = (self.daily_rate + helmet_fee_per_day) * days
        # Slight premium for high displacement
        if self.engine_cc >= 600:
            base *= 1.05
        return base * discount_factor

    def __str__(self) -> str:
        return f"Motorbike {self.year} {self.make} {self.model} (ID: {self.vehicle_id}, {self.engine_cc}cc) - ${self.daily_rate:.2f}/day"

