"""
Main Flask Application for Vehicle Rental System.
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from functools import wraps
from datetime import datetime
import os
import sys

# Add models to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'models'))

from models.dao.vehicle_dao import VehicleDAO
from models.dao.user_dao import UserDAO
from models.dao.rental_dao import RentalDAO
from models.services.auth_service import AuthService
from models.services.rental_service import RentalService
from models.services.analytics_service import AnalyticsService
from models.services.user_management_service import UserManagementService
from models.services.vehicle_management_service import VehicleManagementService
from models.services.rental_period import RentalPeriod

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

# Add datetime to Jinja2 context
from datetime import datetime
@app.context_processor
def inject_now():
    return {'now': datetime.now, 'min': min, 'max': max}

# Add custom Jinja2 filter for pagination
@app.template_filter('reject_page')
def reject_page(args_dict):
    """Remove 'page' parameter from request args."""
    result = dict(args_dict)
    result.pop('page', None)
    return result

# Pagination helper function
def paginate(items, page, per_page=10):
    """
    Paginate a list of items.
    Returns a dict with items for current page and pagination info.
    """
    total = len(items)
    total_pages = (total + per_page - 1) // per_page  # Ceiling division
    
    # Ensure page is within valid range
    page = max(1, min(page, total_pages if total_pages > 0 else 1))
    
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        'items': items[start:end],
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
        'prev_page': page - 1 if page > 1 else None,
        'next_page': page + 1 if page < total_pages else None
    }

# Data file paths
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

VEHICLE_DATA_FILE = os.path.join(DATA_DIR, 'vehicles.pkl')
USER_DATA_FILE = os.path.join(DATA_DIR, 'users.pkl')
RENTAL_DATA_FILE = os.path.join(DATA_DIR, 'rentals.pkl')

# Initialize DAOs
vehicle_dao = VehicleDAO(VEHICLE_DATA_FILE)
user_dao = UserDAO(USER_DATA_FILE)
rental_dao = RentalDAO(RENTAL_DATA_FILE)

# Load data on startup
vehicle_dao.load()
user_dao.load()
rental_dao.load()

# Initialize services
auth_service = AuthService(user_dao)
rental_service = RentalService(vehicle_dao, user_dao, rental_dao)
analytics_service = AnalyticsService(vehicle_dao, user_dao, rental_dao)
user_management_service = UserManagementService(user_dao)
vehicle_management_service = VehicleManagementService(vehicle_dao)


# Helper function to generate user ID based on type
def generate_user_id(user_type):
    """Generate a unique user ID based on user type."""
    # Determine prefix based on user type
    if user_type == 'Staff':
        prefix = 'STAFF'
    elif user_type == 'Corporate':
        prefix = 'CORP'
    else:  # Individual
        prefix = 'USER'
    
    # Find the highest existing number for this prefix
    all_users = user_dao.get_all()
    max_num = 0
    for user in all_users:
        if user.renter_id.startswith(prefix):
            try:
                num = int(user.renter_id[len(prefix):])
                max_num = max(max_num, num)
            except ValueError:
                continue
    
    # Generate new ID with next number
    new_num = max_num + 1
    return f"{prefix}{new_num:03d}"


# Decorators for authentication
def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def staff_required(f):
    """Decorator to require staff privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        user = user_dao.get_by_id(session['user_id'])
        if not user or not auth_service.is_staff(user):
            flash('Staff access required.', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def customer_required(f):
    """Decorator to require customer (non-staff) privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        user = user_dao.get_by_id(session['user_id'])
        if not user or not auth_service.can_rent(user):
            flash('Customer access required.', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


# Routes
@app.route('/')
def index():
    """Home page - redirect to login or dashboard."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = auth_service.authenticate(username, password)
        
        if user:
            # Check if user account is active
            if not user.active:
                flash('Your account has been deactivated. Please contact administrator.', 'danger')
                return render_template('login.html')
            
            session['user_id'] = user.renter_id
            session['username'] = user.username
            session['user_type'] = user.kind
            flash(f'Welcome, {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page."""
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            name = request.form.get('name')
            contact_info = request.form.get('contact_info')
            
            # Validation
            if not all([username, password, confirm_password, name, contact_info]):
                flash('All fields are required.', 'danger')
                return render_template('register.html')
            
            # Email validation
            import re
            email_pattern = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
            if not re.match(email_pattern, contact_info, re.IGNORECASE):
                flash('Please enter a valid email address.', 'danger')
                return render_template('register.html')
            
            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('register.html')
            
            # Password complexity validation
            if len(password) < 8:
                flash('Password must be at least 8 characters long.', 'danger')
                return render_template('register.html')
            
            if not re.search(r'[A-Z]', password):
                flash('Password must contain at least one uppercase letter.', 'danger')
                return render_template('register.html')
            
            if not re.search(r'[a-z]', password):
                flash('Password must contain at least one lowercase letter.', 'danger')
                return render_template('register.html')
            
            if not re.search(r'[0-9]', password):
                flash('Password must contain at least one number.', 'danger')
                return render_template('register.html')
            
            # Check if username already exists
            if user_dao.find_by_username(username):
                flash('Username already exists. Please choose another one.', 'danger')
                return render_template('register.html')
            
            # Generate unique user ID for Individual user
            renter_id = generate_user_id('Individual')
            
            # Create Individual user by default
            user = user_management_service.create_user(
                'Individual', renter_id, name, contact_info, username, password
            )
            
            flash(f'Registration successful! Welcome, {name}! You can now log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'danger')
    
    return render_template('register.html')


@app.route('/logout')
def logout():
    """Logout."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard - role-specific."""
    user = user_dao.get_by_id(session['user_id'])
    
    if auth_service.is_staff(user):
        # Staff dashboard with analytics
        summary = analytics_service.get_dashboard_summary()
        most_rented = analytics_service.get_most_rented_vehicles(5)
        recent_activities = analytics_service.get_user_activity_logs(10)
        overdue_rentals = rental_service.get_overdue_rentals()
        
        return render_template('staff_dashboard.html',
                             user=user,
                             summary=summary,
                             most_rented=most_rented,
                             recent_activities=recent_activities,
                             overdue_rentals=overdue_rentals)
    else:
        # Customer dashboard
        rental_history = list(user.rental_history)
        active_rentals = user.get_active_rentals()
        
        return render_template('customer_dashboard.html',
                             user=user,
                             rental_history=rental_history,
                             active_rentals=active_rentals)


@app.route('/vehicles')
@login_required
def vehicles():
    """Vehicle listing page."""
    # Get filter parameters
    vehicle_type = request.args.get('type')
    make = request.args.get('make')
    price_range = request.args.get('price_range')
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = request.args.get('page', 1, type=int)
    
    min_price = None
    max_price = None
    
    if price_range == 'low':
        max_price = 50
    elif price_range == 'medium':
        min_price = 51
        max_price = 100
    elif price_range == 'high':
        min_price = 101
    
    # Filter vehicles
    all_filtered_vehicles = rental_service.filter_vehicles(
        vehicle_type=vehicle_type,
        make=make,
        min_price=min_price,
        max_price=max_price
    )
    
    # Filter by status
    if status == 'available':
        all_filtered_vehicles = [v for v in all_filtered_vehicles if not v.get_active_rentals()]
    elif status == 'rented':
        all_filtered_vehicles = [v for v in all_filtered_vehicles if v.get_active_rentals()]
    
    # Filter by availability period
    if start_date and end_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
            end_dt = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
            
            # Convert to DD-MM-YYYY HH:MM format for RentalPeriod
            start_formatted = start_dt.strftime('%d-%m-%Y %H:%M')
            end_formatted = end_dt.strftime('%d-%m-%Y %H:%M')
            
            # Create a rental period to check availability
            from models.services.rental_period import RentalPeriod
            check_period = RentalPeriod(start_formatted, end_formatted)
            
            # Filter to only vehicles available during this period
            all_filtered_vehicles = [v for v in all_filtered_vehicles if v.is_available(check_period)]
        except (ValueError, Exception) as e:
            flash(f'Invalid date range: {str(e)}', 'warning')
    
    # Paginate results (9 cards per page for better grid layout: 3 columns x 3 rows)
    pagination = paginate(all_filtered_vehicles, page, per_page=9)
    
    # Get all makes for filter dropdown
    all_vehicles = vehicle_dao.get_all()
    all_makes = sorted(set(v.make for v in all_vehicles))
    
    user = user_dao.get_by_id(session['user_id'])
    
    return render_template('vehicles.html',
                         vehicles=pagination['items'],
                         pagination=pagination,
                         all_makes=all_makes,
                         user=user,
                         current_type=vehicle_type,
                         current_make=make,
                         current_price_range=price_range,
                         current_status=status,
                         current_start_date=start_date,
                         current_end_date=end_date)


@app.route('/vehicles/<vehicle_id>')
@login_required
def vehicle_detail(vehicle_id):
    """Vehicle detail page."""
    vehicle = vehicle_dao.get_by_id(vehicle_id)
    
    if not vehicle:
        flash('Vehicle not found.', 'danger')
        return redirect(url_for('vehicles'))
    
    user = user_dao.get_by_id(session['user_id'])
    rental_history = vehicle.rental_history
    
    # Get booked date ranges for availability calendar
    active_rentals = vehicle.get_active_rentals()
    booked_ranges = []
    for rental in active_rentals:
        # Parse datetime strings (DD-MM-YYYY HH:MM)
        start_parts = rental.period.start_date.split(' ')[0].split('-')
        end_parts = rental.period.end_date.split(' ')[0].split('-')
        
        # Convert to YYYY-MM-DD for JavaScript
        start_date_str = f"{start_parts[2]}-{start_parts[1]}-{start_parts[0]}"
        end_date_str = f"{end_parts[2]}-{end_parts[1]}-{end_parts[0]}"
        
        booked_ranges.append({
            'start': start_date_str,
            'end': end_date_str
        })
    
    import json
    booked_ranges_json = json.dumps(booked_ranges)
    
    return render_template('vehicle_detail.html',
                         vehicle=vehicle,
                         user=user,
                         rental_history=rental_history,
                         booked_ranges=booked_ranges_json)


@app.route('/rent/<vehicle_id>', methods=['GET', 'POST'])
@customer_required
def rent_vehicle(vehicle_id):
    """Rent a vehicle."""
    vehicle = vehicle_dao.get_by_id(vehicle_id)
    
    if not vehicle:
        flash('Vehicle not found.', 'danger')
        return redirect(url_for('vehicles'))
    
    # Get booked date ranges for this vehicle
    booked_ranges = []
    for rental in vehicle.rental_history:
        if not rental.returned:  # Only consider active rentals
            booked_ranges.append({
                'start': rental.period.start_date,
                'end': rental.period.end_date
            })
    
    if request.method == 'POST':
        start_datetime = request.form.get('start_datetime')
        end_datetime = request.form.get('end_datetime')
        
        try:
            # Convert datetime from YYYY-MM-DDTHH:MM to DD-MM-YYYY HH:MM
            start_dt = datetime.strptime(start_datetime, '%Y-%m-%dT%H:%M')
            end_dt = datetime.strptime(end_datetime, '%Y-%m-%dT%H:%M')
            start_datetime_formatted = start_dt.strftime('%d-%m-%Y %H:%M')
            end_datetime_formatted = end_dt.strftime('%d-%m-%Y %H:%M')
            
            period = RentalPeriod(start_datetime_formatted, end_datetime_formatted)
            
            # Calculate rental details for invoice
            user = user_dao.get_by_id(session['user_id'])
            days = period.calculate_duration()
            discount_factor = user.discount_factor(days)
            original_cost = vehicle.daily_rate * days
            discount_rate = (1 - discount_factor) * 100  # Convert to percentage
            
            total_cost = rental_service.rent_vehicle(
                vehicle_id,
                session['user_id'],
                period
            )
            
            flash(f'Vehicle rented successfully! Total cost: ${total_cost:.2f}', 'success')
            return redirect(url_for('rental_confirmation', vehicle_id=vehicle_id, 
                                  start_date=start_datetime_formatted, 
                                  end_date=end_datetime_formatted,
                                  total_cost=f'{total_cost:.2f}',
                                  original_cost=f'{original_cost:.2f}',
                                  discount_rate=f'{discount_rate:.2f}',
                                  days=days))
        
        except ValueError as e:
            flash(str(e), 'danger')
    
    user = user_dao.get_by_id(session['user_id'])
    
    # Convert booked ranges to JavaScript-friendly format (YYYY-MM-DD)
    import json
    booked_ranges_js = []
    for rental_range in booked_ranges:
        # Convert DD-MM-YYYY to YYYY-MM-DD
        start_parts = rental_range['start'].split('-')
        end_parts = rental_range['end'].split('-')
        booked_ranges_js.append({
            'start': f'{start_parts[2]}-{start_parts[1]}-{start_parts[0]}',
            'end': f'{end_parts[2]}-{end_parts[1]}-{end_parts[0]}'
        })
    
    return render_template('rent_vehicle.html', 
                         vehicle=vehicle, 
                         user=user,
                         booked_ranges=json.dumps(booked_ranges_js))


@app.route('/rental-confirmation')
@customer_required
def rental_confirmation():
    """Rental confirmation/invoice page."""
    vehicle_id = request.args.get('vehicle_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    total_cost = request.args.get('total_cost')
    original_cost = request.args.get('original_cost')
    discount_rate = request.args.get('discount_rate')
    days = request.args.get('days')
    
    vehicle = vehicle_dao.get_by_id(vehicle_id)
    user = user_dao.get_by_id(session['user_id'])
    
    return render_template('rental_confirmation.html',
                         vehicle=vehicle,
                         user=user,
                         start_date=start_date,
                         end_date=end_date,
                         total_cost=total_cost,
                         original_cost=original_cost,
                         discount_rate=discount_rate,
                         days=days)


@app.route('/return/<vehicle_id>', methods=['GET', 'POST'])
@customer_required
def return_vehicle(vehicle_id):
    """Return a rented vehicle."""
    vehicle = vehicle_dao.get_by_id(vehicle_id)
    user = user_dao.get_by_id(session['user_id'])
    
    if not vehicle:
        flash('Vehicle not found.', 'danger')
        return redirect(url_for('my_rentals'))
    
    # Find active rental for this vehicle and user
    active_rental = None
    for rental in user.rental_history:
        if rental.vehicle_id == vehicle_id and not rental.returned:
            active_rental = rental
            break
    
    if not active_rental:
        flash('No active rental found for this vehicle.', 'warning')
        return redirect(url_for('my_rentals'))
    
    if request.method == 'POST':
        return_datetime = request.form.get('return_datetime')
        
        try:
            # Convert datetime from YYYY-MM-DDTHH:MM to DD-MM-YYYY HH:MM
            return_dt = datetime.strptime(return_datetime, '%Y-%m-%dT%H:%M')
            return_datetime_formatted = return_dt.strftime('%d-%m-%Y %H:%M')
            
            # Validate return datetime
            start_dt = datetime.strptime(active_rental.period.start_date, '%d-%m-%Y %H:%M')
            if return_dt < start_dt:
                flash('Return date & time cannot be before the rental start!', 'danger')
                return render_template('return_vehicle.html', vehicle=vehicle, user=user, rental=active_rental)
            
            # Return the vehicle
            success = rental_service.return_vehicle(vehicle_id, session['user_id'])
            
            if success:
                flash('Vehicle returned successfully!', 'success')
                return redirect(url_for('my_rentals'))
            else:
                flash('Failed to return vehicle. Please try again.', 'danger')
        
        except ValueError as e:
            flash(str(e), 'danger')
    
    return render_template('return_vehicle.html', vehicle=vehicle, user=user, rental=active_rental)


@app.route('/my-rentals')
@customer_required
def my_rentals():
    """View rental history."""
    page = request.args.get('page', 1, type=int)
    user = user_dao.get_by_id(session['user_id'])
    rental_history = list(user.rental_history)
    
    # Paginate results
    pagination = paginate(rental_history, page, per_page=10)
    
    return render_template('my_rentals.html', 
                         user=user, 
                         rental_history=pagination['items'],
                         pagination=pagination)


# Staff routes
@app.route('/staff/users')
@staff_required
def staff_users():
    """Staff: User management page."""
    page = request.args.get('page', 1, type=int)
    all_users = user_dao.get_all()
    user = user_dao.get_by_id(session['user_id'])
    
    # Paginate results
    pagination = paginate(all_users, page, per_page=10)
    
    return render_template('staff_users.html', 
                         users=pagination['items'], 
                         pagination=pagination,
                         user=user)


@app.route('/staff/users/add', methods=['GET', 'POST'])
@staff_required
def staff_add_user():
    """Staff: Add user."""
    if request.method == 'POST':
        try:
            user_type = request.form.get('user_type')
            name = request.form.get('name')
            contact_info = request.form.get('contact_info')
            username = request.form.get('username')
            password = request.form.get('password')
            
            # Auto-generate ID based on user type
            renter_id = generate_user_id(user_type)
            
            user_management_service.create_user(
                user_type, renter_id, name, contact_info, username, password
            )
            
            flash(f'User {name} added successfully with ID: {renter_id}', 'success')
            return redirect(url_for('staff_users'))
        
        except ValueError as e:
            flash(str(e), 'danger')
    
    user = user_dao.get_by_id(session['user_id'])
    return render_template('staff_add_user.html', user=user)


@app.route('/staff/users/edit/<user_id>', methods=['GET', 'POST'])
@staff_required
def staff_edit_user(user_id):
    """Staff: Edit user."""
    user_to_edit = user_dao.get_by_id(user_id)
    
    if not user_to_edit:
        flash('User not found.', 'danger')
        return redirect(url_for('staff_users'))
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            contact_info = request.form.get('contact_info')
            new_user_type = request.form.get('user_type')
            
            # Update basic info
            if name:
                user_to_edit.name = name
            if contact_info:
                user_to_edit.contact_info = contact_info
            
            # If user type changed, we need to create a new instance
            if new_user_type and new_user_type != user_to_edit.kind:
                from models.renter_model.corporate_user import CorporateUser
                from models.renter_model.individual_user import IndividualUser
                from models.renter_model.staff import Staff
                
                # Store current data
                old_id = user_to_edit.renter_id
                old_username = user_to_edit.username
                old_password = user_to_edit.password
                old_history = list(user_to_edit.rental_history)
                
                # Delete old user
                user_dao.delete(old_id)
                
                # Create new user with new type
                if new_user_type == 'Individual':
                    new_user = IndividualUser(old_id, name, contact_info, old_username, old_password)
                elif new_user_type == 'Corporate':
                    new_user = CorporateUser(old_id, name, contact_info, old_username, old_password)
                elif new_user_type == 'Staff':
                    new_user = Staff(old_id, name, contact_info, old_username, old_password)
                else:
                    raise ValueError(f"Invalid user type: {new_user_type}")
                
                # Restore rental history
                for record in old_history:
                    new_user.add_rental_record(record)
                
                # Add new user
                user_dao.add(new_user)
                
                flash(f'User role changed to {new_user_type} successfully!', 'success')
            else:
                # Just update the existing user
                user_dao.update(user_to_edit)
                flash('User updated successfully!', 'success')
            
            user_dao.save()
            return redirect(url_for('staff_users'))
            
        except ValueError as e:
            flash(str(e), 'danger')
    
    user = user_dao.get_by_id(session['user_id'])
    return render_template('staff_edit_user.html', user=user, user_to_edit=user_to_edit)


@app.route('/staff/users/delete/<user_id>', methods=['POST'])
@staff_required
def staff_delete_user(user_id):
    """Staff: Deactivate user (soft delete)."""
    try:
        # Prevent deactivating yourself
        if user_id == session['user_id']:
            flash('You cannot deactivate your own account!', 'danger')
            return redirect(url_for('staff_users'))
        
        # Get the user
        user = user_dao.get_by_id(user_id)
        if user:
            # Mark user as inactive
            user.active = False
            user_dao.update(user)
            user_dao.save()
            flash(f'User {user.name} has been deactivated successfully!', 'success')
        else:
            flash('User not found.', 'warning')
    
    except Exception as e:
        flash(str(e), 'danger')
    
    return redirect(url_for('staff_users'))


@app.route('/staff/users/activate/<user_id>', methods=['POST'])
@staff_required
def staff_activate_user(user_id):
    """Staff: Activate user (reactivate deactivated account)."""
    try:
        # Get the user
        user = user_dao.get_by_id(user_id)
        if user:
            # Mark user as active
            user.active = True
            user_dao.update(user)
            user_dao.save()
            flash(f'User {user.name} has been activated successfully!', 'success')
        else:
            flash('User not found.', 'warning')
    
    except Exception as e:
        flash(str(e), 'danger')
    
    return redirect(url_for('staff_users'))


@app.route('/staff/vehicles')
@staff_required
def staff_vehicles():
    """Staff: Vehicle management page."""
    page = request.args.get('page', 1, type=int)
    all_vehicles = vehicle_dao.get_all()
    user = user_dao.get_by_id(session['user_id'])
    
    # Paginate results
    pagination = paginate(all_vehicles, page, per_page=10)
    
    return render_template('staff_vehicles.html', 
                         vehicles=pagination['items'],
                         pagination=pagination,
                         user=user)


@app.route('/staff/vehicles/add', methods=['GET', 'POST'])
@staff_required
def staff_add_vehicle():
    """Staff: Add vehicle."""
    if request.method == 'POST':
        try:
            vehicle_type = request.form.get('vehicle_type')
            vehicle_id = request.form.get('vehicle_id')
            make = request.form.get('make')
            model = request.form.get('model')
            year = int(request.form.get('year'))
            daily_rate = float(request.form.get('daily_rate'))
            
            kwargs = {}
            if vehicle_type == 'Car':
                kwargs['num_doors'] = int(request.form.get('num_doors', 4))
            elif vehicle_type == 'Motorbike':
                kwargs['engine_cc'] = int(request.form.get('engine_cc', 150))
            elif vehicle_type == 'Truck':
                kwargs['load_capacity_tons'] = float(request.form.get('load_capacity_tons', 2.0))
            
            vehicle_management_service.create_vehicle(
                vehicle_type, vehicle_id, make, model, year, daily_rate, **kwargs
            )
            
            flash(f'Vehicle {make} {model} added successfully!', 'success')
            return redirect(url_for('staff_vehicles'))
        
        except ValueError as e:
            flash(str(e), 'danger')
    
    user = user_dao.get_by_id(session['user_id'])
    return render_template('staff_add_vehicle.html', user=user)


@app.route('/staff/vehicles/delete/<vehicle_id>', methods=['POST'])
@staff_required
def staff_delete_vehicle(vehicle_id):
    """Staff: Delete vehicle."""
    try:
        success = vehicle_management_service.delete_vehicle(vehicle_id)
        
        if success:
            flash('Vehicle deleted successfully!', 'success')
        else:
            flash('Vehicle not found.', 'warning')
    
    except ValueError as e:
        flash(str(e), 'danger')
    
    return redirect(url_for('staff_vehicles'))


@app.route('/staff/rentals')
@staff_required
def staff_rentals():
    """Staff: View all rentals."""
    page = request.args.get('page', 1, type=int)
    all_rentals = rental_service.get_all_rental_records()
    user = user_dao.get_by_id(session['user_id'])
    
    # Enrich rental records with user and vehicle info
    enriched_rentals = []
    for record in all_rentals:
        renter = user_dao.get_by_id(record.renter_id)
        vehicle = vehicle_dao.get_by_id(record.vehicle_id)
        enriched_rentals.append({
            'record': record,
            'renter': renter,
            'vehicle': vehicle
        })
    
    # Paginate results
    pagination = paginate(enriched_rentals, page, per_page=10)
    
    return render_template('staff_rentals.html', 
                         rentals=pagination['items'],
                         pagination=pagination,
                         user=user)


@app.route('/staff/analytics')
@staff_required
def staff_analytics():
    """Staff: Analytics dashboard."""
    summary = analytics_service.get_dashboard_summary()
    most_rented = analytics_service.get_most_rented_vehicles(10)
    least_rented = analytics_service.get_least_rented_vehicles(10)
    user = user_dao.get_by_id(session['user_id'])
    
    return render_template('staff_analytics.html',
                         summary=summary,
                         most_rented=most_rented,
                         least_rented=least_rented,
                         user=user)


@app.route('/staff/activities')
@staff_required
def staff_activities():
    """Staff: User activity logs."""
    page = request.args.get('page', 1, type=int)
    all_activities = analytics_service.get_user_activity_logs(1000)  # Get more records for pagination
    user = user_dao.get_by_id(session['user_id'])
    
    # Paginate results
    pagination = paginate(all_activities, page, per_page=10)
    
    return render_template('staff_activities.html',
                         activities=pagination['items'],
                         pagination=pagination,
                         user=user)


if __name__ == '__main__':
    app.run(debug=True, port=5000)

