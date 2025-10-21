"""
Initialize the Vehicle Rental System with sample data.
Run this script once to populate the system with demo users and vehicles.
"""
import os
import sys

# Add models to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'models'))

from models.dao.vehicle_dao import VehicleDAO
from models.dao.user_dao import UserDAO
from models.dao.rental_dao import RentalDAO
from models.vehicle_model.car import Car
from models.vehicle_model.motorbike import Motorbike
from models.vehicle_model.truck import Truck
from models.renter_model.corporate_user import CorporateUser
from models.renter_model.individual_user import IndividualUser
from models.renter_model.staff import Staff


def init_data():
    """Initialize the system with sample data."""
    print("=" * 60)
    print("Vehicle Rental System - Data Initialization")
    print("=" * 60)
    
    # Create data directory
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Initialize DAOs
    vehicle_dao = VehicleDAO(os.path.join(data_dir, 'vehicles.pkl'))
    user_dao = UserDAO(os.path.join(data_dir, 'users.pkl'))
    rental_dao = RentalDAO(os.path.join(data_dir, 'rentals.pkl'))
    
    print("\n[1/3] Creating sample users...")
    
    # Create Staff Users
    staff1 = Staff("STAFF001", "Admin User", "admin@vehiclerental.com", "admin", "admin123")
    user_dao.add(staff1)
    print("  ✓ Created staff: admin (password: admin123)")
    
    # Create Corporate Users
    corp1 = CorporateUser("CORP001", "ABC Corporation", "contact@abc.com", "corp001", "password123")
    corp2 = CorporateUser("CORP002", "XYZ Industries", "info@xyz.com", "corp002", "password123")
    user_dao.add(corp1)
    user_dao.add(corp2)
    print("  ✓ Created corporate user: corp001 (password: password123)")
    print("  ✓ Created corporate user: corp002 (password: password123)")
    
    # Create Individual Users
    ind1 = IndividualUser("IND001", "John Doe", "john.doe@email.com", "john001", "password123")
    ind2 = IndividualUser("IND002", "Jane Smith", "jane.smith@email.com", "jane002", "password123")
    ind3 = IndividualUser("IND003", "Bob Johnson", "bob.johnson@email.com", "bob003", "password123")
    user_dao.add(ind1)
    user_dao.add(ind2)
    user_dao.add(ind3)
    print("  ✓ Created individual user: john001 (password: password123)")
    print("  ✓ Created individual user: jane002 (password: password123)")
    print("  ✓ Created individual user: bob003 (password: password123)")
    
    # Save users
    user_dao.save()
    print(f"\n  Total users created: {user_dao.count()}")
    
    print("\n[2/3] Creating sample vehicles...")
    
    # Create Cars
    car1 = Car("CAR001", "Toyota", "Camry", 2023, 50.0, 4)
    car2 = Car("CAR002", "Honda", "Accord", 2023, 55.0, 4)
    car3 = Car("CAR003", "Mazda", "MX-5", 2023, 65.0, 2)
    car4 = Car("CAR004", "Toyota", "Corolla", 2022, 45.0, 4)
    car5 = Car("CAR005", "Honda", "Civic", 2023, 48.0, 4)
    car6 = Car("CAR006", "Ford", "Mustang", 2023, 85.0, 2)
    car7 = Car("CAR007", "Honda", "Odyssey", 2023, 75.0, 5)
    
    vehicle_dao.add(car1)
    vehicle_dao.add(car2)
    vehicle_dao.add(car3)
    vehicle_dao.add(car4)
    vehicle_dao.add(car5)
    vehicle_dao.add(car6)
    vehicle_dao.add(car7)
    print("  ✓ Created 7 cars")
    
    # Create Motorbikes
    bike1 = Motorbike("BIKE001", "Yamaha", "YZF-R3", 2023, 35.0, 321)
    bike2 = Motorbike("BIKE002", "Honda", "CBR500R", 2023, 40.0, 471)
    bike3 = Motorbike("BIKE003", "Kawasaki", "Ninja 650", 2023, 45.0, 649)
    bike4 = Motorbike("BIKE004", "Harley-Davidson", "Sportster", 2023, 60.0, 883)
    bike5 = Motorbike("BIKE005", "Suzuki", "GSX-R750", 2023, 55.0, 750)
    
    vehicle_dao.add(bike1)
    vehicle_dao.add(bike2)
    vehicle_dao.add(bike3)
    vehicle_dao.add(bike4)
    vehicle_dao.add(bike5)
    print("  ✓ Created 5 motorbikes")
    
    # Create Trucks
    truck1 = Truck("TRUCK001", "Ford", "F-150", 2023, 80.0, 1.5)
    truck2 = Truck("TRUCK002", "Chevrolet", "Silverado", 2023, 85.0, 2.0)
    truck3 = Truck("TRUCK003", "RAM", "1500", 2023, 90.0, 2.5)
    truck4 = Truck("TRUCK004", "Ford", "F-250", 2023, 110.0, 4.0)
    truck5 = Truck("TRUCK005", "Toyota", "Tundra", 2023, 95.0, 3.0)
    
    vehicle_dao.add(truck1)
    vehicle_dao.add(truck2)
    vehicle_dao.add(truck3)
    vehicle_dao.add(truck4)
    vehicle_dao.add(truck5)
    print("  ✓ Created 5 trucks")
    
    # Save vehicles
    vehicle_dao.save()
    print(f"\n  Total vehicles created: {vehicle_dao.count()}")
    
    print("\n[3/3] Initializing rental records...")
    
    # Initialize empty rental records
    rental_dao.save()
    print("  ✓ Rental records initialized (empty)")
    
    print("\n" + "=" * 60)
    print("✅ Initialization Complete!")
    print("=" * 60)
    
    print("\nSample Login Credentials:")
    print("-" * 60)
    print("Staff Account:")
    print("  Username: admin")
    print("  Password: admin123")
    print("\nCorporate Accounts:")
    print("  Username: corp001 | Password: password123 (15% discount)")
    print("  Username: corp002 | Password: password123 (15% discount)")
    print("\nIndividual Accounts:")
    print("  Username: john001 | Password: password123 (10% for 7+ days)")
    print("  Username: jane002 | Password: password123 (10% for 7+ days)")
    print("  Username: bob003  | Password: password123 (10% for 7+ days)")
    print("-" * 60)
    
    print("\nVehicle Summary:")
    print("-" * 60)
    print(f"  Cars: 7 vehicles (Daily rate: $45-$85)")
    print(f"  Motorbikes: 5 vehicles (Daily rate: $35-$60)")
    print(f"  Trucks: 5 vehicles (Daily rate: $80-$110)")
    print(f"  Total: {vehicle_dao.count()} vehicles")
    print("-" * 60)
    
    print("\nYou can now start the application with:")
    print("  python app.py")
    print("\nThen visit: http://localhost:5000")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        init_data()
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

