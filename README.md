# Vehicle Rental System

A comprehensive web-based vehicle rental management system built with Flask and Python, featuring role-based access control, rental management, and business analytics.

## Features

### Core Functionality

#### 1. User Roles
- **Corporate User**: 15% discount on all rentals
- **Individual User**: 10% discount for rentals exceeding 7 days
- **Staff**: Full administrative privileges

#### 2. Vehicle Rental Process
- Browse and filter vehicles by type, brand, and price range
- Check availability for selected rental periods
- Rent vehicles for specified durations
- Return vehicles through web interface
- View personal rental history
- Track current status (available, rented, overdue)

#### 3. Advanced Features
- **Overdue Tracking**: System automatically flags overdue rentals
- **Early Return**: Process early returns and update vehicle status immediately
- **Vehicle Filtering**: Filter by type (Car, Motorbike, Truck), brand, and price range
- **Vehicle Details**: Each vehicle has a detailed page with specifications and availability

#### 4. Staff Management Features
- User management (add/remove users)
- Vehicle management (add/remove vehicles)
- View all rental histories (by user or by vehicle)
- Access analytics dashboard
- View user activity logs

#### 5. Analytics Dashboard (Staff Only)
- Most/least rented vehicles
- Revenue summaries by vehicle type and user type
- User activity logs (rental and return events)
- Comprehensive business metrics

#### 6. Authentication & Security
- Secure login for all users
- Role-based access control
- Session management
- Password protection

#### 7. Billing & Invoices
- Automatic rental cost calculation
- Discount application based on user type and duration
- Printable invoices/receipts

#### 8. Data Persistence
- All data stored in pickle files
- Auto-save on changes
- Data loaded on application startup

## Project Structure

```
Assignment-3/
├── app.py                      # Main Flask application
├── run.py                      # Application entry point
├── requirements.txt            # Python dependencies
├── README.md                   # This file
│
├── models/                     # Data models and business logic
│   ├── dao/                    # Data Access Objects
│   │   ├── base_dao.py        # Base DAO with CRUD operations
│   │   ├── user_dao.py        # User data access
│   │   ├── vehicle_dao.py     # Vehicle data access
│   │   └── rental_dao.py      # Rental data access
│   │
│   ├── renter_model/          # User/Renter models
│   │   ├── renter.py          # Abstract base class
│   │   ├── corporate_user.py  # Corporate user
│   │   ├── individual_user.py # Individual user
│   │   └── staff.py           # Staff user
│   │
│   ├── vehicle_model/         # Vehicle models
│   │   ├── vehicle.py         # Abstract base class
│   │   ├── car.py            # Car implementation
│   │   ├── motorbike.py      # Motorbike implementation
│   │   └── truck.py          # Truck implementation
│   │
│   └── services/              # Business logic services
│       ├── rental_period.py   # Rental period management
│       ├── auth_service.py    # Authentication service
│       ├── rental_service.py  # Rental operations
│       ├── analytics_service.py # Business analytics
│       ├── user_management_service.py # User CRUD
│       └── vehicle_management_service.py # Vehicle CRUD
│
├── controllers/               # Controller layer (legacy)
│
├── templates/                 # HTML templates
│   ├── base.html             # Base template with navigation
│   ├── login.html            # Login page
│   ├── customer_dashboard.html
│   ├── staff_dashboard.html
│   ├── vehicles.html         # Vehicle listing
│   ├── vehicle_detail.html   # Vehicle details
│   ├── rent_vehicle.html     # Rental form
│   ├── rental_confirmation.html # Invoice
│   ├── my_rentals.html       # Rental history
│   ├── staff_users.html      # User management
│   ├── staff_add_user.html   # Add user form
│   ├── staff_vehicles.html   # Vehicle management
│   ├── staff_add_vehicle.html # Add vehicle form
│   ├── staff_rentals.html    # All rentals view
│   ├── staff_analytics.html  # Analytics dashboard
│   └── staff_activities.html # Activity logs
│
├── static/                    # Static files
│   ├── css/
│   │   └── style.css         # Custom styles
│   └── images/               # Vehicle images
│       ├── README.md         # Image guidelines
│       └── generate_placeholders.py # Image generator
│
├── tests/                     # Test suite
│   ├── conftest.py           # Pytest configuration
│   ├── test_rental_period.py # RentalPeriod tests
│   ├── test_users.py         # User model tests
│   ├── test_vehicles.py      # Vehicle model tests
│   ├── test_auth_service.py  # Auth service tests
│   └── test_integration.py   # Integration tests
│
├── common/                    # Common utilities
│   └── exceptions.py         # Custom exceptions
│
└── data/                      # Data storage (created on first run)
    ├── vehicles.pkl          # Vehicle data
    ├── users.pkl             # User data
    └── rentals.pkl           # Rental data
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Steps

1. **Clone or download the project**
   ```bash
   cd Assignment-3
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # On macOS/Linux:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize sample data (optional)**
   ```bash
   python init_data.py
   ```

5. **Generate placeholder images (optional)**
   ```bash
   cd static/images
   python generate_placeholders.py
   cd ../..
   ```

## Running the Application

### Start the server
```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Default Login Credentials

After running `init_data.py`, you can use these accounts:

- **Staff**: 
  - Username: `admin`
  - Password: `admin123`

- **Corporate User**: 
  - Username: `corp001`
  - Password: `password123`

- **Individual User**: 
  - Username: `ind001`
  - Password: `password123`

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_users.py
```

### Run with verbose output
```bash
pytest -v
```

### Run with coverage
```bash
pytest --cov=models --cov-report=html
```

## Usage Guide

### For Customers (Corporate & Individual Users)

1. **Login** with your credentials
2. **Browse Vehicles** from the navigation menu
3. **Filter vehicles** by type, brand, or price range
4. **View vehicle details** by clicking on any vehicle
5. **Rent a vehicle** by selecting dates and confirming
6. **View your rentals** from "My Rentals" or Dashboard
7. **Return vehicles** from your Dashboard or My Rentals page

### For Staff Users

1. **Login** with staff credentials
2. **Dashboard** shows system overview and analytics
3. **Manage Users**: Add/remove Corporate and Individual users
4. **Manage Vehicles**: Add/remove vehicles from the fleet
5. **View Rentals**: See all rental records across the system
6. **Analytics**: Access business metrics and reports
7. **Activities**: Monitor user rental and return activities

## Business Rules

### Pricing Structure

#### Cars
- Base rate: Per-day rate set for each vehicle
- 2 doors or less: +10% (sports car premium)
- 3-4 doors: Standard rate
- 5+ doors: +5% (large vehicle premium)

#### Motorbikes
- Base rate + $5/day helmet fee
- Engine ≥ 600cc: +5% premium

#### Trucks
- Base rate per day
- Load capacity > 3 tons: +10% surcharge
- Flat logistics fee: $20

### Discounts
- **Corporate Users**: 15% discount on all rentals
- **Individual Users**: 10% discount for rentals ≥ 7 days
- **Staff**: Cannot rent vehicles (administrative access only)

### Rental Rules
- Minimum rental: 1 day
- Overlapping rentals prevented automatically
- Vehicles must be returned to become available again
- Late returns flagged as overdue

## Technical Details

### Architecture
- **Pattern**: MVC (Model-View-Controller)
- **Backend**: Flask (Python web framework)
- **Frontend**: HTML, CSS, Bootstrap 5, Jinja2 templates
- **Data Persistence**: Pickle files
- **Testing**: pytest

### Key Technologies
- **Flask**: Web framework
- **Bootstrap 5**: Responsive UI framework
- **Bootstrap Icons**: Icon library
- **Jinja2**: Template engine
- **Pickle**: Data serialization

### Design Patterns Used
- **DAO Pattern**: Separation of data access logic
- **Service Layer Pattern**: Business logic encapsulation
- **Template Pattern**: Base classes with inheritance
- **Decorator Pattern**: Route protection and authentication

## Development

### Adding New Vehicle Types
1. Create a new class in `models/vehicle_model/` inheriting from `Vehicle`
2. Implement `calculate_rental()` method with pricing logic
3. Implement `__str__()` method
4. Add type-specific attributes
5. Update `VehicleManagementService` to handle the new type

### Adding New User Types
1. Create a new class in `models/renter_model/` inheriting from `Renter`
2. Implement `discount_factor()` method with discount logic
3. Implement `kind` property
4. Update `UserManagementService` to handle the new type

### Customizing Discounts
Edit the `discount_factor()` method in respective user classes:
- `models/renter_model/corporate_user.py`
- `models/renter_model/individual_user.py`

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, edit `app.py` and change:
```python
app.run(debug=True, port=5001)  # Use a different port
```

### Missing Dependencies
```bash
pip install -r requirements.txt --force-reinstall
```

### Data Corruption
Delete the `data/` directory and run `init_data.py` again to reset.

### Template Not Found
Ensure you're running the app from the project root directory.

## Testing Coverage

The test suite includes:
- **Unit Tests**: Individual component testing
  - RentalPeriod calculations
  - User discount logic
  - Vehicle pricing rules
  - Authentication service
  - Availability checking

- **Integration Tests**: End-to-end workflows
  - Complete rental workflow (login → rent → return)
  - Multiple concurrent rentals
  - Overlapping rental prevention
  - Discount application verification
  - Staff management operations
  - Data persistence verification

## Contributing

This is an academic project. For improvements or bug fixes:
1. Test your changes thoroughly
2. Run the full test suite
3. Update documentation as needed
4. Follow the existing code style

## License

This project is created for educational purposes as part of COMP642 - Object-Oriented Programming course.

## Support

For issues or questions, please refer to the course materials or contact the course instructor.

---

**Author**: Assignment 3 - COMP642  
**Version**: 1.0  
**Last Updated**: October 2025
