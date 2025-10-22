from __future__ import annotations
from datetime import datetime

class RentalPeriod:
    """
    Represents a rental period with start and end dates with time (DD-MM-YYYY HH:MM).
    Provides validation, duration calculation, and overlap checking.
    """

    def __init__(self, start_date: str, end_date: str):
        # Validate and store the dates first
        self.__start_date = self._validate_datetime(start_date)
        self.__end_date = self._validate_datetime(end_date)

        # Convert to datetime objects for internal operations
        self.__start_dt = datetime.strptime(self.__start_date, "%d-%m-%Y %H:%M")
        self.__end_dt = datetime.strptime(self.__end_date, "%d-%m-%Y %H:%M")

        # Ensure end date is not before start date
        if self.__end_dt <= self.__start_dt:
            raise ValueError("End date must be after start date.")

    # ---- Private validation methods ----
    def _validate_datetime(self, datetime_str: str) -> str:
        """
        Ensure datetime_str is a valid DD-MM-YYYY HH:MM datetime string.
        Returns the same string if valid; raises ValueError otherwise.
        """
        if not isinstance(datetime_str, str):
            raise ValueError("DateTime must be a string (DD-MM-YYYY HH:MM).")
        
        try:
            # Try to parse the datetime string
            datetime.strptime(datetime_str, "%d-%m-%Y %H:%M")
            return datetime_str
        except ValueError as ex:
            raise ValueError(f"Invalid datetime '{datetime_str}'. Expected DD-MM-YYYY HH:MM.") from ex

    # ---- Properties ----
    @property
    def start_date(self) -> str:
        """Start datetime string (DD-MM-YYYY HH:MM)."""
        return self.__start_date

    @start_date.setter
    def start_date(self, value: str) -> None:
        self.__start_date = self._validate_datetime(value)
        self.__start_dt = datetime.strptime(self.__start_date, "%d-%m-%Y %H:%M")
        if self.__end_dt <= self.__start_dt:
            raise ValueError("End date must be after start date.")

    @property
    def end_date(self) -> str:
        """End datetime string (DD-MM-YYYY HH:MM)."""
        return self.__end_date

    @end_date.setter
    def end_date(self, value: str) -> None:
        self.__end_date = self._validate_datetime(value)
        self.__end_dt = datetime.strptime(self.__end_date, "%d-%m-%Y %H:%M")
        if self.__end_dt <= self.__start_dt:
            raise ValueError("End date must be after start date.")

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
        Calculates the number of full days in the period (rounded up).
        For billing purposes, any partial day counts as a full day.
        """
        total_hours = (self.end_dt - self.start_dt).total_seconds() / 3600
        return max(1, int((total_hours + 23) // 24))  # Round up to nearest day
    
    def is_overdue(self) -> bool:
        """
        Returns True if the current time has passed the end datetime.
        """
        return datetime.now() > self.end_dt

    def overlaps_with(self, other: "RentalPeriod") -> bool:
        """
        Returns True if two periods overlap in time.
        """
        s1 = self.start_dt
        e1 = self.end_dt
        s2 = other.start_dt
        e2 = other.end_dt
        return max(s1, s2) < min(e1, e2)

    def __str__(self) -> str:
        return f"{self.start_date} -> {self.end_date}"