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
    return {'now': datetime.now}

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
            session['user_id'] = user.renter_id
            session['username'] = user.username
            session['user_type'] = user.kind
            flash(f'Welcome, {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')


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
    vehicles = rental_service.filter_vehicles(
        vehicle_type=vehicle_type,
        make=make,
        min_price=min_price,
        max_price=max_price
    )
    
    # Get all makes for filter dropdown
    all_vehicles = vehicle_dao.get_all()
    all_makes = sorted(set(v.make for v in all_vehicles))
    
    user = user_dao.get_by_id(session['user_id'])
    
    return render_template('vehicles.html',
                         vehicles=vehicles,
                         all_makes=all_makes,
                         user=user,
                         current_type=vehicle_type,
                         current_make=make,
                         current_price_range=price_range)


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
    
    return render_template('vehicle_detail.html',
                         vehicle=vehicle,
                         user=user,
                         rental_history=rental_history)


@app.route('/rent/<vehicle_id>', methods=['GET', 'POST'])
@customer_required
def rent_vehicle(vehicle_id):
    """Rent a vehicle."""
    vehicle = vehicle_dao.get_by_id(vehicle_id)
    
    if not vehicle:
        flash('Vehicle not found.', 'danger')
        return redirect(url_for('vehicles'))
    
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        try:
            # Convert dates from YYYY-MM-DD to DD-MM-YYYY
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            start_date_formatted = start_dt.strftime('%d-%m-%Y')
            end_date_formatted = end_dt.strftime('%d-%m-%Y')
            
            period = RentalPeriod(start_date_formatted, end_date_formatted)
            
            total_cost = rental_service.rent_vehicle(
                vehicle_id,
                session['user_id'],
                period
            )
            
            flash(f'Vehicle rented successfully! Total cost: ${total_cost:.2f}', 'success')
            return redirect(url_for('rental_confirmation', vehicle_id=vehicle_id, 
                                  start_date=start_date_formatted, 
                                  end_date=end_date_formatted,
                                  total_cost=total_cost))
        
        except ValueError as e:
            flash(str(e), 'danger')
    
    user = user_dao.get_by_id(session['user_id'])
    
    return render_template('rent_vehicle.html', vehicle=vehicle, user=user)


@app.route('/rental-confirmation')
@customer_required
def rental_confirmation():
    """Rental confirmation/invoice page."""
    vehicle_id = request.args.get('vehicle_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    total_cost = request.args.get('total_cost')
    
    vehicle = vehicle_dao.get_by_id(vehicle_id)
    user = user_dao.get_by_id(session['user_id'])
    
    return render_template('rental_confirmation.html',
                         vehicle=vehicle,
                         user=user,
                         start_date=start_date,
                         end_date=end_date,
                         total_cost=total_cost)


@app.route('/return/<vehicle_id>', methods=['POST'])
@customer_required
def return_vehicle(vehicle_id):
    """Return a rented vehicle."""
    try:
        success = rental_service.return_vehicle(vehicle_id, session['user_id'])
        
        if success:
            flash('Vehicle returned successfully!', 'success')
        else:
            flash('No active rental found for this vehicle.', 'warning')
    
    except ValueError as e:
        flash(str(e), 'danger')
    
    return redirect(url_for('dashboard'))


@app.route('/my-rentals')
@customer_required
def my_rentals():
    """View rental history."""
    user = user_dao.get_by_id(session['user_id'])
    rental_history = list(user.rental_history)
    
    return render_template('my_rentals.html', user=user, rental_history=rental_history)


# Staff routes
@app.route('/staff/users')
@staff_required
def staff_users():
    """Staff: User management page."""
    users = user_dao.get_all()
    user = user_dao.get_by_id(session['user_id'])
    
    return render_template('staff_users.html', users=users, user=user)


@app.route('/staff/users/add', methods=['GET', 'POST'])
@staff_required
def staff_add_user():
    """Staff: Add user."""
    if request.method == 'POST':
        try:
            user_type = request.form.get('user_type')
            renter_id = request.form.get('renter_id')
            name = request.form.get('name')
            contact_info = request.form.get('contact_info')
            username = request.form.get('username')
            password = request.form.get('password')
            
            user_management_service.create_user(
                user_type, renter_id, name, contact_info, username, password
            )
            
            flash(f'User {name} added successfully!', 'success')
            return redirect(url_for('staff_users'))
        
        except ValueError as e:
            flash(str(e), 'danger')
    
    user = user_dao.get_by_id(session['user_id'])
    return render_template('staff_add_user.html', user=user)


@app.route('/staff/users/delete/<user_id>', methods=['POST'])
@staff_required
def staff_delete_user(user_id):
    """Staff: Delete user."""
    try:
        success = user_management_service.delete_user(user_id)
        
        if success:
            flash('User deleted successfully!', 'success')
        else:
            flash('User not found.', 'warning')
    
    except ValueError as e:
        flash(str(e), 'danger')
    
    return redirect(url_for('staff_users'))


@app.route('/staff/vehicles')
@staff_required
def staff_vehicles():
    """Staff: Vehicle management page."""
    vehicles = vehicle_dao.get_all()
    user = user_dao.get_by_id(session['user_id'])
    
    return render_template('staff_vehicles.html', vehicles=vehicles, user=user)


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
    
    return render_template('staff_rentals.html', 
                         rentals=enriched_rentals, 
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
    activities = analytics_service.get_user_activity_logs(50)
    user = user_dao.get_by_id(session['user_id'])
    
    return render_template('staff_activities.html',
                         activities=activities,
                         user=user)


if __name__ == '__main__':
    app.run(debug=True, port=5000)

