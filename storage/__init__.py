"""
Storage module for Civic Eye - Database and data persistence components
"""

# Storage module version
__version__ = "1.0.0"

# Import database components
from .db import CivicDB, ReportRecord

__all__ = [
    'CivicDB',
    'ReportRecord'
]
