"""
Rental Data Access Object - handles rental record persistence.
"""
from typing import List
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dao.base_dao import BaseDAO
from vehicle_model.vehicle import RentalRecord


class RentalDAO(BaseDAO[RentalRecord]):
    """
    DAO for RentalRecord entities.
    """
    
    def __init__(self, data_file: str):
        super().__init__(data_file)
        self._records: List[RentalRecord] = []
    
    def get_entity_id(self, entity: RentalRecord) -> str:
        # Generate a unique ID for rental records
        return f"{entity.vehicle_id}_{entity.renter_id}_{entity.period.start_date}"
    
    def add(self, entity: RentalRecord) -> None:
        """Add a rental record."""
        self._records.append(entity)
    
    def get_all(self) -> List[RentalRecord]:
        """Get all rental records."""
        return self._records
    
    def find_by_vehicle(self, vehicle_id: str) -> List[RentalRecord]:
        """Find all rentals for a specific vehicle."""
        return [r for r in self._records if r.vehicle_id == vehicle_id]
    
    def find_by_user(self, renter_id: str) -> List[RentalRecord]:
        """Find all rentals for a specific user."""
        return [r for r in self._records if r.renter_id == renter_id]
    
    def find_active_rentals(self) -> List[RentalRecord]:
        """Find all active (unreturned) rentals."""
        return [r for r in self._records if not r.returned]
    
    def find_returned_rentals(self) -> List[RentalRecord]:
        """Find all returned rentals."""
        return [r for r in self._records if r.returned]
    
    def find_overdue_rentals(self) -> List[RentalRecord]:
        """Find all overdue rentals (active rentals past their end date)."""
        today = datetime.today()
        overdue = []
        for record in self._records:
            if not record.returned:
                end_date = record.period.end_dt
                if end_date < today:
                    overdue.append(record)
        return overdue
    
    def load(self) -> None:
        """Load rental records from pickle file."""
        try:
            import pickle
            with open(self.data_file, 'rb') as f:
                self._records = pickle.load(f)
        except FileNotFoundError:
            self._records = []
        except Exception as e:
            raise Exception(f"Failed to load rental data from {self.data_file}: {e}")
    
    def save(self) -> None:
        """Save rental records to pickle file."""
        try:
            import pickle
            with open(self.data_file, 'wb') as f:
                pickle.dump(self._records, f)
        except Exception as e:
            raise Exception(f"Failed to save rental data to {self.data_file}: {e}")
    
    def clear(self) -> None:
        """Clear all rental records."""
        self._records.clear()

