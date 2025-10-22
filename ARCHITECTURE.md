# Vehicle Rental System - Architecture Documentation

## 📐 Architecture Overview

This application implements a **Model-View-Controller (MVC)** pattern with **Flask Blueprints** for modular controller organization.

## 🏗️ Layer Structure

### 1. Model Layer (`models/`)

Handles business logic, data access, and domain entities.

#### Entities (`models/renter_model/`, `models/vehicle_model/`)
- **Purpose**: Represent core domain objects
- **Key Classes**:
  - `Renter` (abstract base), `IndividualUser`, `CorporateUser`, `Staff`
  - `Vehicle` (abstract base), `Car`, `Motorbike`, `Truck`
  - `RentalRecord`, `RentalPeriod`
- **Principles**: Inheritance, encapsulation, polymorphism

#### Data Access Objects (`models/dao/`)
- **Purpose**: Abstract data persistence operations
- **Pattern**: Generic CRUD operations using pickle
- **Classes**:
  - `BaseDAO`: Generic persistence methods
  - `VehicleDAO`, `UserDAO`, `RentalDAO`: Specialized DAOs

#### Services (`models/services/`)
- **Purpose**: Encapsulate business logic
- **Classes**:
  - `AuthService`: Authentication and authorization
  - `RentalService`: Rental/return operations
  - `AnalyticsService`: Reporting and statistics
  - `UserManagementService`: User CRUD operations
  - `VehicleManagementService`: Vehicle CRUD operations

### 2. View Layer (`templates/`)

HTML templates rendered with Jinja2.

#### Template Organization
- **Base**: `base.html` (shared layout)
- **Auth**: `login.html`, `register.html`
- **Customer**: `vehicles.html`, `vehicle_detail.html`, `rent_vehicle.html`, `return_vehicle.html`, `my_rentals.html`, `rental_confirmation.html`, `customer_dashboard.html`
- **Staff**: `staff_*.html` (users, vehicles, rentals, analytics, activities management)
- **Components**: `pagination.html` (reusable pagination)

### 3. Controller Layer (`controllers/`)

Flask Blueprints for modular route handling.

#### Auth Controller (`controllers/auth_controller.py`)
- **Prefix**: `/` (root)
- **Routes**: 5
  - `GET /` → Redirect to login or dashboard
  - `GET/POST /login` → User authentication
  - `GET/POST /register` → User registration
  - `GET /logout` → User logout
  - `GET /dashboard` → Role-specific dashboard

#### Customer Controller (`controllers/customer_controller.py`)
- **Prefix**: `/` (root)
- **Routes**: 7
  - `GET /vehicles` → Browse vehicles (with filters, search, pagination)
  - `GET /vehicles/<id>` → Vehicle details with availability calendar
  - `GET/POST /rent/<id>` → Rent a vehicle
  - `GET /rental-confirmation` → Rental invoice/confirmation
  - `GET/POST /return/<id>` → Return a vehicle
  - `GET /my-rentals` → View rental history (with search, pagination)
  - `GET /invoice` → View specific rental invoice

#### Staff Controller (`controllers/staff_controller.py`)
- **Prefix**: `/staff`
- **Routes**: 11
  - `GET /users` → List all users (paginated)
  - `GET/POST /users/add` → Add new user
  - `GET/POST /users/edit/<id>` → Edit user details/role
  - `POST /users/delete/<id>` → Deactivate user (soft delete)
  - `POST /users/activate/<id>` → Reactivate user
  - `GET /vehicles` → List all vehicles (paginated)
  - `GET/POST /vehicles/add` → Add new vehicle
  - `POST /vehicles/delete/<id>` → Delete vehicle
  - `GET /rentals` → View all rental records (paginated)
  - `GET /analytics` → Analytics dashboard
  - `GET /activities` → User activity logs (paginated)

### 4. Application Entry (`app.py`, `run.py`)

#### app.py
- Initializes Flask app
- Sets up DAOs and services
- Registers Blueprints
- Configures Jinja2 context processors
- Stores services in `app.config` for Blueprint access

#### run.py
- Entry point for running the application
- Provides user-friendly startup message

## 🔒 Security Features

### Authentication
- Session-based authentication
- Password validation (min 8 chars, uppercase, lowercase, digit)
- Username uniqueness check

### Authorization Decorators
- `@login_required`: Requires authenticated user
- `@staff_required`: Requires staff role
- `@customer_required`: Requires customer role (Individual/Corporate)

### Soft Delete
- Users are deactivated, not permanently deleted
- Preserves data integrity and history

## 💾 Data Persistence

### Pickle Storage
- **Location**: `data/` directory
- **Files**:
  - `users.pkl`: All user accounts
  - `vehicles.pkl`: Vehicle inventory
  - `rentals.pkl`: Rental records

### Data Flow
1. **Load**: DAOs load data from pickle files on app startup
2. **Update**: Changes are immediately saved to pickle files
3. **Consistency**: All operations update in-memory objects and persist to disk

## 🎯 Design Patterns

### 1. MVC (Model-View-Controller)
- Clear separation of concerns
- Models handle data and logic
- Views handle presentation
- Controllers handle request routing

### 2. DAO (Data Access Object)
- Abstracts data persistence
- Generic CRUD operations
- Swappable storage backend (currently pickle)

### 3. Service Layer
- Encapsulates business logic
- Orchestrates between DAOs and controllers
- Promotes code reuse

### 4. Blueprint (Flask-specific)
- Modular controller organization
- Clear route grouping by functionality
- Independent development and testing

### 5. Decorator Pattern
- Authentication/authorization decorators
- Jinja2 template filters
- Reusable cross-cutting concerns

## 📊 Key Features Implementation

### 1. Role-Based Access
- **Implementation**: Decorators check user role from session
- **Roles**: Staff, Corporate, Individual
- **Permissions**: Each role has specific allowed operations

### 2. Discount Calculation
- **Corporate**: 15% on all rentals (in `CorporateUser` class)
- **Individual**: 10% for rentals > 7 days (in `IndividualUser` class)
- **Pattern**: Polymorphic `discount_factor()` method

### 3. Pagination
- **Helper**: Generic `paginate()` function in controllers
- **Template**: Reusable `pagination.html` component
- **Per Page**: 9 for vehicle cards, 10 for lists

### 4. Search & Filtering
- **Vehicles**: By type, make, price range, status, availability period, search term
- **Rentals**: By vehicle ID, make, model

### 5. Availability Calendar
- **Vehicle Detail**: Shows booked dates for next 3 months
- **Rental Form**: Disables booked dates in date picker
- **Implementation**: JavaScript with backend-provided booked ranges

### 6. Invoice Generation
- **Dynamic Calculation**: Original cost, discount rate, final amount
- **Format**: All monetary values to 2 decimal places
- **Reusable**: Same template for confirmation and invoice viewing

## 🔄 Request Flow Example

### User Rents a Vehicle

1. **User clicks "Rent" on vehicle card**
   - Route: `GET /vehicles/CAR001`
   - Controller: `customer_controller.vehicle_detail()`
   - Renders: `vehicle_detail.html`

2. **User selects dates and submits**
   - Route: `POST /rent/CAR001`
   - Controller: `customer_controller.rent_vehicle()`
   - Service: `rental_service.rent_vehicle()`
   - DAO: `rental_dao.add()`, `vehicle_dao.update()`, `user_dao.update()`
   - Redirect: `/rental-confirmation?...`

3. **User views confirmation**
   - Route: `GET /rental-confirmation`
   - Controller: `customer_controller.rental_confirmation()`
   - Renders: `rental_confirmation.html`

## 🧪 Testing Strategy

### Unit Tests (`tests/`)
- Test individual components in isolation
- Mock external dependencies
- Focus on business logic (discounts, availability, etc.)

### Integration Tests
- Test complete workflows end-to-end
- Use temporary pickle files
- Verify data persistence

### Test Coverage Areas
- Authentication and authorization
- Rental period validation
- Discount calculations
- Vehicle availability checking
- Data persistence
- Staff management operations

## 🚀 Benefits of This Architecture

1. **Maintainability**: Clear separation of concerns, easy to locate and modify code
2. **Scalability**: Can easily add new Blueprints or services
3. **Testability**: Isolated components can be tested independently
4. **Reusability**: Services and DAOs can be reused across controllers
5. **Readability**: Each file has a single, clear responsibility
6. **Team Collaboration**: Different developers can work on different Blueprints

## 📝 Code Quality Practices

1. **Docstrings**: All classes and functions documented
2. **Type Hints**: Used where appropriate for clarity
3. **Error Handling**: Try-except blocks with user-friendly messages
4. **Validation**: Input validation at both client and server side
5. **DRY Principle**: Pagination, decorators, and services promote code reuse
6. **Consistent Naming**: Clear, descriptive variable and function names

---

**Last Updated**: October 2025  
**Version**: 2.0 (Blueprint Refactored)

