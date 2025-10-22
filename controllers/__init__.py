"""
Controllers package for Vehicle Rental System.
Contains Blueprint controllers for different application areas.
"""

from flask import session
from functools import wraps
from flask import flash, redirect, url_for


def login_required(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def staff_required(f):
    """Decorator to require staff privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from models.dao.user_dao import UserDAO
        import os
        
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Get user_dao from app config
        from flask import current_app
        user_dao = current_app.config['USER_DAO']
        auth_service = current_app.config['AUTH_SERVICE']
        
        user = user_dao.get_by_id(session['user_id'])
        if not user or not auth_service.is_staff(user):
            flash('Staff access required.', 'danger')
            return redirect(url_for('auth.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


def customer_required(f):
    """Decorator to require customer (non-staff) privileges."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        from flask import current_app
        user_dao = current_app.config['USER_DAO']
        auth_service = current_app.config['AUTH_SERVICE']
        
        user = user_dao.get_by_id(session['user_id'])
        if not user or not auth_service.can_rent(user):
            flash('Customer access required.', 'danger')
            return redirect(url_for('auth.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

