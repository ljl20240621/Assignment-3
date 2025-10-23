#!/usr/bin/env python3
"""
Data Initialization Script
Initialize vehicles and three user accounts for the Vehicle Rental System.
"""

import os
import sys
import pickle
from datetime import datetime

# Add models to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'models'))

from models.dao.vehicle_dao import VehicleDAO
from models.dao.user_dao import UserDAO
from models.dao.rental_dao import RentalDAO
from models.renter_model.individual_user import IndividualUser
from models.renter_model.corporate_user import CorporateUser
from models.renter_model.staff import Staff
from models.vehicle_model.car import Car
from models.vehicle_model.motorbike import Motorbike
from models.vehicle_model.truck import Truck

def generate_user_id(user_type):
    """Generate user ID based on type."""
    if user_type == 'staff':
        return 'STAFF001'
    elif user_type == 'corporate':
        return 'CORP001'
    else:
        return 'USER001'

def initialize_data():
    """Initialize vehicles and user accounts."""
    
    # Create data directory
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # File paths
    vehicle_file = os.path.join(data_dir, 'vehicles.pkl')
    user_file = os.path.join(data_dir, 'users.pkl')
    rental_file = os.path.join(data_dir, 'rentals.pkl')
        
    # Initialize DAOs
    vehicle_dao = VehicleDAO(vehicle_file)
    user_dao = UserDAO(user_file)
    rental_dao = RentalDAO(rental_file)
    
    # Initialize vehicles
    print("📦 Creating vehicles...")
    vehicles = [
        # Cars
        Car("CAR001", "Toyota", "Camry", 2020, 50.0, 4),
        Car("CAR002", "Honda", "Civic", 2019, 45.0, 4),
        Car("CAR003", "BMW", "X5", 2021, 120.0, 5),
        Car("CAR004", "Mercedes", "C-Class", 2020, 100.0, 4),
        Car("CAR005", "Audi", "A4", 2019, 90.0, 4),
        Car("CAR006", "Ford", "Mustang", 2021, 85.0, 2),
        Car("CAR007", "Tesla", "Model 3", 2022, 110.0, 4),
        Car("CAR008", "Nissan", "Altima", 2020, 55.0, 4),
        Car("CAR009", "Hyundai", "Elantra", 2019, 40.0, 4),
        Car("CAR010", "Kia", "Sorento", 2021, 70.0, 7),
        
        # Motorbikes
        Motorbike("BIKE001", "Honda", "CBR600RR", 2020, 35.0, 600),
        Motorbike("BIKE002", "Yamaha", "YZF-R1", 2021, 45.0, 1000),
        Motorbike("BIKE003", "Kawasaki", "Ninja 400", 2019, 30.0, 400),
        Motorbike("BIKE004", "Ducati", "Monster 821", 2020, 55.0, 821),
        Motorbike("BIKE005", "Suzuki", "GSX-R750", 2021, 40.0, 750),
        
        # Trucks
        Truck("TRUCK001", "Ford", "F-150", 2020, 80.0, 2.5),
        Truck("TRUCK002", "Chevrolet", "Silverado", 2019, 85.0, 3.0),
        Truck("TRUCK003", "Ram", "1500", 2021, 90.0, 2.7),
        Truck("TRUCK004", "Toyota", "Tacoma", 2020, 75.0, 2.4),
        Truck("TRUCK005", "GMC", "Sierra", 2021, 95.0, 3.0),
    ]
    
    # Add vehicles to DAO
    for vehicle in vehicles:
        vehicle_dao.add(vehicle)
    
    
    # Initialize users
    print("👥 Creating user accounts...")
    
    # Staff user
    staff = Staff(
        renter_id=generate_user_id('staff'),
        name="Admin User",
        contact_info="admin@rental.com",
        username="admin",
        password="admin123"
    )
    user_dao.add(staff)
    
    # Corporate user
    corporate = CorporateUser(
        renter_id=generate_user_id('corporate'),
        name="Corporate Client",
        contact_info="corporate@company.com",
        username="corp001",
        password="password123"
    )
    user_dao.add(corporate)
    
    # Individual user
    individual = IndividualUser(
        renter_id=generate_user_id('individual'),
        name="John Doe",
        contact_info="john@email.com",
        username="john001",
        password="password123"
    )
    user_dao.add(individual)
    
    # Save all data
    print("Saving data to files...")
    vehicle_dao.save()
    user_dao.save()
    rental_dao.save()

if __name__ == "__main__":
    try:
        initialize_data()
    except Exception as e:
        print(f"Error during initialization: {str(e)}")
        sys.exit(1)
