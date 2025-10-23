"""
Staff Controller - Handles administrative operations for staff users.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from controllers import staff_required

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')


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


@staff_bp.route('/users')
@staff_required
def users():
    """Staff: User management page."""
    user_dao = current_app.config['USER_DAO']
    
    page = request.args.get('page', 1, type=int)
    all_users = user_dao.get_all()
    user = user_dao.get_by_id(session['user_id'])
    
    # Check if user exists
    if not user:
        flash('User not found. Please log in again.', 'danger')
        session.clear()
        return redirect(url_for('auth.login'))
    
    # Paginate results
    pagination = paginate(all_users, page, per_page=10)
    
    return render_template('staff_users.html', 
                         users=pagination['items'], 
                         pagination=pagination,
                         user=user)


@staff_bp.route('/users/add', methods=['GET', 'POST'])
@staff_required
def add_user():
    """Staff: Add user."""
    if request.method == 'POST':
        try:
            user_management_service = current_app.config['USER_MANAGEMENT_SERVICE']
            user_dao = current_app.config['USER_DAO']
            
            user_type = request.form.get('user_type')
            name = request.form.get('name')
            contact_info = request.form.get('contact_info')
            username = request.form.get('username')
            password = request.form.get('password')
            
            # Auto-generate ID based on user type
            renter_id = current_app.config['generate_user_id'](user_type)
            
            user_management_service.create_user(
                user_type, renter_id, name, contact_info, username, password
            )
            
            flash(f'User {name} added successfully with ID: {renter_id}', 'success')
            return redirect(url_for('staff.users'))
        
        except ValueError as e:
            flash(str(e), 'danger')
    
    user_dao = current_app.config['USER_DAO']
    user = user_dao.get_by_id(session['user_id'])
    return render_template('staff_add_user.html', user=user)


@staff_bp.route('/users/edit/<user_id>', methods=['GET', 'POST'])
@staff_required
def edit_user(user_id):
    """Staff: Edit user."""
    user_dao = current_app.config['USER_DAO']
    user_to_edit = user_dao.get_by_id(user_id)
    
    if not user_to_edit:
        flash('User not found.', 'danger')
        return redirect(url_for('staff.users'))
    
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
            return redirect(url_for('staff.users'))
            
        except ValueError as e:
            flash(str(e), 'danger')
    
    user = user_dao.get_by_id(session['user_id'])
    return render_template('staff_edit_user.html', user=user, user_to_edit=user_to_edit)


@staff_bp.route('/users/delete/<user_id>', methods=['POST'])
@staff_required
def delete_user(user_id):
    """Staff: Deactivate user (soft delete)."""
    try:
        user_dao = current_app.config['USER_DAO']
        
        # Prevent deactivating yourself
        if user_id == session['user_id']:
            flash('You cannot deactivate your own account!', 'danger')
            return redirect(url_for('staff.users'))
        
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
    
    return redirect(url_for('staff.users'))


@staff_bp.route('/users/activate/<user_id>', methods=['POST'])
@staff_required
def activate_user(user_id):
    """Staff: Activate user (reactivate deactivated account)."""
    try:
        user_dao = current_app.config['USER_DAO']
        
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
    
    return redirect(url_for('staff.users'))


@staff_bp.route('/vehicles')
@staff_required
def vehicles():
    """Staff: Vehicle management page."""
    vehicle_dao = current_app.config['VEHICLE_DAO']
    user_dao = current_app.config['USER_DAO']
    
    page = request.args.get('page', 1, type=int)
    all_vehicles = vehicle_dao.get_all()
    user = user_dao.get_by_id(session['user_id'])
    
    # Paginate results
    pagination = paginate(all_vehicles, page, per_page=10)
    
    return render_template('staff_vehicles.html', 
                         vehicles=pagination['items'],
                         pagination=pagination,
                         user=user)


@staff_bp.route('/vehicles/add', methods=['GET', 'POST'])
@staff_required
def add_vehicle():
    """Staff: Add vehicle."""
    if request.method == 'POST':
        try:
            vehicle_management_service = current_app.config['VEHICLE_MANAGEMENT_SERVICE']
            user_dao = current_app.config['USER_DAO']
            
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
            return redirect(url_for('staff.vehicles'))
        
        except ValueError as e:
            flash(str(e), 'danger')
    
    user_dao = current_app.config['USER_DAO']
    user = user_dao.get_by_id(session['user_id'])
    return render_template('staff_add_vehicle.html', user=user)


@staff_bp.route('/vehicles/delete/<vehicle_id>', methods=['POST'])
@staff_required
def delete_vehicle(vehicle_id):
    """Staff: Delete vehicle."""
    try:
        vehicle_management_service = current_app.config['VEHICLE_MANAGEMENT_SERVICE']
        success = vehicle_management_service.delete_vehicle(vehicle_id)
        
        if success:
            flash('Vehicle deleted successfully!', 'success')
        else:
            flash('Vehicle not found.', 'warning')
    
    except ValueError as e:
        flash(str(e), 'danger')
    
    return redirect(url_for('staff.vehicles'))


@staff_bp.route('/rentals')
@staff_required
def rentals():
    """Staff: View all rentals."""
    vehicle_dao = current_app.config['VEHICLE_DAO']
    user_dao = current_app.config['USER_DAO']
    rental_service = current_app.config['RENTAL_SERVICE']
    
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


@staff_bp.route('/analytics')
@staff_required
def analytics():
    """Staff: Analytics dashboard."""
    analytics_service = current_app.config['ANALYTICS_SERVICE']
    user_dao = current_app.config['USER_DAO']
    
    summary = analytics_service.get_dashboard_summary()
    most_rented = analytics_service.get_most_rented_vehicles(10)
    least_rented = analytics_service.get_least_rented_vehicles(10)
    user = user_dao.get_by_id(session['user_id'])
    
    return render_template('staff_analytics.html',
                         summary=summary,
                         most_rented=most_rented,
                         least_rented=least_rented,
                         user=user)


@staff_bp.route('/activities')
@staff_required
def activities():
    """Staff: User activity logs."""
    analytics_service = current_app.config['ANALYTICS_SERVICE']
    user_dao = current_app.config['USER_DAO']
    
    page = request.args.get('page', 1, type=int)
    all_activities = analytics_service.get_user_activity_logs(1000)  # Get more records for pagination
    user = user_dao.get_by_id(session['user_id'])
    
    # Paginate results
    pagination = paginate(all_activities, page, per_page=10)
    
    return render_template('staff_activities.html',
                         activities=pagination['items'],
                         pagination=pagination,
                         user=user)

