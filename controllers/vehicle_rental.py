import atexit
import pickle
from typing import Dict, Optional, Tuple, List

from exceptions import (
    PersistenceError,
    OverlappingBookingError,
    UserNotFoundError,
    VehicleNotAvailableError,
    VehicleNotFoundError,
    ReturnNotFoundError,
)
from rental_period import RentalPeriod
from renter import Renter
from vehicle import Vehicle, RentalRecord


class VehicleRental:
    """
    Core service: manages vehicles and users; supports renting, returning,
    listing, and persistence via pickling.
    """

    def __init__(self, autosave_path: str = "vehicle_data.pkl"):
        self.__vehicles: Dict[str, Vehicle] = {}
        self.__users: Dict[str, Renter] = {}
        self.__autosave_path = autosave_path
        # Shared rental records for consistency between vehicles and users
        self.__all_rental_records: List[RentalRecord] = []
        # auto-save on interpreter exit
        atexit.register(self.save)

    # ---------- Persistence ----------
    @classmethod
    def load(cls, path: str = "vehicle_data.pkl") -> "VehicleRental":
        """
        Create a VehicleRental instance and populate it from a pickle file, if available.
        """
        vr = cls(autosave_path=path)
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            vehicles = data.get("vehicles", {})
            users = data.get("users", {})
            rental_records = data.get("rental_records", [])
            if isinstance(vehicles, dict):
                for vid, v in vehicles.items():
                    vr.__vehicles[vid] = v
            if isinstance(users, dict):
                for uid, u in users.items():
                    vr.__users[uid] = u
            if isinstance(rental_records, list):
                vr.__all_rental_records = rental_records
        except FileNotFoundError:
            # fresh start is fine
            pass
        except Exception as ex:
            raise PersistenceError(f"Failed loading data from '{path}': {ex}") from ex
        return vr

    def save(self) -> None:
        """
        Save the whole system state to the autosave path via pickle.
        """
        try:
            with open(self.__autosave_path, "wb") as f:
                pickle.dump({
                    "vehicles": self.__vehicles, 
                    "users": self.__users,
                    "rental_records": self.__all_rental_records
                }, f)
        except Exception as ex:
            # Convert to our domain exception
            raise PersistenceError(f"Failed saving data to '{self.__autosave_path}': {ex}")   

    # ---------- Encapsulated collections ----------
    @property
    def vehicles(self) -> Tuple[Vehicle, ...]:
        """Read-only snapshot of all vehicles."""
        return tuple(self.__vehicles.values())

    @property
    def users(self) -> Tuple[Renter, ...]:
        """Read-only snapshot of all users."""
        return tuple(self.__users.values())

    # ---------- Registration ----------
    def add_vehicle(self, vehicle: Vehicle) -> None:
        """Add a new vehicle with uniqueness check and auto-save."""
        if vehicle.vehicle_id in self.__vehicles:
            raise ValueError(f"Vehicle with ID '{vehicle.vehicle_id}' already exists.")
        self.__vehicles[vehicle.vehicle_id] = vehicle
        self.save()  # Auto-save after adding

    def add_user(self, user: Renter) -> None:
        """Add a new user with uniqueness check and auto-save."""
        if user.renter_id in self.__users:
            raise ValueError(f"User with ID '{user.renter_id}' already exists.")
        self.__users[user.renter_id] = user
        self.save()  # Auto-save after adding

    # ---------- Lookups ----------
    def find_vehicle(self, vehicle_id: str) -> Optional[Vehicle]:
        return self.__vehicles.get(vehicle_id)

    def find_user(self, renter_id: str) -> Optional[Renter]:
        return self.__users.get(renter_id)

    # ---------- Operations ----------
    def rent_vehicle(self, vehicle_id: str, renter_id: str, period: RentalPeriod) -> None:
        """
        Attempt to rent a vehicle for the given user and period.
        Returns the total cost if successful.
        Raises domain exceptions on error.
        """
        vehicle = self.find_vehicle(vehicle_id)
        if not vehicle:
            raise VehicleNotFoundError(vehicle_id)
        user = self.find_user(renter_id)
        if not user:
            raise UserNotFoundError(renter_id)

        if not vehicle.is_available(period):
            raise OverlappingBookingError(vehicle_id, period)

        days = period.calculate_duration()
        factor = user.discount_factor(days)
        total = vehicle.calculate_rental(period, discount_factor=factor)
        
        # Create shared rental record
        rental_record = RentalRecord(
            vehicle_id=vehicle_id,
            renter_id=renter_id,
            period=period,
            total_cost=total
        )
        
        # Add to shared records
        self.__all_rental_records.append(rental_record)
        
        # Add to vehicle's history
        vehicle.add_rental(renter_id=renter_id, period=period, total_cost=total)
        
        # Add to user's history
        user.add_rental_record(rental_record)
        
        return total

    def return_vehicle(self, vehicle_id: str, renter_id: str, period: Optional[RentalPeriod] = None) -> None:
        """
        Return a previously rented vehicle for the given user.
        If period is omitted, returns the most recent outstanding rental for that user.
        Raises if the vehicle or user is unknown, or if no matching rental is found.
        """
        vehicle = self.find_vehicle(vehicle_id)
        if not vehicle:
            raise VehicleNotFoundError(f"Vehicle '{vehicle_id}' not found.")
        user = self.find_user(renter_id)
        if not user:
            raise UserNotFoundError(f"User '{renter_id}' not found.")

        ok = vehicle.return_rental(renter_id, period=period)
        if not ok:
            raise ReturnNotFoundError("No matching outstanding rental to return.")

    # ---------- Displays ----------
    def display_available_vehicles(self, when: Optional[RentalPeriod] = None) -> List[Vehicle]:
        """
        Print and return vehicles available for the specified period (default: today).

        Returns a list of Vehicle objects. Also prints them for convenience.
        """
        if when is None:
            from datetime import datetime
            today = datetime.today().strftime("%d-%m-%Y")
            from rental_period import RentalPeriod
            when = RentalPeriod(today, today)

        print("=== Available Vehicles ===")
        result: List[Vehicle] = [v for v in self.__vehicles.values() if v.is_available(when)]
        for v in result:
            print(v)
        return result

    def display_rented_vehicles(self, when: Optional[RentalPeriod] = None) -> List[Vehicle]:
        """
        Print and return vehicles that are booked for the specified period (default: today).

        Returns a list of Vehicle objects. Also prints them for convenience.
        """
        if when is None:
            from datetime import datetime
            today = datetime.today().strftime("%d-%m-%Y")
            from rental_period import RentalPeriod
            when = RentalPeriod(today, today)

        print("=== Rented Vehicles ===")
        result: List[Vehicle] = [v for v in self.__vehicles.values() if not v.is_available(when)]
        for v in result:
            print(v)
        return result

    def display_users(self) -> List[Renter]:
        """Print and return all users as a list."""
        print("=== Users ===")
        result: List[Renter] = list(self.__users.values())
        for u in result:
            print(u)
        return result

    # ---------- Rental History Management ----------
    def get_user_rental_history(self, renter_id: str) -> List[RentalRecord]:
        """Get all rental records for a specific user."""
        user = self.find_user(renter_id)
        if not user:
            raise UserNotFoundError(renter_id)
        return list(user.rental_history)

    def get_vehicle_rental_history(self, vehicle_id: str) -> List[RentalRecord]:
        """Get all rental records for a specific vehicle."""
        vehicle = self.find_vehicle(vehicle_id)
        if not vehicle:
            raise VehicleNotFoundError(vehicle_id)
        return list(vehicle.rental_history)

    def get_all_rental_records(self) -> List[RentalRecord]:
        """Get all rental records in the system."""
        return list(self.__all_rental_records)

    def display_user_rentals(self, renter_id: str) -> List[RentalRecord]:
        """Display and return rental history for a specific user."""
        user = self.find_user(renter_id)
        if not user:
            raise UserNotFoundError(renter_id)
        
        rentals = list(user.rental_history)
        print(f"=== Rental History for {user.name} ({renter_id}) ===")
        if not rentals:
            print("No rental history found.")
        else:
            for rental in rentals:
                status = "RETURNED" if rental.returned else "ACTIVE"
                print(f"Vehicle {rental.vehicle_id}: {rental.period} - ${rental.total_cost:.2f} [{status}]")
        return rentals

    # ---------- Business Analytics (using full rental history) ----------
    def get_vehicle_analytics(self, vehicle_id: str) -> dict:
        """Get comprehensive analytics for a vehicle using full rental history."""
        vehicle = self.find_vehicle(vehicle_id)
        if not vehicle:
            raise VehicleNotFoundError(vehicle_id)
        
        all_rentals = vehicle.rental_history
        active_rentals = vehicle.get_active_rentals()
        returned_rentals = vehicle.get_returned_rentals()
        
        return {
            "vehicle_id": vehicle_id,
            "total_rentals": len(all_rentals),
            "active_rentals": len(active_rentals),
            "returned_rentals": len(returned_rentals),
            "total_revenue": vehicle.get_total_revenue(),
            "total_rental_days": vehicle.get_total_rental_days(),
            "average_rental_duration": vehicle.get_total_rental_days() / len(all_rentals) if all_rentals else 0,
            "utilization_rate": len(returned_rentals) / len(all_rentals) if all_rentals else 0
        }

    def get_user_analytics(self, renter_id: str) -> dict:
        """Get comprehensive analytics for a user using full rental history."""
        user = self.find_user(renter_id)
        if not user:
            raise UserNotFoundError(renter_id)
        
        all_rentals = list(user.rental_history)
        active_rentals = user.get_active_rentals()
        returned_rentals = user.get_returned_rentals()
        
        total_spent = sum(rental.total_cost for rental in all_rentals)
        total_days = sum(rental.period.calculate_duration() for rental in all_rentals)
        
        return {
            "renter_id": renter_id,
            "user_name": user.name,
            "user_type": user.kind,
            "total_rentals": len(all_rentals),
            "active_rentals": len(active_rentals),
            "returned_rentals": len(returned_rentals),
            "total_spent": total_spent,
            "total_rental_days": total_days,
            "average_rental_cost": total_spent / len(all_rentals) if all_rentals else 0,
            "average_rental_duration": total_days / len(all_rentals) if all_rentals else 0
        }

    def display_vehicle_analytics(self, vehicle_id: str) -> dict:
        """Display and return vehicle analytics."""
        analytics = self.get_vehicle_analytics(vehicle_id)
        print(f"=== Vehicle Analytics for {vehicle_id} ===")
        print(f"Total Rentals: {analytics['total_rentals']}")
        print(f"Active Rentals: {analytics['active_rentals']}")
        print(f"Returned Rentals: {analytics['returned_rentals']}")
        print(f"Total Revenue: ${analytics['total_revenue']:.2f}")
        print(f"Total Rental Days: {analytics['total_rental_days']}")
        print(f"Average Rental Duration: {analytics['average_rental_duration']:.1f} days")
        print(f"Utilization Rate: {analytics['utilization_rate']:.1%}")
        return analytics

    def display_user_analytics(self, renter_id: str) -> dict:
        """Display and return user analytics."""
        analytics = self.get_user_analytics(renter_id)
        print(f"=== User Analytics for {analytics['user_name']} ({renter_id}) ===")
        print(f"User Type: {analytics['user_type']}")
        print(f"Total Rentals: {analytics['total_rentals']}")
        print(f"Active Rentals: {analytics['active_rentals']}")
        print(f"Returned Rentals: {analytics['returned_rentals']}")
        print(f"Total Spent: ${analytics['total_spent']:.2f}")
        print(f"Total Rental Days: {analytics['total_rental_days']}")
        print(f"Average Rental Cost: ${analytics['average_rental_cost']:.2f}")
        print(f"Average Rental Duration: {analytics['average_rental_duration']:.1f} days")
        return analytics