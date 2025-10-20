from vehicle import Vehicle
from rental_period import RentalPeriod

class Truck(Vehicle):
    """
    Truck vehicle. Adds load capacity (tons) and applies a heavy-load surcharge.
    """
    def __init__(self, vehicle_id: str, make: str, model: str, year: int, daily_rate: float, load_capacity_tons: float = 2.0):
        super().__init__(vehicle_id, make, model, year, daily_rate)
        if load_capacity_tons < 0:
            raise ValueError("load_capacity_tons must be non-negative.")
        self.__load_capacity_tons = load_capacity_tons

    @property
    def load_capacity_tons(self) -> float:
        return self.__load_capacity_tons

    @load_capacity_tons.setter
    def load_capacity_tons(self, value: float) -> None:
        if value < 0:
            raise ValueError("load_capacity_tons must be non-negative.")
        self.__load_capacity_tons = value
        
    def calculate_rental(self, period: RentalPeriod, discount_factor: float) -> float:
        """
        Calculate rental cost for a truck.

        Base: daily_rate * days.
        If load_capacity_tons > 3.0: +10% surcharge.
        Add a flat logistics fee (20.0) at the end.

        Apply discount_factor to the resulting amount.
        """
        days = period.calculate_duration()
        base = self.daily_rate * days
        # Heavy loads => 10% surcharge
        if self.load_capacity_tons > 3.0:
            base *= 1.10
        # Trucks include a flat logistics fee
        base += 20.0
        return base * discount_factor

    def __str__(self) -> str:
        return f"Truck {self.year} {self.make} {self.model} (ID: {self.vehicle_id}, {self.load_capacity_tons}t) - ${self.daily_rate:.2f}/day"
