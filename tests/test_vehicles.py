"""
Unit tests for Vehicle classes (Car, Motorbike, Truck).
"""
import pytest
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models.vehicle_model.car import Car
from models.vehicle_model.motorbike import Motorbike
from models.vehicle_model.truck import Truck
from models.services.rental_period import RentalPeriod


class TestCar:
    """Test Car functionality."""
    
    def test_creation(self):
        """Test creating a car."""
        car = Car("CAR001", "Toyota", "Camry", 2023, 50.0, 4)
        assert car.vehicle_id == "CAR001"
        assert car.make == "Toyota"
        assert car.model == "Camry"
        assert car.year == 2023
        assert car.daily_rate == 50.0
        assert car.num_doors == 4
    
    def test_regular_car_rental_cost(self):
        """Test rental cost for regular car (4 doors)."""
        car = Car("CAR001", "Toyota", "Camry", 2023, 50.0, 4)
        period = RentalPeriod("01-01-2025 09:00", "03-01-2025 18:00")  # 3 days
        # Base: 50 * 3 = 150, 4 doors = no premium, discount = 1.0 (no discount)
        cost = car.calculate_rental(period, 1.0)
        assert cost == 150.0
    
    def test_sports_car_rental_cost(self):
        """Test rental cost for sports car (2 doors)."""
        car = Car("CAR002", "Mazda", "MX-5", 2023, 60.0, 2)
        period = RentalPeriod("01-01-2025 09:00", "03-01-2025 18:00")  # 3 days
        # Base: 60 * 3 = 180, 2 doors = +10% = 198, discount = 1.0
        cost = car.calculate_rental(period, 1.0)
        assert abs(cost - 198.0) < 0.01  # Allow small floating point errors
    
    def test_large_car_rental_cost(self):
        """Test rental cost for large car (5+ doors)."""
        car = Car("CAR003", "Honda", "Odyssey", 2023, 70.0, 5)
        period = RentalPeriod("01-01-2025 09:00", "03-01-2025 18:00")  # 3 days
        # Base: 70 * 3 = 210, 5 doors = +5% = 220.5, discount = 1.0
        cost = car.calculate_rental(period, 1.0)
        assert cost == 220.5
    
    def test_car_with_discount(self):
        """Test car rental with discount."""
        car = Car("CAR001", "Toyota", "Camry", 2023, 50.0, 4)
        period = RentalPeriod("01-01-2025 09:00", "03-01-2025 18:00")  # 3 days
        # Base: 150, discount 0.85 (15% off) = 127.5
        cost = car.calculate_rental(period, 0.85)
        assert cost == 127.5


class TestMotorbike:
    """Test Motorbike functionality."""
    
    def test_creation(self):
        """Test creating a motorbike."""
        bike = Motorbike("BIKE001", "Yamaha", "R3", 2023, 30.0, 300)
        assert bike.vehicle_id == "BIKE001"
        assert bike.make == "Yamaha"
        assert bike.engine_cc == 300
    
    def test_small_bike_rental_cost(self):
        """Test rental cost for small motorbike."""
        bike = Motorbike("BIKE001", "Yamaha", "R3", 2023, 30.0, 300)
        period = RentalPeriod("01-01-2025 09:00", "03-01-2025 18:00")  # 3 days
        # Base: (30 + 5 helmet) * 3 = 105, no premium for < 600cc, discount = 1.0
        cost = bike.calculate_rental(period, 1.0)
        assert cost == 105.0
    
    def test_large_bike_rental_cost(self):
        """Test rental cost for large motorbike."""
        bike = Motorbike("BIKE002", "Harley", "Sportster", 2023, 50.0, 883)
        period = RentalPeriod("01-01-2025 09:00", "03-01-2025 18:00")  # 3 days
        # Base: (50 + 5 helmet) * 3 = 165, >= 600cc = +5% = 173.25, discount = 1.0
        cost = bike.calculate_rental(period, 1.0)
        assert cost == 173.25


class TestTruck:
    """Test Truck functionality."""
    
    def test_creation(self):
        """Test creating a truck."""
        truck = Truck("TRUCK001", "Ford", "F-150", 2023, 80.0, 2.5)
        assert truck.vehicle_id == "TRUCK001"
        assert truck.make == "Ford"
        assert truck.load_capacity_tons == 2.5
    
    def test_small_truck_rental_cost(self):
        """Test rental cost for small truck."""
        truck = Truck("TRUCK001", "Ford", "F-150", 2023, 80.0, 2.0)
        period = RentalPeriod("01-01-2025 09:00", "03-01-2025 18:00")  # 3 days
        # Base: 80 * 3 = 240, no heavy load surcharge, + 20 logistics fee = 260, discount = 1.0
        cost = truck.calculate_rental(period, 1.0)
        assert cost == 260.0
    
    def test_heavy_truck_rental_cost(self):
        """Test rental cost for heavy truck."""
        truck = Truck("TRUCK002", "Ford", "F-250", 2023, 100.0, 4.0)
        period = RentalPeriod("01-01-2025 09:00", "03-01-2025 18:00")  # 3 days
        # Base: 100 * 3 = 300, > 3t = +10% = 330, + 20 logistics fee = 350, discount = 1.0
        cost = truck.calculate_rental(period, 1.0)
        assert cost == 350.0


class TestVehicleAvailability:
    """Test vehicle availability checking."""
    
    def test_initially_available(self):
        """Test that new vehicle is available."""
        car = Car("CAR001", "Toyota", "Camry", 2023, 50.0, 4)
        period = RentalPeriod("01-01-2025 09:00", "05-01-2025 18:00")
        assert car.is_available(period) == True
    
    def test_unavailable_during_rental(self):
        """Test that vehicle is unavailable during active rental."""
        car = Car("CAR001", "Toyota", "Camry", 2023, 50.0, 4)
        period1 = RentalPeriod("01-01-2025 09:00", "05-01-2025 18:00")
        period2 = RentalPeriod("03-01-2025 09:00", "07-01-2025 18:00")
        
        # Add a rental
        car.add_rental("USER001", period1, 150.0)
        
        # Should not be available during overlapping period
        assert car.is_available(period2) == False
    
    def test_available_after_return(self):
        """Test that vehicle becomes available after return."""
        car = Car("CAR001", "Toyota", "Camry", 2023, 50.0, 4)
        period1 = RentalPeriod("01-01-2025 09:00", "05-01-2025 18:00")
        period2 = RentalPeriod("03-01-2025 09:00", "07-01-2025 18:00")
        
        # Add and return rental
        car.add_rental("USER001", period1, 150.0)
        car.return_rental("USER001", period1)
        
        # Should be available now even for overlapping period
        assert car.is_available(period2) == True


class TestVehicleRentalHistory:
    """Test vehicle rental history tracking."""
    
    def test_rental_count(self):
        """Test rental count tracking."""
        car = Car("CAR001", "Toyota", "Camry", 2023, 50.0, 4)
        period1 = RentalPeriod("01-01-2025 09:00", "05-01-2025 18:00")
        period2 = RentalPeriod("10-01-2025 09:00", "15-01-2025 18:00")
        
        car.add_rental("USER001", period1, 150.0)
        car.return_rental("USER001", period1)
        car.add_rental("USER002", period2, 180.0)
        
        assert car.get_rental_count() == 2
    
    def test_total_revenue(self):
        """Test total revenue calculation."""
        car = Car("CAR001", "Toyota", "Camry", 2023, 50.0, 4)
        period1 = RentalPeriod("01-01-2025 09:00", "05-01-2025 18:00")
        period2 = RentalPeriod("10-01-2025 09:00", "15-01-2025 18:00")
        
        car.add_rental("USER001", period1, 150.0)
        car.add_rental("USER002", period2, 180.0)
        
        assert car.get_total_revenue() == 330.0

