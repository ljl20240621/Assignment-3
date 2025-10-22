"""
Analytics Service - handles business analytics and reporting.
"""
from typing import List, Dict, Tuple
from collections import Counter
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vehicle_model.vehicle import Vehicle, RentalRecord
from renter_model.renter import Renter
from dao.vehicle_dao import VehicleDAO
from dao.user_dao import UserDAO
from dao.rental_dao import RentalDAO


class AnalyticsService:
    """
    Service for handling analytics and reporting.
    """
    
    def __init__(self, vehicle_dao: VehicleDAO, user_dao: UserDAO, rental_dao: RentalDAO):
        self.vehicle_dao = vehicle_dao
        self.user_dao = user_dao
        self.rental_dao = rental_dao
    
    def get_most_rented_vehicles(self, limit: int = 10) -> List[Tuple[Vehicle, int]]:
        """
        Get the most rented vehicles.
        Returns a list of (vehicle, rental_count) tuples.
        """
        rental_counts = Counter()
        
        for record in self.rental_dao.get_all():
            rental_counts[record.vehicle_id] += 1
        
        results = []
        for vehicle_id, count in rental_counts.most_common(limit):
            vehicle = self.vehicle_dao.get_by_id(vehicle_id)
            if vehicle:
                results.append((vehicle, count))
        
        return results
    
    def get_least_rented_vehicles(self, limit: int = 10) -> List[Tuple[Vehicle, int]]:
        """
        Get the least rented vehicles.
        Returns a list of (vehicle, rental_count) tuples.
        """
        all_vehicles = self.vehicle_dao.get_all()
        rental_counts = Counter()
        
        # Count rentals for each vehicle
        for record in self.rental_dao.get_all():
            rental_counts[record.vehicle_id] += 1
        
        # Include vehicles with zero rentals
        for vehicle in all_vehicles:
            if vehicle.vehicle_id not in rental_counts:
                rental_counts[vehicle.vehicle_id] = 0
        
        # Get least common
        results = []
        for vehicle_id, count in rental_counts.most_common()[-limit:]:
            vehicle = self.vehicle_dao.get_by_id(vehicle_id)
            if vehicle:
                results.append((vehicle, count))
        
        return list(reversed(results))
    
    def get_total_revenue(self) -> float:
        """Get total revenue from all rentals."""
        return sum(record.total_cost for record in self.rental_dao.get_all())
    
    def get_revenue_by_vehicle_type(self) -> Dict[str, float]:
        """Get revenue breakdown by vehicle type."""
        revenue_by_type = {}
        
        for record in self.rental_dao.get_all():
            vehicle = self.vehicle_dao.get_by_id(record.vehicle_id)
            if vehicle:
                vehicle_type = vehicle.__class__.__name__
                revenue_by_type[vehicle_type] = revenue_by_type.get(vehicle_type, 0) + record.total_cost
        
        return revenue_by_type
    
    def get_revenue_by_user_type(self) -> Dict[str, float]:
        """Get revenue breakdown by user type."""
        revenue_by_type = {}
        
        for record in self.rental_dao.get_all():
            user = self.user_dao.get_by_id(record.renter_id)
            if user:
                user_type = user.kind
                revenue_by_type[user_type] = revenue_by_type.get(user_type, 0) + record.total_cost
        
        return revenue_by_type
    
    def get_vehicle_analytics(self, vehicle_id: str) -> Dict:
        """Get comprehensive analytics for a specific vehicle."""
        vehicle = self.vehicle_dao.get_by_id(vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle with ID '{vehicle_id}' not found.")
        
        rentals = [r for r in self.rental_dao.get_all() if r.vehicle_id == vehicle_id]
        active_rentals = [r for r in rentals if not r.returned]
        returned_rentals = [r for r in rentals if r.returned]
        
        total_revenue = sum(r.total_cost for r in rentals)
        total_days = sum(r.period.calculate_duration() for r in rentals)
        
        return {
            "vehicle_id": vehicle_id,
            "vehicle": str(vehicle),
            "total_rentals": len(rentals),
            "active_rentals": len(active_rentals),
            "returned_rentals": len(returned_rentals),
            "total_revenue": total_revenue,
            "total_rental_days": total_days,
            "average_rental_duration": total_days / len(rentals) if rentals else 0,
            "utilization_rate": len(returned_rentals) / len(rentals) if rentals else 0
        }
    
    def get_user_analytics(self, renter_id: str) -> Dict:
        """Get comprehensive analytics for a specific user."""
        user = self.user_dao.get_by_id(renter_id)
        if not user:
            raise ValueError(f"User with ID '{renter_id}' not found.")
        
        rentals = list(user.rental_history)
        active_rentals = user.get_active_rentals()
        returned_rentals = user.get_returned_rentals()
        
        total_spent = sum(r.total_cost for r in rentals)
        total_days = sum(r.period.calculate_duration() for r in rentals)
        
        return {
            "renter_id": renter_id,
            "user_name": user.name,
            "user_type": user.kind,
            "total_rentals": len(rentals),
            "active_rentals": len(active_rentals),
            "returned_rentals": len(returned_rentals),
            "total_spent": total_spent,
            "total_rental_days": total_days,
            "average_rental_cost": total_spent / len(rentals) if rentals else 0,
            "average_rental_duration": total_days / len(rentals) if rentals else 0
        }
    
    def get_user_activity_logs(self, limit: int = 100) -> List[Dict]:
        """
        Get user activity logs (rental and return events).
        Returns a list of activity dictionaries sorted by date.
        """
        activities = []
        
        for record in self.rental_dao.get_all():
            user = self.user_dao.get_by_id(record.renter_id)
            vehicle = self.vehicle_dao.get_by_id(record.vehicle_id)
            
            # Rental event
            activities.append({
                "type": "rental",
                "date": record.period.start_date,
                "user": user.name if user else "Unknown",
                "user_id": record.renter_id,
                "vehicle": str(vehicle) if vehicle else record.vehicle_id,
                "vehicle_id": record.vehicle_id,
                "cost": record.total_cost,
                "period": str(record.period)
            })
            
            # Return event (if returned)
            if record.returned:
                activities.append({
                    "type": "return",
                    "date": record.period.end_date,
                    "user": user.name if user else "Unknown",
                    "user_id": record.renter_id,
                    "vehicle": str(vehicle) if vehicle else record.vehicle_id,
                    "vehicle_id": record.vehicle_id,
                    "cost": record.total_cost,
                    "period": str(record.period)
                })
        
        # Sort by date (most recent first)
        from datetime import datetime
        activities.sort(
            key=lambda x: datetime.strptime(x["date"], "%d-%m-%Y %H:%M"),
            reverse=True
        )
        
        return activities[:limit]
    
    def get_dashboard_summary(self) -> Dict:
        """Get a summary of key metrics for the dashboard."""
        all_rentals = self.rental_dao.get_all()
        active_rentals = self.rental_dao.find_active_rentals()
        overdue_rentals = self.rental_dao.find_overdue_rentals()
        
        all_vehicles = self.vehicle_dao.get_all()
        all_users = self.user_dao.get_all()
        
        return {
            "total_vehicles": len(all_vehicles),
            "total_users": len(all_users),
            "total_rentals": len(all_rentals),
            "active_rentals": len(active_rentals),
            "overdue_rentals": len(overdue_rentals),
            "total_revenue": self.get_total_revenue(),
            "revenue_by_vehicle_type": self.get_revenue_by_vehicle_type(),
            "revenue_by_user_type": self.get_revenue_by_user_type()
        }

