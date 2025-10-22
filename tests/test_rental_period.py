"""
Unit tests for RentalPeriod class.
"""
import pytest
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models.services.rental_period import RentalPeriod


class TestRentalPeriod:
    """Test RentalPeriod functionality."""
    
    def test_valid_period_creation(self):
        """Test creating a valid rental period."""
        period = RentalPeriod("01-01-2025 09:00", "05-01-2025 18:00")
        assert period.start_date == "01-01-2025 09:00"
        assert period.end_date == "05-01-2025 18:00"
    
    def test_duration_calculation(self):
        """Test duration calculation."""
        period = RentalPeriod("01-01-2025 09:00", "05-01-2025 18:00")
        assert period.calculate_duration() == 5
    
    def test_single_day_rental(self):
        """Test single day rental duration."""
        period = RentalPeriod("01-01-2025 09:00", "01-01-2025 18:00")
        assert period.calculate_duration() == 1
    
    def test_invalid_date_format(self):
        """Test that invalid date format raises error."""
        with pytest.raises(ValueError):
            RentalPeriod("2025-01-01", "2025-01-05")
    
    def test_end_before_start(self):
        """Test that end date before start date raises error."""
        with pytest.raises(ValueError):
            RentalPeriod("05-01-2025 09:00", "01-01-2025 18:00")
    
    def test_overlaps_with(self):
        """Test overlap detection."""
        period1 = RentalPeriod("01-01-2025 09:00", "05-01-2025 18:00")
        period2 = RentalPeriod("03-01-2025 09:00", "07-01-2025 18:00")
        period3 = RentalPeriod("06-01-2025 09:00", "10-01-2025 18:00")
        
        assert period1.overlaps_with(period2) == True
        assert period1.overlaps_with(period3) == False
    
    def test_exact_overlap(self):
        """Test exact period overlap."""
        period1 = RentalPeriod("01-01-2025 09:00", "05-01-2025 18:00")
        period2 = RentalPeriod("01-01-2025 09:00", "05-01-2025 18:00")
        
        assert period1.overlaps_with(period2) == True
    
    def test_adjacent_periods_no_overlap(self):
        """Test that adjacent periods don't overlap."""
        period1 = RentalPeriod("01-01-2025 09:00", "05-01-2025 18:00")
        period2 = RentalPeriod("06-01-2025 09:00", "10-01-2025 18:00")
        
        assert period1.overlaps_with(period2) == False

