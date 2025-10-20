from __future__ import annotations
from datetime import datetime

class RentalPeriod:
    """
    Represents a rental period with start and end dates (DD-MM-YYYY).
    Provides validation, duration calculation, and overlap checking.
    """

    def __init__(self, start_date: str, end_date: str):
        # Validate and store the dates first
        self.__start_date = self._validate_date(start_date)
        self.__end_date = self._validate_date(end_date)

        # Convert to datetime objects for internal operations
        self.__start_dt = datetime.strptime(self.__start_date, "%d-%m-%Y")
        self.__end_dt = datetime.strptime(self.__end_date, "%d-%m-%Y")

        # Ensure end date is not before start date
        if self.__end_dt < self.__start_dt:
            raise ValueError("End date must not be before start date.")

    # ---- Private validation methods ----
    def _validate_date(self, date_str: str) -> str:
        """
        Ensure date_str is a valid DD-MM-YYYY date string.
        Returns the same string if valid; raises ValueError otherwise.
        """
        if not isinstance(date_str, str):
            raise ValueError("Date must be a string (DD-MM-YYYY).")
        
        try:
            # Try to parse the date string
            datetime.strptime(date_str, "%d-%m-%Y")
            return date_str
        except ValueError as ex:
            raise ValueError(f"Invalid date '{date_str}'. Expected DD-MM-YYYY.") from ex

    # ---- Properties ----
    @property
    def start_date(self) -> str:
        """Start date string (DD-MM-YYYY)."""
        return self.__start_date

    @start_date.setter
    def start_date(self, value: str) -> None:
        self.__start_date = self._validate_date(value)
        self.__start_dt = datetime.strptime(self.__start_date, "%d-%m-%Y")
        if self.__end_dt < self.__start_dt:
            raise ValueError("End date must not be before start date.")

    @property
    def end_date(self) -> str:
        """End date string (DD-MM-YYYY)."""
        return self.__end_date

    @end_date.setter
    def end_date(self, value: str) -> None:
        self.__end_date = self._validate_date(value)
        self.__end_dt = datetime.strptime(self.__end_date, "%d-%m-%Y")
        if self.__end_dt < self.__start_dt:
            raise ValueError("End date must not be before start date.")

    @property
    def start_dt(self) -> datetime:
        """Start date as datetime object."""
        return self.__start_dt

    @property
    def end_dt(self) -> datetime:
        """End date as datetime object."""
        return self.__end_dt

    # ---- Methods ----
    def calculate_duration(self) -> int:
        """
        Calculates the inclusive number of days in the period.
        """
        return (self.end_dt - self.start_dt).days + 1

    def overlaps_with(self, other: "RentalPeriod") -> bool:
        """
        Returns True if two periods overlap at least one day.
        """
        s1 = self.start_dt
        e1 = self.end_dt
        s2 = other.start_dt
        e2 = other.end_dt
        return max(s1, s2) <= min(e1, e2)

    def __str__(self) -> str:
        return f"{self.start_date} -> {self.end_date}"