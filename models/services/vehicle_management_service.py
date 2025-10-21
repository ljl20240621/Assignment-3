"""
Vehicle Management Service - handles vehicle CRUD operations (staff only).
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vehicle_model.vehicle import Vehicle
from vehicle_model.car import Car
from vehicle_model.motorbike import Motorbike
from vehicle_model.truck import Truck
from dao.vehicle_dao import VehicleDAO


class VehicleManagementService:
    """
    Service for managing vehicles (staff only operations).
    """
    
    def __init__(self, vehicle_dao: VehicleDAO):
        self.vehicle_dao = vehicle_dao
    
    def create_vehicle(self, vehicle_type: str, vehicle_id: str, make: str, 
                      model: str, year: int, daily_rate: float, **kwargs) -> Vehicle:
        """
        Create a new vehicle.
        vehicle_type: 'Car', 'Motorbike', or 'Truck'
        kwargs: type-specific attributes (num_doors, engine_cc, load_capacity_tons)
        """
        if self.vehicle_dao.exists(vehicle_id):
            raise ValueError(f"Vehicle with ID '{vehicle_id}' already exists.")
        
        if vehicle_type == "Car":
            num_doors = kwargs.get("num_doors", 4)
            vehicle = Car(vehicle_id, make, model, year, daily_rate, num_doors)
        elif vehicle_type == "Motorbike":
            engine_cc = kwargs.get("engine_cc", 150)
            vehicle = Motorbike(vehicle_id, make, model, year, daily_rate, engine_cc)
        elif vehicle_type == "Truck":
            load_capacity_tons = kwargs.get("load_capacity_tons", 2.0)
            vehicle = Truck(vehicle_id, make, model, year, daily_rate, load_capacity_tons)
        else:
            raise ValueError(f"Invalid vehicle type: {vehicle_type}")
        
        self.vehicle_dao.add(vehicle)
        self.vehicle_dao.save()
        
        return vehicle
    
    def update_vehicle(self, vehicle_id: str, make: str = None, model: str = None,
                      year: int = None, daily_rate: float = None, **kwargs) -> Vehicle:
        """Update vehicle information."""
        vehicle = self.vehicle_dao.get_by_id(vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle with ID '{vehicle_id}' not found.")
        
        if make:
            vehicle.make = make
        if model:
            vehicle.model = model
        if year:
            vehicle.year = year
        if daily_rate:
            vehicle.daily_rate = daily_rate
        
        # Update type-specific attributes
        if isinstance(vehicle, Car) and "num_doors" in kwargs:
            vehicle.num_doors = kwargs["num_doors"]
        elif isinstance(vehicle, Motorbike) and "engine_cc" in kwargs:
            vehicle.engine_cc = kwargs["engine_cc"]
        elif isinstance(vehicle, Truck) and "load_capacity_tons" in kwargs:
            vehicle.load_capacity_tons = kwargs["load_capacity_tons"]
        
        self.vehicle_dao.update(vehicle)
        self.vehicle_dao.save()
        
        return vehicle
    
    def delete_vehicle(self, vehicle_id: str) -> bool:
        """Delete a vehicle."""
        success = self.vehicle_dao.delete(vehicle_id)
        if success:
            self.vehicle_dao.save()
        return success
    
    def get_vehicle(self, vehicle_id: str) -> Vehicle:
        """Get a vehicle by ID."""
        vehicle = self.vehicle_dao.get_by_id(vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle with ID '{vehicle_id}' not found.")
        return vehicle
    
    def get_all_vehicles(self):
        """Get all vehicles."""
        return self.vehicle_dao.get_all()
    
    def get_vehicles_by_type(self, vehicle_type: str):
        """Get vehicles by type."""
        return self.vehicle_dao.find_by_type(vehicle_type)

