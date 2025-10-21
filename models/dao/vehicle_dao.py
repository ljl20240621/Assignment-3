"""
Vehicle Data Access Object - handles vehicle persistence.
"""
from typing import List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dao.base_dao import BaseDAO
from vehicle_model.vehicle import Vehicle


class VehicleDAO(BaseDAO[Vehicle]):
    """
    DAO for Vehicle entities.
    """
    
    def get_entity_id(self, entity: Vehicle) -> str:
        return entity.vehicle_id
    
    def find_by_type(self, vehicle_type: str) -> List[Vehicle]:
        """Find vehicles by type (Car, Motorbike, Truck)."""
        return [v for v in self._data.values() if v.__class__.__name__ == vehicle_type]
    
    def find_by_brand(self, make: str) -> List[Vehicle]:
        """Find vehicles by make/brand."""
        return [v for v in self._data.values() if v.make.lower() == make.lower()]
    
    def find_by_price_range(self, min_price: float, max_price: float) -> List[Vehicle]:
        """Find vehicles within a price range."""
        return [v for v in self._data.values() 
                if min_price <= v.daily_rate <= max_price]
    
    def filter_vehicles(self, vehicle_type: str = None, make: str = None, 
                       min_price: float = None, max_price: float = None) -> List[Vehicle]:
        """Filter vehicles by multiple criteria."""
        vehicles = self.get_all()
        
        if vehicle_type:
            vehicles = [v for v in vehicles if v.__class__.__name__ == vehicle_type]
        
        if make:
            vehicles = [v for v in vehicles if v.make.lower() == make.lower()]
        
        if min_price is not None:
            vehicles = [v for v in vehicles if v.daily_rate >= min_price]
        
        if max_price is not None:
            vehicles = [v for v in vehicles if v.daily_rate <= max_price]
        
        return vehicles

