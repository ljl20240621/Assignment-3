"""
Pytest configuration and fixtures.
"""
import pytest
import sys
import os

# Add models to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'models'))

