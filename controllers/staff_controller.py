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
    """Staff: User management page with search functionality."""
    user_dao = current_app.config['USER_DAO']
    
    # Get search parameters
    search = request.args.get('search', '').strip()
    name_filter = request.args.get('name', '').strip()
    username_filter = request.args.get('username', '').strip()
    type_filter = request.args.get('type', '').strip()
    contact_filter = request.args.get('contact', '').strip()
    status_filter = request.args.get('status', '').strip()
    
    page = request.args.get('page', 1, type=int)
    all_users = user_dao.get_all()
    user = user_dao.get_by_id(session['user_id'])
    
    # Check if user exists
    if not user:
        flash('User not found. Please log in again.', 'danger')
        session.clear()
        return redirect(url_for('auth.login'))
    
    # Apply filters
    filtered_users = all_users
    
    if search:
        filtered_users = [u for u in filtered_users if 
                         search.lower() in u.renter_id.lower() or
                         search.lower() in u.name.lower() or
                         search.lower() in u.username.lower() or
                         search.lower() in u.kind.lower() or
                         search.lower() in u.contact_info.lower()]
    
    if name_filter:
        filtered_users = [u for u in filtered_users if 
                      name_filter.lower() in u.name.lower()]
    
    if username_filter:
        filtered_users = [u for u in filtered_users if 
                        username_filter.lower() in u.username.lower()]
    
    if type_filter:
        filtered_users = [u for u in filtered_users if 
                        u.kind.lower() == type_filter.lower()]
    
    if contact_filter:
        filtered_users = [u for u in filtered_users if 
                        contact_filter.lower() in u.contact_info.lower()]
    
    if status_filter:
        if status_filter.lower() == 'active':
            filtered_users = [u for u in filtered_users if u.active]
        elif status_filter.lower() == 'inactive':
            filtered_users = [u for u in filtered_users if not u.active]
    
    # Paginate results
    pagination = paginate(filtered_users, page, per_page=10)
    
    return render_template('staff_users.html', 
                         users=pagination['items'], 
                         pagination=pagination,
                         user=user,
                         search=search,
                         name_filter=name_filter,
                         username_filter=username_filter,
                         type_filter=type_filter,
                         contact_filter=contact_filter,
                         status_filter=status_filter)


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
    """Staff: Vehicle management page with search functionality."""
    vehicle_dao = current_app.config['VEHICLE_DAO']
    user_dao = current_app.config['USER_DAO']
    
    # Get search parameters
    search = request.args.get('search', '').strip()
    id_filter = request.args.get('id', '').strip()
    type_filter = request.args.get('type', '').strip()
    make_filter = request.args.get('make', '').strip()
    model_filter = request.args.get('model', '').strip()
    year_filter = request.args.get('year', '').strip()
    price_min = request.args.get('price_min', '').strip()
    price_max = request.args.get('price_max', '').strip()
    specs_filter = request.args.get('specs', '').strip()
    
    page = request.args.get('page', 1, type=int)
    all_vehicles = vehicle_dao.get_all()
    user = user_dao.get_by_id(session['user_id'])
    
    # Apply filters
    filtered_vehicles = all_vehicles
    
    if search:
        filtered_vehicles = [v for v in filtered_vehicles if 
                           search.lower() in v.vehicle_id.lower() or
                           search.lower() in v.make.lower() or
                           search.lower() in v.model.lower() or
                           search.lower() in v.__class__.__name__.lower()]
    
    if id_filter:
        filtered_vehicles = [v for v in filtered_vehicles if 
                           id_filter.lower() in v.vehicle_id.lower()]
    
    if type_filter:
        filtered_vehicles = [v for v in filtered_vehicles if 
                           v.__class__.__name__.lower() == type_filter.lower()]
    
    if make_filter:
        filtered_vehicles = [v for v in filtered_vehicles if 
                           make_filter.lower() in v.make.lower()]
    
    if model_filter:
        filtered_vehicles = [v for v in filtered_vehicles if 
                           model_filter.lower() in v.model.lower()]
    
    if year_filter:
        try:
            year = int(year_filter)
            if 2000 <= year <= 2025:  # Validate year range
                filtered_vehicles = [v for v in filtered_vehicles if v.year == year]
        except ValueError:
            pass  # Invalid year format, ignore filter
    
    if price_min or price_max:
        try:
            min_price = float(price_min) if price_min else 0
            max_price = float(price_max) if price_max else float('inf')
            filtered_vehicles = [v for v in filtered_vehicles if min_price <= v.daily_rate <= max_price]
        except ValueError:
            pass  # Invalid price format, ignore filter
    
    if specs_filter:
        if specs_filter == '2 Door':
            filtered_vehicles = [v for v in filtered_vehicles if 
                               v.__class__.__name__ == 'Car' and v.num_doors == 2]
        elif specs_filter == '4 Door':
            filtered_vehicles = [v for v in filtered_vehicles if 
                               v.__class__.__name__ == 'Car' and v.num_doors == 4]
        elif specs_filter == '5 Door':
            filtered_vehicles = [v for v in filtered_vehicles if 
                               v.__class__.__name__ == 'Car' and v.num_doors == 5]
    
    # Paginate results
    pagination = paginate(filtered_vehicles, page, per_page=10)
    
    return render_template('staff_vehicles.html', 
                         vehicles=pagination['items'],
                         pagination=pagination,
                         user=user,
                         search=search,
                         id_filter=id_filter,
                         type_filter=type_filter,
                         make_filter=make_filter,
                         model_filter=model_filter,
                         year_filter=year_filter,
                         price_min=price_min,
                         price_max=price_max,
                         specs_filter=specs_filter)


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
    """Staff: View all rentals with search functionality."""
    vehicle_dao = current_app.config['VEHICLE_DAO']
    user_dao = current_app.config['USER_DAO']
    rental_service = current_app.config['RENTAL_SERVICE']
    
    # Get search parameters
    search = request.args.get('search', '').strip()
    vehicle_filter = request.args.get('vehicle', '').strip()
    user_filter = request.args.get('user', '').strip()
    user_type_filter = request.args.get('user_type', '').strip()
    start_date_filter = request.args.get('start_date', '').strip()
    end_date_filter = request.args.get('end_date', '').strip()
    status_filter = request.args.get('status', '').strip()
    overdue_filter = request.args.get('overdue', '').strip()
    
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
    
    # Apply filters
    filtered_rentals = enriched_rentals
    
    if search:
        filtered_rentals = [r for r in filtered_rentals if 
                           search.lower() in r['record'].vehicle_id.lower() or
                           search.lower() in r['record'].renter_id.lower() or
                           (r['vehicle'] and search.lower() in f"{r['vehicle'].make} {r['vehicle'].model}".lower()) or
                           (r['renter'] and search.lower() in r['renter'].name.lower())]
    
    if vehicle_filter:
        filtered_rentals = [r for r in filtered_rentals if 
                           vehicle_filter.lower() in r['record'].vehicle_id.lower() or
                           (r['vehicle'] and vehicle_filter.lower() in f"{r['vehicle'].make} {r['vehicle'].model}".lower())]
    
    if user_filter:
        filtered_rentals = [r for r in filtered_rentals if 
                           user_filter.lower() in r['record'].renter_id.lower() or
                           (r['renter'] and user_filter.lower() in r['renter'].name.lower())]
    
    if user_type_filter:
        filtered_rentals = [r for r in filtered_rentals if 
                           r['renter'] and r['renter'].kind.lower() == user_type_filter.lower()]
    
    if start_date_filter or end_date_filter:
        # Filter by rental period date range
        from datetime import datetime, time
        try:
            # Convert date strings to datetime objects with time boundaries
            if start_date_filter:
                start_date = datetime.strptime(start_date_filter, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                start_date = None
                
            if end_date_filter:
                end_date = datetime.strptime(end_date_filter, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
            else:
                end_date = None
            
            def is_rental_in_date_range(rental):
                if not rental['record'].period or not rental['record'].period.start_date or not rental['record'].period.end_date:
                    return False
                
                # Parse rental period dates
                rental_start = datetime.strptime(rental['record'].period.start_date, "%d-%m-%Y %H:%M")
                rental_end = datetime.strptime(rental['record'].period.end_date, "%d-%m-%Y %H:%M")
                
                # Check if rental period overlaps with query range
                if start_date and end_date:
                    # Both dates provided: rental must overlap with query range
                    return not (rental_end < start_date or rental_start > end_date)
                elif start_date:
                    # Only start date provided: rental must start on or after this date
                    return rental_start >= start_date
                elif end_date:
                    # Only end date provided: rental must end on or before this date
                    return rental_end <= end_date
                return True
                
            filtered_rentals = [r for r in filtered_rentals if is_rental_in_date_range(r)]
        except ValueError:
            pass  # Invalid date format, ignore filter
    
    if status_filter:
        if status_filter.lower() == 'active':
            filtered_rentals = [r for r in filtered_rentals if not r['record'].returned]
        elif status_filter.lower() == 'returned':
            filtered_rentals = [r for r in filtered_rentals if r['record'].returned]
    
    if overdue_filter and overdue_filter.lower() == 'yes':
        from datetime import datetime
        now = datetime.now()
        filtered_rentals = [r for r in filtered_rentals if 
                           not r['record'].returned and 
                           r['record'].period and 
                           r['record'].period.end_date and
                           datetime.strptime(r['record'].period.end_date, "%d-%m-%Y %H:%M") < now]
    
    # Paginate results
    pagination = paginate(filtered_rentals, page, per_page=10)
    
    # Calculate global statistics for all rentals (not filtered)
    total_rentals = len(enriched_rentals)
    active_rentals = len([r for r in enriched_rentals if not r['record'].returned])
    returned_rentals = len([r for r in enriched_rentals if r['record'].returned])
    total_revenue = sum(r['record'].total_cost for r in enriched_rentals)
    
    return render_template('staff_rentals.html', 
                         rentals=pagination['items'],
                         pagination=pagination,
                         user=user,
                         total_rentals=total_rentals,
                         active_rentals=active_rentals,
                         returned_rentals=returned_rentals,
                         total_revenue=total_revenue,
                         search=search,
                         vehicle_filter=vehicle_filter,
                         user_filter=user_filter,
                         user_type_filter=user_type_filter,
                         start_date_filter=start_date_filter,
                         end_date_filter=end_date_filter,
                         status_filter=status_filter,
                         overdue_filter=overdue_filter)


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

