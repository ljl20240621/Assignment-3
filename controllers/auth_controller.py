"""
Authentication Controller - Handles user authentication and authorization.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from controllers import login_required
import re

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    """Home page - redirect to login or dashboard."""
    if 'user_id' in session:
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        auth_service = current_app.config['AUTH_SERVICE']
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
            return redirect(url_for('auth.dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
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
            user_dao = current_app.config['USER_DAO']
            if user_dao.find_by_username(username):
                flash('Username already exists. Please choose another one.', 'danger')
                return render_template('register.html')
            
            # Generate unique user ID for Individual user
            renter_id = current_app.config['generate_user_id']('Individual')
            
            # Create Individual user by default
            user_management_service = current_app.config['USER_MANAGEMENT_SERVICE']
            user = user_management_service.create_user(
                'Individual', renter_id, name, contact_info, username, password
            )
            
            flash(f'Registration successful! Welcome, {name}! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'danger')
    
    return render_template('register.html')


@auth_bp.route('/logout')
def logout():
    """Logout."""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard - role-specific."""
    user_dao = current_app.config['USER_DAO']
    auth_service = current_app.config['AUTH_SERVICE']
    analytics_service = current_app.config['ANALYTICS_SERVICE']
    rental_service = current_app.config['RENTAL_SERVICE']
    
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
        all_active_rentals = user.get_active_rentals()
        
        # Add vehicle information to each rental
        vehicle_dao = current_app.config['VEHICLE_DAO']
        for rental in all_active_rentals:
            rental.vehicle = vehicle_dao.get_by_id(rental.vehicle_id)
        
        # Limit active rentals to first 10 for dashboard
        active_rentals_display = all_active_rentals[:10]
        total_active = len(all_active_rentals)
        has_more_active = total_active > 10
        
        return render_template('customer_dashboard.html',
                             user=user,
                             rental_history=rental_history,
                             active_rentals=active_rentals_display,
                             total_active=total_active,
                             has_more_active=has_more_active)

