import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vehicle_model.vehicle import Vehicle
from services.rental_period import RentalPeriod

class Car(Vehicle):
    """
    Car vehicle. Adds number of doors and uses a straightforward base-cost rule.
    """   
    def __init__(self, vehicle_id: str, make: str, model: str, year: int, daily_rate: float, num_doors: int = 4):
        super().__init__(vehicle_id, make, model, year, daily_rate)
        self.__num_doors = num_doors

    @property
    def num_doors(self) -> int:
        return self.__num_doors

    @num_doors.setter
    def num_doors(self, value: int) -> None:
        self.__num_doors = value
        
    def calculate_rental(self, period: RentalPeriod, discount_factor: float) -> float:
        """
        Calculate rental cost for a car.

        Base rule: daily_rate * days.
        Surcharges by door count (mutually exclusive):
          - <= 2 doors: +10% (sports)
          - 3-4 doors: +0% (regular)
          - >= 5 doors: +5% (large)

        The final price applies the provided discount_factor at the end.
        """
        days = period.calculate_duration()
        base = self.daily_rate * days
        
        # Simplified door-based pricing (3 categories)
        if self.num_doors <= 2:
            base *= 1.10  # 10% premium for sports cars (2 doors or less)
        elif self.num_doors <= 4:
            base *= 1.00  # Standard pricing for regular cars (3-4 doors)
        else:  # 5+ doors
            base *= 1.05  # 5% premium for large vehicles (5+ doors)
            
        return base * discount_factor

    def __str__(self) -> str:
        # Simplified vehicle type classification
        if self.num_doors <= 2:
            vehicle_type = "Sports Car"
        elif self.num_doors <= 4:
            vehicle_type = "Regular Car"
        else:  # 5+ doors
            vehicle_type = "Large Vehicle"
            
        return f"Car {self.year} {self.make} {self.model} (ID: {self.vehicle_id}, {self.num_doors} doors, {vehicle_type}) - ${self.daily_rate:.2f}/day"