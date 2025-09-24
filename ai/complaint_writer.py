import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ComplaintWriter:
    """
    Template-based complaint generator with customization options.
    
    Generates formal complaint letters from civic issue reports.
    Can be extended with more advanced NLG or GPT-based generation.
    """
    
    # Base template for formal complaints
    FORMAL_TEMPLATE = (
        "To,\n"
        "The Concerned Authority,\n"
        "{authority_name}\n"
        "Municipal Corporation\n\n"
        "Date: {date}\n"
        "Subject: Report regarding {issue_type} - Complaint ID: {complaint_id}\n\n"
        "Respected Sir/Madam,\n\n"
        "I would like to bring to your attention an urgent civic issue that requires "
        "immediate attention and resolution.\n\n"
        "Issue Details:\n"
        "- Type: {issue_type_display}\n"
        "- Location: {location_str}\n"
        "- Description: {description}\n"
        "- Reported on: {date}\n\n"
        "{priority_statement}\n\n"
        "I request you to kindly look into this matter and take necessary action "
        "at the earliest possible time. The issue is causing inconvenience to "
        "residents and requires prompt resolution.\n\n"
        "I would appreciate if you could provide updates on the progress of this "
        "complaint and the expected timeline for resolution.\n\n"
        "Thank you for your attention to this matter.\n\n"
        "Sincerely,\n"
        "Concerned Citizen\n"
        "Civic Eye Platform\n"
        "Complaint ID: {complaint_id}"
    )
    
    # Issue-specific priority statements
    PRIORITY_STATEMENTS = {
        "pothole": (
            "This road damage poses a serious safety risk to commuters and vehicles. "
            "It can cause accidents and vehicle damage if not addressed promptly."
        ),
        "garbage": (
            "The accumulation of waste is creating unhygienic conditions and health hazards. "
            "It may lead to the spread of diseases and environmental pollution."
        ),
        "streetlight": (
            "The non-functional street lighting is compromising public safety, especially "
            "during night hours. This creates security concerns for pedestrians and commuters."
        ),
        "waterlogging": (
            "The water accumulation is causing significant inconvenience to residents and "
            "commuters. It may lead to property damage and health issues if not resolved quickly."
        ),
        "encroachment": (
            "The unauthorized construction/occupation is blocking public access and "
            "violating municipal regulations. This requires immediate intervention."
        ),
        "unknown": (
            "This civic issue requires attention from the appropriate authorities "
            "to ensure public welfare and safety."
        )
    }
    
    # Display names for issue types
    ISSUE_DISPLAY_NAMES = {
        "pothole": "Road Damage / Pothole",
        "garbage": "Waste Management / Garbage Disposal",
        "streetlight": "Street Lighting Issue",
        "waterlogging": "Water Logging / Drainage Problem",
        "encroachment": "Unauthorized Encroachment",
        "unknown": "General Civic Issue"
    }
    
    # Authority mappings
    AUTHORITY_NAMES = {
        "pothole": "Roads and Infrastructure Department",
        "garbage": "Sanitation and Waste Management Department", 
        "streetlight": "Electrical and Public Lighting Department",
        "waterlogging": "Water Supply and Drainage Department",
        "encroachment": "Town Planning and Enforcement Department",
        "unknown": "Municipal Administration"
    }
    
    def __init__(self):
        logger.info("ComplaintWriter initialized")
    
    def _format_location(self, location: Optional[Dict]) -> str:
        """
        Format location information for the complaint.
        
        Args:
            location: Location dictionary with latitude/longitude
            
        Returns:
            Formatted location string
        """
        if not location:
            return "Location not specified"
        
        lat = location.get("latitude")
        lng = location.get("longitude")
        
        if lat is not None and lng is not None:
            # Format coordinates with appropriate precision
            lat_str = f"{lat:.6f}"
            lng_str = f"{lng:.6f}"
            
            # Add cardinal directions for clarity
            lat_dir = "N" if lat >= 0 else "S"
            lng_dir = "E" if lng >= 0 else "W"
            
            return f"GPS Coordinates: {abs(lat):.6f}°{lat_dir}, {abs(lng):.6f}°{lng_dir}"
        
        return "Location coordinates provided"
    
    def _generate_complaint_id(self) -> str:
        """
        Generate a complaint ID if not provided.
        
        Returns:
            Generated complaint ID
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"CE{timestamp}"
    
    def _sanitize_description(self, description: str) -> str:
        """
        Clean and format the description text.
        
        Args:
            description: Raw description text
            
        Returns:
            Cleaned and formatted description
        """
        if not description:
            return "No detailed description provided"
        
        # Basic cleanup
        cleaned = description.strip()
        
        # Ensure proper sentence ending
        if cleaned and not cleaned.endswith(('.', '!', '?')):
            cleaned += '.'
        
        # Capitalize first letter
        if cleaned:
            cleaned = cleaned[0].upper() + cleaned[1:]
        
        return cleaned
    
    def generate(self, 
                issue_type: str, 
                description: str, 
                location: Optional[Dict] = None,
                complaint_id: Optional[str] = None) -> str:
        """
        Generate a formal complaint letter.
        
        Args:
            issue_type: Type of civic issue
            description: Description of the problem
            location: Location dictionary with coordinates
            complaint_id: Optional complaint ID
            
        Returns:
            Formatted complaint letter
        """
        logger.debug(f"Generating complaint for issue type: {issue_type}")
        
        # Sanitize inputs
        issue_type = (issue_type or "unknown").lower()
        description = self._sanitize_description(description)
        complaint_id = complaint_id or self._generate_complaint_id()
        
        # Get issue-specific information
        issue_display = self.ISSUE_DISPLAY_NAMES.get(issue_type, issue_type.title())
        priority_statement = self.PRIORITY_STATEMENTS.get(issue_type, 
                                                         self.PRIORITY_STATEMENTS["unknown"])
        authority_name = self.AUTHORITY_NAMES.get(issue_type, 
                                                 self.AUTHORITY_NAMES["unknown"])
        
        # Format location
        location_str = self._format_location(location)
        
        # Get current date
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Generate the complaint
        try:
            complaint = self.FORMAL_TEMPLATE.format(
                authority_name=authority_name,
                date=current_date,
                issue_type=issue_type,
                issue_type_display=issue_display,
                location_str=location_str,
                description=description,
                priority_statement=priority_statement,
                complaint_id=complaint_id
            )
            
            logger.info(f"Generated complaint for {issue_type} (ID: {complaint_id})")
            return complaint
            
        except Exception as e:
            logger.error(f"Error generating complaint: {e}")
            
            # Fallback simple template
            fallback = (
                f"Complaint regarding {issue_display}\n\n"
                f"Date: {current_date}\n"
                f"Location: {location_str}\n\n"
                f"Description: {description}\n\n"
                f"This issue requires immediate attention from the concerned authorities.\n\n"
                f"Complaint ID: {complaint_id}"
            )
            
            return fallback
    
    def generate_acknowledgment(self, complaint_id: str, issue_type: str) -> str:
        """
        Generate an acknowledgment message for the citizen.
        
        Args:
            complaint_id: The complaint ID
            issue_type: Type of issue reported
            
        Returns:
            Acknowledgment message
        """
        issue_display = self.ISSUE_DISPLAY_NAMES.get(issue_type.lower(), 
                                                    issue_type.title())
        
        acknowledgment = (
            f"Dear Citizen,\n\n"
            f"Thank you for reporting the {issue_display} through Civic Eye platform.\n\n"
            f"Your complaint has been registered with ID: {complaint_id}\n\n"
            f"Your report has been forwarded to the {self.AUTHORITY_NAMES.get(issue_type.lower(), 'appropriate department')} "
            f"for necessary action.\n\n"
            f"You can track the status of your complaint using the complaint ID on our platform.\n\n"
            f"We appreciate your civic participation in making our city better.\n\n"
            f"Best regards,\n"
            f"Civic Eye Team"
        )
        
        return acknowledgment
    
    def get_issue_authority(self, issue_type: str) -> str:
        """
        Get the responsible authority for an issue type.
        
        Args:
            issue_type: Type of civic issue
            
        Returns:
            Authority name
        """
        return self.AUTHORITY_NAMES.get(issue_type.lower(), 
                                       self.AUTHORITY_NAMES["unknown"])
    
    def get_supported_issues(self) -> Dict[str, str]:
        """
        Get all supported issue types and their display names.
        
        Returns:
            Dictionary mapping issue types to display names
        """
        return self.ISSUE_DISPLAY_NAMES.copy()
    
    def add_custom_template(self, issue_type: str, template: str, 
                          priority_statement: str = None, 
                          authority_name: str = None):
        """
        Add a custom template for a specific issue type.
        
        Args:
            issue_type: Issue type identifier
            template: Custom template string
            priority_statement: Custom priority statement
            authority_name: Custom authority name
        """
        if priority_statement:
            self.PRIORITY_STATEMENTS[issue_type] = priority_statement
        
        if authority_name:
            self.AUTHORITY_NAMES[issue_type] = authority_name
        
        logger.info(f"Added custom template for issue type: {issue_type}")
