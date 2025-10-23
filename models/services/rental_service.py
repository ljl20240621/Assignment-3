"""
Rental Service - handles vehicle rental business logic.
"""
from typing import List, Optional, Dict
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vehicle_model.vehicle import Vehicle, RentalRecord
from renter_model.renter import Renter
from services.rental_period import RentalPeriod
from dao.vehicle_dao import VehicleDAO
from dao.user_dao import UserDAO
from dao.rental_dao import RentalDAO


class RentalService:
    """
    Service for handling vehicle rental operations.
    """
    
    def __init__(self, vehicle_dao: VehicleDAO, user_dao: UserDAO, rental_dao: RentalDAO):
        self.vehicle_dao = vehicle_dao
        self.user_dao = user_dao
        self.rental_dao = rental_dao
    
    def rent_vehicle(self, vehicle_id: str, renter_id: str, period: RentalPeriod) -> tuple[str, float]:
        """
        Rent a vehicle for a user.
        Returns (rental_id, total_cost).
        Raises exceptions if vehicle or user not found, or if vehicle not available.
        """
        vehicle = self.vehicle_dao.get_by_id(vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle with ID '{vehicle_id}' not found.")
        
        user = self.user_dao.get_by_id(renter_id)
        if not user:
            raise ValueError(f"User with ID '{renter_id}' not found.")
        
        if not vehicle.is_available(period):
            raise ValueError(f"Vehicle '{vehicle_id}' is not available for the requested period.")
        
        # Calculate cost
        days = period.calculate_duration()
        discount_factor = user.discount_factor(days)
        total_cost = vehicle.calculate_rental(period, discount_factor)
        
        # Create rental record and get rental ID
        rental_id = vehicle.add_rental(renter_id, period, total_cost)
        
        # Get the created rental record
        rental_record = vehicle.get_rental_by_id(rental_id)
        
        # Add to user's history
        user.add_rental_record(rental_record)
        
        # Add to rental records
        self.rental_dao.add(rental_record)
        
        # Save changes
        self.vehicle_dao.save()
        self.user_dao.save()
        self.rental_dao.save()
        
        return rental_id, total_cost
    
    def return_vehicle_by_id(self, rental_id: str) -> bool:
        """
        Return a vehicle by rental ID.
        Returns True if successful, False otherwise.
        """
        # Find the rental record
        rental_record = None
        for record in self.rental_dao.get_all():
            if record.rental_id == rental_id:
                rental_record = record
                break
        
        if not rental_record:
            return False
        
        if rental_record.returned:
            return True  # Already returned
        
        # Get the vehicle and mark as returned
        vehicle = self.vehicle_dao.get_by_id(rental_record.vehicle_id)
        if not vehicle:
            return False
        
        # Mark as returned in vehicle
        success = vehicle.return_rental(rental_id)
        
        if success:
            # Update the user's rental history
            user = self.user_dao.get_by_id(rental_record.renter_id)
            if user:
                for record in user.rental_history:
                    if record.rental_id == rental_id:
                        record.returned = True
                        break
            
            # Update the shared rental record
            rental_record.returned = True
            
            # Save changes
            self.vehicle_dao.save()
            self.user_dao.save()
            self.rental_dao.save()
        
        return success
    
    def return_vehicle(self, vehicle_id: str, renter_id: str, period: Optional[RentalPeriod] = None) -> bool:
        """
        Return a rented vehicle (idempotent operation).
        Returns True if successful or already returned, False otherwise.
        """
        vehicle = self.vehicle_dao.get_by_id(vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle with ID '{vehicle_id}' not found.")
        
        user = self.user_dao.get_by_id(renter_id)
        if not user:
            raise ValueError(f"User with ID '{renter_id}' not found.")
        
        # Check if already returned in user's history (idempotent check)
        already_returned = False
        for record in user.rental_history:
            if (record.vehicle_id == vehicle_id and 
                record.renter_id == renter_id):
                if period is None or (record.period.start_date == period.start_date and 
                                     record.period.end_date == period.end_date):
                    if record.returned:
                        already_returned = True
                    break
        
        if already_returned:
            return True  # Already returned, consider it successful
        
        # Mark as returned in vehicle's history
        success = vehicle.return_rental(renter_id, period)
        
        if success:
            # Update the user's rental history
            for record in user.rental_history:
                if (record.vehicle_id == vehicle_id and 
                    record.renter_id == renter_id and 
                    not record.returned):
                    if period is None or (record.period.start_date == period.start_date and 
                                         record.period.end_date == period.end_date):
                        record.returned = True
                        break
            
            # Update the shared rental record in rental_dao
            for record in self.rental_dao.get_all():
                if (record.vehicle_id == vehicle_id and 
                    record.renter_id == renter_id and 
                    not record.returned):
                    if period is None or (record.period.start_date == period.start_date and 
                                         record.period.end_date == period.end_date):
                        record.returned = True
                        break
            
            # Save changes to all data sources
            self.vehicle_dao.save()
            self.user_dao.save()
            self.rental_dao.save()
        
        return success
    
    def get_available_vehicles(self, period: Optional[RentalPeriod] = None) -> List[Vehicle]:
        """Get all available vehicles for a given period."""
        if period is None:
            today = datetime.today().strftime("%d-%m-%Y")
            period = RentalPeriod(today, today)
        
        return [v for v in self.vehicle_dao.get_all() if v.is_available(period)]
    
    def get_rented_vehicles(self, period: Optional[RentalPeriod] = None) -> List[Vehicle]:
        """Get all rented vehicles for a given period."""
        if period is None:
            today = datetime.today().strftime("%d-%m-%Y")
            period = RentalPeriod(today, today)
        
        return [v for v in self.vehicle_dao.get_all() if not v.is_available(period)]
    
    def filter_vehicles(self, vehicle_type: str = None, make: str = None,
                       min_price: float = None, max_price: float = None,
                       period: Optional[RentalPeriod] = None) -> List[Vehicle]:
        """Filter vehicles by multiple criteria and availability."""
        vehicles = self.vehicle_dao.filter_vehicles(vehicle_type, make, min_price, max_price)
        
        if period:
            vehicles = [v for v in vehicles if v.is_available(period)]
        
        return vehicles
    
    def get_user_rental_history(self, renter_id: str) -> List[RentalRecord]:
        """Get rental history for a user."""
        user = self.user_dao.get_by_id(renter_id)
        if not user:
            raise ValueError(f"User with ID '{renter_id}' not found.")
        return list(user.rental_history)
    
    def get_vehicle_rental_history(self, vehicle_id: str) -> List[RentalRecord]:
        """Get rental history for a vehicle."""
        vehicle = self.vehicle_dao.get_by_id(vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle with ID '{vehicle_id}' not found.")
        return list(vehicle.rental_history)
    
    def get_all_rental_records(self) -> List[RentalRecord]:
        """Get all rental records."""
        return self.rental_dao.get_all()
    
    def get_overdue_rentals(self) -> List[RentalRecord]:
        """Get all overdue rentals."""
        return self.rental_dao.find_overdue_rentals()
    
    def get_active_rentals(self) -> List[RentalRecord]:
        """Get all active rentals."""
        return self.rental_dao.find_active_rentals()

