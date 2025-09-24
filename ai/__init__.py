"""
AI module for Civic Eye - Smart Civic Issue Detection and Classification
"""

# AI module version
__version__ = "1.0.0"

# Import all AI components
from .image_classifier import ImageIssueClassifier
from .nlp import ComplaintNLPAnalyzer
from .fake_detection import FakeReportDetector
from .complaint_writer import ComplaintWriter

__all__ = [
    'ImageIssueClassifier',
    'ComplaintNLPAnalyzer', 
    'FakeReportDetector',
    'ComplaintWriter'
]
