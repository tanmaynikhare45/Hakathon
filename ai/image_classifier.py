import os
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ImageIssueClassifier:
    """
    Hugging Face-based image classifier with graceful fallback.
    
    Uses transformers pipeline for image-classification if available.
    Maps raw labels to civic issue categories heuristically.
    """
    
    SUPPORTED_ISSUES = [
        "garbage",
        "pothole", 
        "streetlight",
        "waterlogging",
        "encroachment",
    ]
    
    # Mapping of potential model outputs to our issue categories
    LABEL_MAPPINGS = {
        # Garbage/Waste related
        "trash": "garbage",
        "garbage": "garbage", 
        "waste": "garbage",
        "dump": "garbage",
        "litter": "garbage",
        "refuse": "garbage",
        "rubbish": "garbage",
        "debris": "garbage",
        "dumpster": "garbage",
        "landfill": "garbage",
        
        # Pothole/Road related
        "pothole": "pothole",
        "hole": "pothole",
        "asphalt": "pothole", 
        "road damage": "pothole",
        "crack": "pothole",
        "pavement": "pothole",
        "street": "pothole",
        "road": "pothole",
        "highway": "pothole",
        
        # Street light related
        "street light": "streetlight",
        "streetlight": "streetlight",
        "lamp": "streetlight", 
        "light pole": "streetlight",
        "lighting": "streetlight",
        "bulb": "streetlight",
        "illumination": "streetlight",
        
        # Water/flooding related
        "flood": "waterlogging",
        "water": "waterlogging",
        "waterlog": "waterlogging",
        "drainage": "waterlogging",
        "puddle": "waterlogging", 
        "overflow": "waterlogging",
        "stagnant": "waterlogging",
        
        # Encroachment related
        "encroach": "encroachment",
        "illegal structure": "encroachment",
        "kiosk": "encroachment",
        "unauthorized": "encroachment",
        "construction": "encroachment",
        "building": "encroachment",
        "structure": "encroachment",
    }
    
    def __init__(self):
        self.pipeline = None
        self.model_id = os.getenv("HUGGINGFACE_IMAGE_MODEL", "google/vit-base-patch16-224")
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Hugging Face model pipeline."""
        try:
            from transformers import pipeline
            logger.info(f"Initializing image classifier with model: {self.model_id}")
            self.pipeline = pipeline("image-classification", model=self.model_id)
            logger.info("Image classifier initialized successfully")
        except ImportError:
            logger.warning("Transformers not available, image classification will use fallback")
            self.pipeline = None
        except Exception as e:
            logger.error(f"Failed to initialize image classifier: {e}")
            self.pipeline = None
    
    def _map_label_to_issue(self, raw_label: str) -> Optional[str]:
        """
        Map a raw classification label to our civic issue categories.
        
        Args:
            raw_label: Raw label from the model
            
        Returns:
            Mapped issue type or None if no mapping found
        """
        if not raw_label:
            return None
            
        # Convert to lowercase for comparison
        label_lower = raw_label.lower()
        
        # Direct mapping first
        if label_lower in self.LABEL_MAPPINGS:
            return self.LABEL_MAPPINGS[label_lower]
        
        # Check if any mapping key is contained in the label
        for keyword, issue_type in self.LABEL_MAPPINGS.items():
            if keyword in label_lower:
                return issue_type
        
        # Special cases with more complex logic
        if any(word in label_lower for word in ["broken", "damaged", "cracked"]):
            if any(word in label_lower for word in ["road", "street", "pavement"]):
                return "pothole"
            elif any(word in label_lower for word in ["light", "lamp", "bulb"]):
                return "streetlight"
        
        return None
    
    def classify_image(self, image_path: str) -> Optional[str]:
        """
        Classify a civic issue from an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Classified issue type or None if classification fails
        """
        if not self.pipeline:
            logger.warning("Image classifier not available, returning None")
            return None
            
        # Validate image path
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return None
        
        try:
            from PIL import Image
            
            # Load and preprocess image
            logger.debug(f"Processing image: {image_path}")
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Get predictions from model
            results = self.pipeline(image)
            
            if not results:
                logger.warning("No classification results returned")
                return None
            
            # Process results (usually sorted by confidence)
            logger.debug(f"Classification results: {results}")
            
            # Try to map each result until we find a match
            for result in results:
                label = result.get("label", "")
                confidence = result.get("score", 0.0)
                
                logger.debug(f"Checking label: '{label}' with confidence: {confidence}")
                
                # Only consider predictions with reasonable confidence
                if confidence < 0.1:  # 10% minimum confidence
                    continue
                
                mapped_issue = self._map_label_to_issue(label)
                if mapped_issue:
                    logger.info(f"Image classified as '{mapped_issue}' (confidence: {confidence:.3f})")
                    return mapped_issue
            
            logger.info("No civic issue detected in image")
            return None
            
        except ImportError:
            logger.error("PIL not available for image processing")
            return None
        except Exception as e:
            logger.error(f"Error classifying image {image_path}: {e}")
            return None
    
    def get_supported_issues(self) -> list:
        """Get list of supported issue types."""
        return self.SUPPORTED_ISSUES.copy()
    
    def is_available(self) -> bool:
        """Check if the image classifier is available."""
        return self.pipeline is not None
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "model_id": self.model_id,
            "available": self.is_available(),
            "supported_issues": self.get_supported_issues()
        }
