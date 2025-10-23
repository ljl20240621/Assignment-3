"""
Customer Controller - Handles vehicle browsing, rental, and return operations.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from controllers import login_required, customer_required
from datetime import datetime
import json

customer_bp = Blueprint('customer', __name__)


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


@customer_bp.route('/vehicles')
@login_required
def vehicles():
    """Vehicle listing page."""
    vehicle_dao = current_app.config['VEHICLE_DAO']
    user_dao = current_app.config['USER_DAO']
    rental_service = current_app.config['RENTAL_SERVICE']
    
    # Get filter parameters
    search = request.args.get('search', '').strip()
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
    
    # Search filter
    if search:
        search_lower = search.lower()
        all_filtered_vehicles = [
            v for v in all_filtered_vehicles 
            if search_lower in v.make.lower() 
            or search_lower in v.model.lower() 
            or search_lower in v.vehicle_id.lower()
        ]
    
    # Filter by status
    if status == 'available':
        all_filtered_vehicles = [v for v in all_filtered_vehicles if not v.get_active_rentals()]
    elif status == 'rented':
        all_filtered_vehicles = [v for v in all_filtered_vehicles if v.get_active_rentals()]
    
    # Filter by availability period
    if start_date or end_date:
        try:
            from models.services.rental_period import RentalPeriod
            from datetime import timedelta
            
            # If only one date is provided, use reasonable defaults
            if start_date and not end_date:
                # If only start date: check from start to 30 days later
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = start_dt + timedelta(days=30)
            elif end_date and not start_date:
                # If only end date: check from now to end date
                start_dt = datetime.now()
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                # Both dates provided
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Validate date range
            if end_dt <= start_dt:
                flash('End date must be after start date.', 'warning')
            else:
                # Convert to DD-MM-YYYY HH:MM format for RentalPeriod
                start_formatted = start_dt.strftime('%d-%m-%Y %H:%M')
                end_formatted = end_dt.strftime('%d-%m-%Y %H:%M')
                
                # Create a rental period to check availability
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
    
    # Check if user exists
    if not user:
        flash('User not found. Please log in again.', 'danger')
        session.clear()
        return redirect(url_for('auth.login'))
    
    return render_template('vehicles.html',
                         vehicles=pagination['items'],
                         pagination=pagination,
                         all_makes=all_makes,
                         user=user,
                         current_search=search,
                         current_type=vehicle_type,
                         current_make=make,
                         current_price_range=price_range,
                         current_status=status,
                         current_start_date=start_date,
                         current_end_date=end_date)


@customer_bp.route('/vehicles/<vehicle_id>')
@login_required
def vehicle_detail(vehicle_id):
    """Vehicle detail page."""
    vehicle_dao = current_app.config['VEHICLE_DAO']
    user_dao = current_app.config['USER_DAO']
    
    vehicle = vehicle_dao.get_by_id(vehicle_id)
    
    if not vehicle:
        flash('Vehicle not found.', 'danger')
        return redirect(url_for('customer.vehicles'))
    
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
    
    booked_ranges_json = json.dumps(booked_ranges)
    
    return render_template('vehicle_detail.html',
                         vehicle=vehicle,
                         user=user,
                         rental_history=rental_history,
                         booked_ranges=booked_ranges_json)


@customer_bp.route('/rent/<vehicle_id>', methods=['GET', 'POST'])
@customer_required
def rent_vehicle(vehicle_id):
    """Rent a vehicle."""
    vehicle_dao = current_app.config['VEHICLE_DAO']
    user_dao = current_app.config['USER_DAO']
    rental_service = current_app.config['RENTAL_SERVICE']
    
    # Reload data to ensure we have the latest information
    vehicle_dao.load()
    user_dao.load()
    
    vehicle = vehicle_dao.get_by_id(vehicle_id)
    
    if not vehicle:
        flash('Vehicle not found.', 'danger')
        return redirect(url_for('customer.vehicles'))
    
    # Get booked date ranges for this vehicle - only active rentals
    booked_ranges = []
    active_rentals = vehicle.get_active_rentals()
    for rental in active_rentals:
        booked_ranges.append({
            'start': rental.period.start_date,
            'end': rental.period.end_date
        })
    
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        start_time = request.form.get('start_time')
        end_date = request.form.get('end_date')
        end_time = request.form.get('end_time')
        
        try:
            # Combine date and time, then convert to DD-MM-YYYY HH:MM format
            start_datetime = f"{start_date}T{start_time}"
            end_datetime = f"{end_date}T{end_time}"
            
            start_dt = datetime.strptime(start_datetime, '%Y-%m-%dT%H:%M')
            end_dt = datetime.strptime(end_datetime, '%Y-%m-%dT%H:%M')
            start_datetime_formatted = start_dt.strftime('%d-%m-%Y %H:%M')
            end_datetime_formatted = end_dt.strftime('%d-%m-%Y %H:%M')
            
            from models.services.rental_period import RentalPeriod
            period = RentalPeriod(start_datetime_formatted, end_datetime_formatted)
            
            # Calculate rental details for invoice
            user = user_dao.get_by_id(session['user_id'])
            days = period.calculate_duration()
            discount_factor = user.discount_factor(days)
            original_cost = vehicle.daily_rate * days
            discount_rate = (1 - discount_factor) * 100  # Convert to percentage
            
            rental_id, total_cost = rental_service.rent_vehicle(
                vehicle_id,
                session['user_id'],
                period
            )
            
            flash(f'Vehicle rented successfully! Total cost: ${total_cost:.2f}', 'success')
            return redirect(url_for('customer.rental_confirmation', vehicle_id=vehicle_id, 
                                  start_date=start_datetime_formatted, 
                                  end_date=end_datetime_formatted,
                                  total_cost=f'{total_cost:.2f}',
                                  original_cost=f'{original_cost:.2f}',
                                  discount_rate=f'{discount_rate:.2f}',
                                  days=days,
                                  rental_id=rental_id))
        
        except ValueError as e:
            flash(str(e), 'danger')
    
    user = user_dao.get_by_id(session['user_id'])
    
    # Convert booked ranges to JavaScript-friendly format (YYYY-MM-DD)
    booked_ranges_js = []
    for rental_range in booked_ranges:
        # Convert DD-MM-YYYY HH:MM to YYYY-MM-DD
        start_date_str = rental_range['start'].split(' ')[0]  # Get date part only
        end_date_str = rental_range['end'].split(' ')[0]      # Get date part only
        
        start_parts = start_date_str.split('-')
        end_parts = end_date_str.split('-')
        
        booked_ranges_js.append({
            'start': f'{start_parts[2]}-{start_parts[1]}-{start_parts[0]}',
            'end': f'{end_parts[2]}-{end_parts[1]}-{end_parts[0]}'
        })
    
    return render_template('rent_vehicle.html', 
                         vehicle=vehicle, 
                         user=user,
                         booked_ranges=json.dumps(booked_ranges_js))


@customer_bp.route('/rental-confirmation')
@customer_required
def rental_confirmation():
    """Rental confirmation/invoice page."""
    vehicle_dao = current_app.config['VEHICLE_DAO']
    user_dao = current_app.config['USER_DAO']
    
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


@customer_bp.route('/return/<vehicle_id>', methods=['GET', 'POST'])
@customer_required
def return_vehicle(vehicle_id):
    """Return a rented vehicle."""
    vehicle_dao = current_app.config['VEHICLE_DAO']
    user_dao = current_app.config['USER_DAO']
    rental_service = current_app.config['RENTAL_SERVICE']
    
    # Get source parameter to determine return destination
    source = request.args.get('source', 'my-rentals')
    return_to = 'customer.my_rentals'  # Default fallback
    
    if source == 'dashboard':
        return_to = 'auth.dashboard'
    elif source == 'my-rentals':
        return_to = 'customer.my_rentals'
    
    # Get rental_id parameter
    rental_id = request.args.get('rental_id')
    
    user = user_dao.get_by_id(session['user_id'])
    
    # Check if user exists
    if not user:
        flash('User not found. Please log in again.', 'danger')
        session.clear()
        return redirect(url_for('auth.login'))
    
    # Find active rental by rental_id if provided, otherwise fallback to old method
    active_rental = None
    if rental_id:
        # Use rental_id to find the specific rental
        for rental in user.rental_history:
            if rental.rental_id == rental_id and not rental.returned:
                active_rental = rental
                break
    else:
        # Fallback to old method (for backward compatibility)
        for rental in user.rental_history:
            if rental.vehicle_id == vehicle_id and not rental.returned:
                active_rental = rental
                break
    
    if not active_rental:
        flash('No active rental found for this vehicle.', 'warning')
        return redirect(url_for(return_to))
    
    # Get vehicle information from the rental record
    vehicle = vehicle_dao.get_by_id(active_rental.vehicle_id)
    if not vehicle:
        flash('Vehicle not found.', 'danger')
        return redirect(url_for(return_to))
    
    if request.method == 'POST':
        return_datetime = request.form.get('return_datetime')
        
        try:
            # Convert datetime from YYYY-MM-DDTHH:MM to DD-MM-YYYY HH:MM
            return_dt = datetime.strptime(return_datetime, '%Y-%m-%dT%H:%M')
            start_dt = datetime.strptime(active_rental.period.start_date, '%d-%m-%Y %H:%M')
            end_dt = datetime.strptime(active_rental.period.end_date, '%d-%m-%Y %H:%M')

            # Check if already returned (idempotent check)
            if active_rental.returned:
                flash('This vehicle has already been returned.', 'info')
                return redirect(url_for(return_to))
            
            # Return the vehicle using rental ID
            success = rental_service.return_vehicle_by_id(active_rental.rental_id)
            
            if success:
                # early return
                if return_dt < start_dt:
                    flash('Vehicle early returned successfully! 50% of the rental cost will be returned.', 'success')
                    return redirect(url_for(return_to))
                # late return
                if return_dt > end_dt:
                    flash('Vehicle late returned successfully! please pay the late return fee.', 'danger')
                    return redirect(url_for(return_to))
                # normal return
                flash('Vehicle returned successfully!', 'success')
                return redirect(url_for(return_to))
            else:
                # Check if it was already returned during the process
                user = user_dao.get_by_id(session['user_id'])
                updated_rental = None
                if rental_id:
                    # Use rental_id to find the specific rental
                    for rental in user.rental_history:
                        if rental.rental_id == rental_id:
                            updated_rental = rental
                            break
                else:
                    # Fallback to old method
                    for rental in user.rental_history:
                        if rental.vehicle_id == vehicle_id and not rental.returned:
                            updated_rental = rental
                            break
                
                if updated_rental and updated_rental.returned:
                    flash('Vehicle was already returned.', 'info')
                    return redirect(url_for(return_to))
                else:
                    flash('Failed to return vehicle. Please try again.', 'danger')
        
        except ValueError as e:
            flash(str(e), 'danger')
    print("return_to", return_to)
    return render_template('return_vehicle.html', vehicle=vehicle, user=user, rental=active_rental, return_to=return_to)


@customer_bp.route('/my-rentals')
@customer_required
def my_rentals():
    """View rental history."""
    vehicle_dao = current_app.config['VEHICLE_DAO']
    user_dao = current_app.config['USER_DAO']
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    user = user_dao.get_by_id(session['user_id'])
    
    # Check if user exists
    if not user:
        flash('User not found. Please log in again.', 'danger')
        session.clear()
        return redirect(url_for('auth.login'))
    
    # Get all rental history for global statistics
    all_rental_history = list(user.rental_history)
    
    # Calculate global statistics
    total_rentals = len(all_rental_history)
    total_spent = sum(rental.total_cost for rental in all_rental_history)
    active_rentals = len([r for r in all_rental_history if not r.returned])
    
    # Apply filters to rental history
    rental_history = list(user.rental_history)
    
    # Status filter
    if status_filter:
        if status_filter == 'active':
            rental_history = [r for r in rental_history if not r.returned]
        elif status_filter == 'returned':
            rental_history = [r for r in rental_history if r.returned]
    
    # Search filter
    if search:
        search_lower = search.lower()
        filtered_history = []
        for rental in rental_history:
            # Get vehicle details for searching
            vehicle = vehicle_dao.get_by_id(rental.vehicle_id)
            if vehicle:
                # Search in vehicle_id, make, and model
                if (search_lower in rental.vehicle_id.lower() or
                    search_lower in vehicle.make.lower() or
                    search_lower in vehicle.model.lower()):
                    filtered_history.append(rental)
        rental_history = filtered_history
    
    # Sort rental history: first by status (active first), then by start date (descending)
    def sort_key(rental):
        # Status priority: active (False) comes before returned (True)
        status_priority = 0 if not rental.returned else 1
        
        # Parse start date for sorting
        from datetime import datetime
        start_date = datetime.strptime(rental.period.start_date, '%d-%m-%Y %H:%M')
        
        return (status_priority, -start_date.timestamp())  # Negative for descending order
    
    rental_history.sort(key=sort_key)
    
    # Paginate results
    pagination = paginate(rental_history, page, per_page=10)
    
    # Create a dictionary of vehicles for easy lookup in template
    vehicles_dict = {}
    for rental in pagination['items']:
        if rental.vehicle_id not in vehicles_dict:
            vehicle = vehicle_dao.get_by_id(rental.vehicle_id)
            if vehicle:
                vehicles_dict[rental.vehicle_id] = vehicle
    
    return render_template('my_rentals.html', 
                         user=user, 
                         rental_history=pagination['items'],
                         pagination=pagination,
                         current_search=search,
                         current_status=status_filter,
                         vehicles_dict=vehicles_dict,
                         total_rentals=total_rentals,
                         total_spent=total_spent,
                         active_rentals=active_rentals)


@customer_bp.route('/invoice')
@customer_required
def view_invoice():
    """View invoice for a specific rental."""
    vehicle_dao = current_app.config['VEHICLE_DAO']
    user_dao = current_app.config['USER_DAO']
    
    vehicle_id = request.args.get('vehicle_id')
    start_date = request.args.get('start_date')
    
    user = user_dao.get_by_id(session['user_id'])
    vehicle = vehicle_dao.get_by_id(vehicle_id)
    
    if not vehicle:
        flash('Vehicle not found.', 'danger')
        return redirect(url_for('customer.my_rentals'))
    
    # Find the rental record
    rental_record = None
    for rental in user.rental_history:
        if rental.vehicle_id == vehicle_id and rental.period.start_date == start_date:
            rental_record = rental
            break
    
    if not rental_record:
        flash('Rental record not found.', 'warning')
        return redirect(url_for('customer.my_rentals'))
    
    # Calculate invoice details
    days = rental_record.period.calculate_duration()
    discount_factor = user.discount_factor(days)
    
    # Calculate original cost (before discount)
    original_cost = rental_record.total_cost / discount_factor
    
    # Calculate discount rate as percentage
    discount_rate = (1 - discount_factor) * 100
    
    # Format to 2 decimal places
    total_cost = f"{rental_record.total_cost:.2f}"
    original_cost = f"{original_cost:.2f}"
    discount_rate = f"{discount_rate:.2f}"
    
    return render_template('rental_confirmation.html',
                         vehicle=vehicle,
                         user=user,
                         start_date=rental_record.period.start_date,
                         end_date=rental_record.period.end_date,
                         total_cost=total_cost,
                         original_cost=original_cost,
                         discount_rate=discount_rate,
                         days=days,
                         is_invoice=True)

