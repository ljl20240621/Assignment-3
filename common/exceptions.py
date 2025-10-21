"""
Custom exceptions for the Vehicle Rental application.
"""
from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models'))
    from services.rental_period import RentalPeriod

class VehicleRentalError(Exception):
    """Base class for all custom vehicle rental exceptions."""
    pass


class VehicleNotFoundError(VehicleRentalError):
    """Raised when a vehicle ID cannot be found."""
    def __init__(self, vehicle_id: str):
        self.vehicle_id = vehicle_id
        super().__init__(f"Vehicle with ID '{vehicle_id}' not found.")


class UserNotFoundError(VehicleRentalError):
    """Raised when a user (renter) ID cannot be found."""
    def __init__(self, renter_id: str):
        self.renter_id = renter_id
        super().__init__(f"User with ID '{renter_id}' not found.")


class OverlappingBookingError(VehicleRentalError):
    """Raised when a requested rental period overlaps with an existing booking."""
    def __init__(self, vehicle_id: str, period: RentalPeriod):
        self.vehicle_id = vehicle_id
        self.period = period
        super().__init__(f"Vehicle '{vehicle_id}' is already booked over {period}.")


class VehicleNotAvailableError(VehicleRentalError):
    """Raised when a vehicle is not available for the requested period."""
    def __init__(self, vehicle_id: str, period: RentalPeriod):
        self.vehicle_id = vehicle_id
        self.period = period
        super().__init__(f"Vehicle '{vehicle_id}' not available over {period}.")


class ReturnNotFoundError(VehicleRentalError):
    """Raised when no matching rental is found for return."""
    def __init__(self, vehicle_id: str, renter_id: str, period: Optional[RentalPeriod] = None):
        self.vehicle_id = vehicle_id
        self.renter_id = renter_id
        self.period = period
        base = f"No matching outstanding rental to return for vehicle '{vehicle_id}' and user '{renter_id}'"
        super().__init__(f"{base} over {period}." if period else base + ".")


class PersistenceError(VehicleRentalError):
    """Raised for problems saving or loading persistent data."""
    def __init__(self, path: str, cause: Exception | None = None):
        self.path = path
        self.cause = cause
        msg = f"Failed saving/loading data at '{path}'."
        super().__init__(f"{msg} Cause: {cause}" if cause else msg)