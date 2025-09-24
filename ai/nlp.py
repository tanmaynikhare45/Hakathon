import os
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class ComplaintNLPAnalyzer:
    """
    Zero-shot classifier with fallback to simple keywords.
    
    Uses transformers zero-shot classification when available,
    falls back to keyword matching for robustness.
    """
    
    # Keyword mappings for fallback classification
    KEYWORD_MAPPINGS = {
        "pothole": [
            "pothole", "road hole", "broken road", "cracked road", "damaged road",
            "road crack", "street crack", "pavement crack", "asphalt crack",
            "road damage", "street damage", "pavement damage", "surface damage",
            "road repair", "street repair", "चर्राहा", "सड़क में गड्ढा", "खड्डा"
        ],
        "garbage": [
            "garbage", "trash", "waste", "dump", "litter", "refuse", "rubbish",
            "dustbin", "waste bin", "garbage bin", "overflowing", "smell",
            "stench", "dirty", "unclean", "कूड़ा", "गंदगी", "कचरा", "कूड़ादान"
        ],
        "streetlight": [
            "street light", "streetlight", "lamp", "light not working", "dark",
            "lighting", "bulb", "pole light", "light pole", "broken light",
            "dim light", "flickering", "no light", "बत्ती", "रोशनी", "लाइट"
        ],
        "waterlogging": [
            "waterlog", "waterlogging", "flood", "water on road", "drainage",
            "water stagnant", "overflow", "blocked drain", "water accumulation",
            "puddle", "standing water", "सड़क पर पानी", "जल भराव", "बाढ़"
        ],
        "encroachment": [
            "encroach", "encroachment", "illegal construction", "hawker",
            "unauthorized structure", "illegal building", "blocking road",
            "footpath blocked", "unauthorized vendor", "illegal occupation",
            "अतिक्रमण", "अवैध निर्माण", "रास्ता रोकना"
        ]
    }
    
    def __init__(self):
        self.zero_shot_pipeline = None
        self.candidate_labels = self._get_candidate_labels()
        self.model_id = os.getenv("HUGGINGFACE_NLP_MODEL", "facebook/bart-large-mnli")
        self._initialize_model()
    
    def _get_candidate_labels(self) -> List[str]:
        """Get candidate labels from environment or use defaults."""
        env_labels = os.getenv("NLP_CANDIDATE_LABELS", "")
        if env_labels:
            return [label.strip() for label in env_labels.split(",") if label.strip()]
        return list(self.KEYWORD_MAPPINGS.keys()) + ["unknown"]
    
    def _initialize_model(self):
        """Initialize the zero-shot classification model."""
        try:
            from transformers import pipeline
            logger.info(f"Initializing NLP analyzer with model: {self.model_id}")
            self.zero_shot_pipeline = pipeline(
                "zero-shot-classification", 
                model=self.model_id
            )
            logger.info("NLP analyzer initialized successfully")
        except ImportError:
            logger.warning("Transformers not available, NLP will use keyword fallback")
            self.zero_shot_pipeline = None
        except Exception as e:
            logger.error(f"Failed to initialize NLP model: {e}")
            self.zero_shot_pipeline = None
    
    def _classify_with_keywords(self, text: str) -> str:
        """
        Fallback keyword-based classification.
        
        Args:
            text: Input text to classify
            
        Returns:
            Best matching issue type or "unknown"
        """
        if not text:
            return "unknown"
        
        text_lower = text.lower()
        matches = {}
        
        # Count keyword matches for each category
        for issue_type, keywords in self.KEYWORD_MAPPINGS.items():
            match_count = 0
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    # Give higher weight to exact matches
                    weight = 2 if keyword.lower() == text_lower else 1
                    match_count += weight
            
            if match_count > 0:
                matches[issue_type] = match_count
        
        # Return the category with the highest match count
        if matches:
            best_match = max(matches, key=matches.get)
            logger.debug(f"Keyword classification: '{best_match}' with {matches[best_match]} matches")
            return best_match
        
        return "unknown"
    
    def _classify_with_model(self, text: str) -> str:
        """
        Model-based zero-shot classification.
        
        Args:
            text: Input text to classify
            
        Returns:
            Predicted issue type or "unknown"
        """
        try:
            result = self.zero_shot_pipeline(text, self.candidate_labels)
            
            if not result or "labels" not in result:
                logger.warning("Invalid result from zero-shot classifier")
                return "unknown"
            
            labels = result["labels"]
            scores = result.get("scores", [])
            
            if not labels:
                return "unknown"
            
            # Get the best prediction
            best_label = labels[0]
            best_score = scores[0] if scores else 0.0
            
            # Only trust predictions above a certain threshold
            min_confidence = float(os.getenv("NLP_MIN_CONFIDENCE", "0.3"))
            if best_score < min_confidence:
                logger.debug(f"Low confidence prediction ({best_score:.3f}), falling back to keywords")
                return self._classify_with_keywords(text)
            
            logger.debug(f"Model classification: '{best_label}' with confidence: {best_score:.3f}")
            return best_label
            
        except Exception as e:
            logger.error(f"Error in model classification: {e}")
            return self._classify_with_keywords(text)
    
    def analyze(self, text: str) -> Dict[str, str]:
        """
        Analyze complaint text and classify the issue type.
        
        Args:
            text: Input complaint text
            
        Returns:
            Dictionary with classification results
        """
        if not text or not text.strip():
            return {"issue_type": "unknown"}
        
        content = text.strip()
        logger.debug(f"Analyzing text: '{content[:100]}...'")
        
        # Try model-based classification first
        if self.zero_shot_pipeline:
            issue_type = self._classify_with_model(content)
        else:
            # Fall back to keyword-based classification
            issue_type = self._classify_with_keywords(content)
        
        # Additional analysis could be added here
        result = {
            "issue_type": issue_type,
            "confidence_method": "model" if self.zero_shot_pipeline else "keywords"
        }
        
        logger.info(f"Text classified as: {issue_type}")
        return result
    
    def extract_keywords(self, text: str, issue_type: str = None) -> List[str]:
        """
        Extract relevant keywords from text.
        
        Args:
            text: Input text
            issue_type: Optional issue type to focus keyword extraction
            
        Returns:
            List of relevant keywords
        """
        if not text:
            return []
        
        text_lower = text.lower()
        found_keywords = []
        
        # Get keywords to search
        if issue_type and issue_type in self.KEYWORD_MAPPINGS:
            keyword_sets = {issue_type: self.KEYWORD_MAPPINGS[issue_type]}
        else:
            keyword_sets = self.KEYWORD_MAPPINGS
        
        # Find matching keywords
        for category, keywords in keyword_sets.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    found_keywords.append(keyword)
        
        return list(set(found_keywords))  # Remove duplicates
    
    def get_supported_issues(self) -> List[str]:
        """Get list of supported issue types."""
        return list(self.KEYWORD_MAPPINGS.keys())
    
    def is_available(self) -> bool:
        """Check if the advanced NLP model is available."""
        return self.zero_shot_pipeline is not None
    
    def get_model_info(self) -> dict:
        """Get information about the NLP analyzer."""
        return {
            "model_id": self.model_id,
            "model_available": self.is_available(),
            "fallback_method": "keyword_matching",
            "supported_issues": self.get_supported_issues(),
            "candidate_labels": self.candidate_labels
        }
    
    def add_keywords(self, issue_type: str, keywords: List[str]):
        """
        Add custom keywords for an issue type.
        
        Args:
            issue_type: The issue category
            keywords: List of keywords to add
        """
        if issue_type not in self.KEYWORD_MAPPINGS:
            self.KEYWORD_MAPPINGS[issue_type] = []
        
        self.KEYWORD_MAPPINGS[issue_type].extend(keywords)
        logger.info(f"Added {len(keywords)} keywords for issue type: {issue_type}")
