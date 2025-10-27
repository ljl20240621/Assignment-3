from flask import Flask
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

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

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


# Store services and DAOs in app config for access in blueprints
app.config['VEHICLE_DAO'] = vehicle_dao
app.config['USER_DAO'] = user_dao
app.config['RENTAL_DAO'] = rental_dao
app.config['AUTH_SERVICE'] = auth_service
app.config['RENTAL_SERVICE'] = rental_service
app.config['ANALYTICS_SERVICE'] = analytics_service
app.config['USER_MANAGEMENT_SERVICE'] = user_management_service
app.config['VEHICLE_MANAGEMENT_SERVICE'] = vehicle_management_service
app.config['generate_user_id'] = generate_user_id


# Add datetime to Jinja2 context
@app.context_processor
def inject_now():
    """Inject datetime and utility functions into Jinja2 context."""
    return {'now': datetime.now, 'min': min, 'max': max}


# Add custom Jinja2 filter for pagination
@app.template_filter('reject_page')
def reject_page(args_dict):
    """Remove 'page' parameter from request args."""
    result = dict(args_dict)
    result.pop('page', None)
    return result


# Register Blueprints
from controllers.auth_controller import auth_bp
from controllers.customer_controller import customer_bp
from controllers.staff_controller import staff_bp

app.register_blueprint(auth_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(staff_bp)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
