"""
Integration tests for the Vehicle Rental System.
Tests end-to-end workflows.
"""
import pytest
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models.dao.vehicle_dao import VehicleDAO
from models.dao.user_dao import UserDAO
from models.dao.rental_dao import RentalDAO
from models.services.rental_service import RentalService
from models.services.auth_service import AuthService
from models.services.analytics_service import AnalyticsService
from models.vehicle_model.car import Car
from models.vehicle_model.motorbike import Motorbike
from models.renter_model.corporate_user import CorporateUser
from models.renter_model.individual_user import IndividualUser
from models.renter_model.staff import Staff
from models.services.rental_period import RentalPeriod


class TestEndToEndRentalWorkflow:
    """Test complete rental workflows from login to return."""
    
    @pytest.fixture
    def setup_system(self, tmp_path):
        """Setup complete system with DAOs and services."""
        # Create DAOs
        vehicle_dao = VehicleDAO(str(tmp_path / "vehicles.pkl"))
        user_dao = UserDAO(str(tmp_path / "users.pkl"))
        rental_dao = RentalDAO(str(tmp_path / "rentals.pkl"))
        
        # Create services
        auth_service = AuthService(user_dao)
        rental_service = RentalService(vehicle_dao, user_dao, rental_dao)
        analytics_service = AnalyticsService(vehicle_dao, user_dao, rental_dao)
        
        # Add test vehicles
        car = Car("CAR001", "Toyota", "Camry", 2023, 50.0, 4)
        bike = Motorbike("BIKE001", "Yamaha", "R3", 2023, 30.0, 300)
        vehicle_dao.add(car)
        vehicle_dao.add(bike)
        
        # Add test users
        corporate = CorporateUser("CORP001", "ABC Corp", "corp@test.com", "corp001", "pass123")
        individual = IndividualUser("IND001", "John Doe", "john@test.com", "john001", "pass123")
        staff = Staff("STAFF001", "Admin", "admin@test.com", "admin", "admin123")
        user_dao.add(corporate)
        user_dao.add(individual)
        user_dao.add(staff)
        
        return {
            'auth_service': auth_service,
            'rental_service': rental_service,
            'analytics_service': analytics_service,
            'vehicle_dao': vehicle_dao,
            'user_dao': user_dao,
            'rental_dao': rental_dao,
            'car': car,
            'bike': bike,
            'corporate': corporate,
            'individual': individual,
            'staff': staff
        }
    
    def test_user_login_rent_return_workflow(self, setup_system):
        """Test: User logs in -> rents vehicle -> returns vehicle."""
        services = setup_system
        
        # Step 1: User authentication
        user = services['auth_service'].authenticate("corp001", "pass123")
        assert user is not None
        assert user.renter_id == "CORP001"
        
        # Step 2: Check if user can rent
        assert services['auth_service'].can_rent(user) == True
        
        # Step 3: Browse available vehicles
        period = RentalPeriod("01-01-2025 09:00", "05-01-2025 18:00")
        available = services['rental_service'].get_available_vehicles(period)
        assert len(available) == 2  # Both car and bike available
        
        # Step 4: Rent a vehicle
        rental_id, cost = services['rental_service'].rent_vehicle("CAR001", "CORP001", period)
        assert cost > 0
        
        # Step 5: Check vehicle is no longer available
        available = services['rental_service'].get_available_vehicles(period)
        assert len(available) == 1  # Only bike available
        
        # Step 6: Check user's active rentals
        rentals = services['rental_service'].get_user_rental_history("CORP001")
        assert len(rentals) == 1
        assert rentals[0].returned == False
        
        # Step 7: Return vehicle
        success = services['rental_service'].return_vehicle("CAR001", "CORP001")
        assert success == True
        
        # Step 8: Check vehicle is available again
        available = services['rental_service'].get_available_vehicles(period)
        assert len(available) == 2  # Both available again
        
        # Step 9: Check rental is marked as returned
        rentals = services['rental_service'].get_user_rental_history("CORP001")
        assert rentals[0].returned == True
    
    def test_multiple_rentals_workflow(self, setup_system):
        """Test: Multiple users renting different vehicles."""
        services = setup_system
        
        period = RentalPeriod("01-01-2025 09:00", "05-01-2025 18:00")
        
        # Corporate user rents car
        rental_id1, cost1 = services['rental_service'].rent_vehicle("CAR001", "CORP001", period)
        
        # Individual user rents bike
        rental_id2, cost2 = services['rental_service'].rent_vehicle("BIKE001", "IND001", period)
        
        # Check both vehicles are unavailable
        available = services['rental_service'].get_available_vehicles(period)
        assert len(available) == 0
        
        # Check rental records
        all_rentals = services['rental_service'].get_all_rental_records()
        assert len(all_rentals) == 2
    
    def test_overlapping_rental_prevented(self, setup_system):
        """Test: System prevents overlapping rentals."""
        services = setup_system
        
        period1 = RentalPeriod("01-01-2025 09:00", "05-01-2025 18:00")
        
        # First user rents car
        rental_id, cost = services['rental_service'].rent_vehicle("CAR001", "CORP001", period1)
        
        # Second user tries to rent same car for overlapping period
        period2 = RentalPeriod("03-01-2025 09:00", "07-01-2025 18:00")
        with pytest.raises(Exception):  # Should raise VehicleNotAvailableError or OverlappingBookingError
            services['rental_service'].rent_vehicle("CAR001", "IND001", period2)
    
    def test_corporate_discount_applied(self, setup_system):
        """Test: Corporate user gets 15% discount."""
        services = setup_system
        
        period = RentalPeriod("01-01-2025 09:00", "03-01-2025 18:00")  # 3 days
        
        # Corporate user rents car
        # Base: 50 * 3 = 150, with 15% discount = 127.5
        rental_id, cost = services['rental_service'].rent_vehicle("CAR001", "CORP001", period)
        assert cost == 127.5
    
    def test_individual_discount_applied(self, setup_system):
        """Test: Individual user gets 10% discount for 7+ days."""
        services = setup_system
        
        # Short rental (no discount)
        period_short = RentalPeriod("01-01-2025 09:00", "03-01-2025 18:00")  # 3 days
        rental_id_short, cost_short = services['rental_service'].rent_vehicle("CAR001", "IND001", period_short)
        # Base: 50 * 3 = 150, no discount
        assert cost_short == 150.0
        
        # Return and rent again for long period
        services['rental_service'].return_vehicle("CAR001", "IND001")
        
        # Long rental (10% discount)
        period_long = RentalPeriod("10-01-2025 09:00", "17-01-2025 18:00")  # 8 days
        rental_id_long, cost_long = services['rental_service'].rent_vehicle("CAR001", "IND001", period_long)
        # Base: 50 * 8 = 400, with 10% discount = 360
        assert cost_long == 360.0


class TestStaffManagementWorkflow:
    """Test staff administrative workflows."""
    
    @pytest.fixture
    def setup_system(self, tmp_path):
        """Setup system for staff tests."""
        vehicle_dao = VehicleDAO(str(tmp_path / "vehicles.pkl"))
        user_dao = UserDAO(str(tmp_path / "users.pkl"))
        rental_dao = RentalDAO(str(tmp_path / "rentals.pkl"))
        
        auth_service = AuthService(user_dao)
        analytics_service = AnalyticsService(vehicle_dao, user_dao, rental_dao)
        
        # Add staff user
        staff = Staff("STAFF001", "Admin", "admin@test.com", "admin", "admin123")
        user_dao.add(staff)
        
        return {
            'auth_service': auth_service,
            'analytics_service': analytics_service,
            'vehicle_dao': vehicle_dao,
            'user_dao': user_dao,
            'rental_dao': rental_dao,
            'staff': staff
        }
    
    def test_staff_login_and_permissions(self, setup_system):
        """Test: Staff login and check permissions."""
        services = setup_system
        
        # Staff authentication
        user = services['auth_service'].authenticate("admin", "admin123")
        assert user is not None
        assert services['auth_service'].is_staff(user) == True
        
        # Staff permissions
        assert services['auth_service'].can_manage_users(user) == True
        assert services['auth_service'].can_manage_vehicles(user) == True
        assert services['auth_service'].can_rent(user) == False
    
    def test_staff_view_analytics(self, setup_system):
        """Test: Staff can view analytics."""
        services = setup_system
        
        # Add some test data
        car = Car("CAR001", "Toyota", "Camry", 2023, 50.0, 4)
        services['vehicle_dao'].add(car)
        
        user = IndividualUser("IND001", "John Doe", "john@test.com", "john001", "pass123")
        services['user_dao'].add(user)
        
        # Create rental
        period = RentalPeriod("01-01-2025 09:00", "05-01-2025 18:00")
        car.add_rental("IND001", period, 200.0)
        user.add_rental_record(car.rental_history[0])
        
        from models.vehicle_model.vehicle import RentalRecord
        rental_record = RentalRecord("RENT_20250101090000_12345678", "CAR001", "IND001", period, 200.0)
        services['rental_dao'].add(rental_record)
        
        # Get analytics
        summary = services['analytics_service'].get_dashboard_summary()
        assert summary['total_vehicles'] == 1
        assert summary['total_users'] == 2  # Staff + Individual
        assert summary['total_revenue'] == 200.0


class TestDataPersistence:
    """Test data persistence with pickle."""
    
    def test_vehicle_persistence(self, tmp_path):
        """Test: Vehicles are persisted across sessions."""
        data_file = tmp_path / "vehicles.pkl"
        
        # Session 1: Add vehicles
        dao1 = VehicleDAO(str(data_file))
        car = Car("CAR001", "Toyota", "Camry", 2023, 50.0, 4)
        dao1.add(car)
        dao1.save()
        
        # Session 2: Load vehicles
        dao2 = VehicleDAO(str(data_file))
        dao2.load()
        loaded_car = dao2.get_by_id("CAR001")
        
        assert loaded_car is not None
        assert loaded_car.make == "Toyota"
        assert loaded_car.model == "Camry"
    
    def test_user_persistence(self, tmp_path):
        """Test: Users are persisted across sessions."""
        data_file = tmp_path / "users.pkl"
        
        # Session 1: Add user
        dao1 = UserDAO(str(data_file))
        user = CorporateUser("CORP001", "ABC Corp", "corp@test.com", "corp001", "pass123")
        dao1.add(user)
        dao1.save()
        
        # Session 2: Load user
        dao2 = UserDAO(str(data_file))
        dao2.load()
        loaded_user = dao2.get_by_id("CORP001")
        
        assert loaded_user is not None
        assert loaded_user.name == "ABC Corp"
        assert loaded_user.username == "corp001"

