import logging
from typing import Tuple, Optional, List, Dict
from math import radians, sin, cos, asin, sqrt

logger = logging.getLogger(__name__)


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees) in kilometers.
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon/2) ** 2
    c = 2 * asin(sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    return c * r


class FakeReportDetector:
    """
    Duplicate/fake detector using TF-IDF similarity + location proximity.
    
    Uses multiple signals to detect potentially fake or duplicate reports:
    1. Text similarity using TF-IDF vectorization
    2. Location proximity (reports within 100m of each other)
    3. Temporal patterns (multiple reports in short time)
    4. Basic content validation
    
    If scikit-learn is unavailable, falls back to heuristic methods.
    """
    
    def __init__(self):
        self.vectorizer = None
        self.min_text_length = 10
        self.proximity_threshold_km = 0.1  # 100 meters
        self.similarity_threshold = 0.7
        self.temporal_window_minutes = 30
        self._ensure_vectorizer()
    
    def _ensure_vectorizer(self):
        """Initialize TF-IDF vectorizer if scikit-learn is available."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vectorizer = TfidfVectorizer(
                min_df=1,
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 2),  # Include bigrams
                lowercase=True,
                strip_accents='unicode'
            )
            logger.info("TF-IDF vectorizer initialized successfully")
        except ImportError:
            logger.warning("scikit-learn not available, using heuristic similarity")
            self.vectorizer = None
        except Exception as e:
            logger.error(f"Failed to initialize TF-IDF vectorizer: {e}")
            self.vectorizer = None
    
    def _calculate_text_similarity(self, text: str, corpus: List[str]) -> float:
        """
        Calculate text similarity using TF-IDF cosine similarity.
        
        Args:
            text: Input text to compare
            corpus: List of existing texts to compare against
            
        Returns:
            Maximum similarity score (0-1)
        """
        if not self.vectorizer or not corpus or not text:
            return 0.0
        
        try:
            import numpy as np
            
            # Prepare documents (input text + corpus)
            documents = [text] + corpus
            
            # Fit and transform
            tfidf_matrix = self.vectorizer.fit_transform(documents)
            
            if tfidf_matrix.shape[0] < 2:
                return 0.0
            
            # Calculate cosine similarity
            input_vector = tfidf_matrix[0].toarray()[0]
            corpus_vectors = tfidf_matrix[1:].toarray()
            
            if corpus_vectors.size == 0:
                return 0.0
            
            # Compute cosine similarities
            similarities = []
            for corpus_vector in corpus_vectors:
                # Cosine similarity formula
                dot_product = np.dot(input_vector, corpus_vector)
                norm_input = np.linalg.norm(input_vector)
                norm_corpus = np.linalg.norm(corpus_vector)
                
                if norm_input == 0 or norm_corpus == 0:
                    similarities.append(0.0)
                else:
                    similarity = dot_product / (norm_input * norm_corpus)
                    similarities.append(similarity)
            
            max_similarity = float(np.max(similarities)) if similarities else 0.0
            logger.debug(f"Text similarity calculated: {max_similarity:.3f}")
            return max_similarity
            
        except Exception as e:
            logger.error(f"Error calculating text similarity: {e}")
            return self._heuristic_text_similarity(text, corpus)
    
    def _heuristic_text_similarity(self, text: str, corpus: List[str]) -> float:
        """
        Fallback heuristic text similarity using simple word overlap.
        
        Args:
            text: Input text
            corpus: List of texts to compare against
            
        Returns:
            Similarity score (0-1)
        """
        if not text or not corpus:
            return 0.0
        
        text_words = set(text.lower().split())
        if not text_words:
            return 0.0
        
        max_similarity = 0.0
        
        for corpus_text in corpus:
            if not corpus_text:
                continue
                
            corpus_words = set(corpus_text.lower().split())
            if not corpus_words:
                continue
            
            # Jaccard similarity
            intersection = text_words.intersection(corpus_words)
            union = text_words.union(corpus_words)
            
            if union:
                similarity = len(intersection) / len(union)
                max_similarity = max(max_similarity, similarity)
        
        return max_similarity
    
    def _check_location_proximity(self, 
                                latitude: Optional[str], 
                                longitude: Optional[str],
                                recent_reports: List[Dict]) -> bool:
        """
        Check if the report location is too close to recent reports.
        
        Args:
            latitude: Input latitude as string
            longitude: Input longitude as string
            recent_reports: List of recent report dictionaries
            
        Returns:
            True if location is suspiciously close to recent reports
        """
        try:
            if latitude is None or longitude is None:
                return False
            
            input_lat = float(latitude)
            input_lng = float(longitude)
            
            # Check bounds
            if not (-90.0 <= input_lat <= 90.0 and -180.0 <= input_lng <= 180.0):
                logger.warning(f"Invalid coordinates: {input_lat}, {input_lng}")
                return True  # Invalid coordinates are suspicious
            
            for report in recent_reports:
                location = report.get("location") or {}
                report_lat = location.get("latitude")
                report_lng = location.get("longitude")
                
                if report_lat is None or report_lng is None:
                    continue
                
                try:
                    distance = _haversine_km(input_lat, input_lng, report_lat, report_lng)
                    
                    if distance <= self.proximity_threshold_km:
                        logger.debug(f"Found nearby report within {distance*1000:.0f}m")
                        return True
                        
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error calculating distance: {e}")
                    continue
            
            return False
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Error processing location: {e}")
            return True  # Treat parsing errors as suspicious
    
    def _check_temporal_patterns(self, recent_reports: List[Dict]) -> float:
        """
        Check for suspicious temporal patterns in recent reports.
        
        Args:
            recent_reports: List of recent reports
            
        Returns:
            Suspicion score (0-1)
        """
        try:
            from datetime import datetime, timedelta
            
            if not recent_reports:
                return 0.0
            
            current_time = datetime.utcnow()
            recent_count = 0
            
            for report in recent_reports:
                try:
                    created_at = report.get("created_at", "")
                    if not created_at:
                        continue
                    
                    # Parse ISO format timestamp
                    report_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    time_diff = current_time - report_time
                    
                    if time_diff <= timedelta(minutes=self.temporal_window_minutes):
                        recent_count += 1
                        
                except (ValueError, TypeError) as e:
                    logger.debug(f"Error parsing timestamp: {e}")
                    continue
            
            # Calculate suspicion based on frequency
            if recent_count >= 5:  # 5+ reports in 30 minutes is suspicious
                return 0.8
            elif recent_count >= 3:  # 3+ reports is moderately suspicious
                return 0.5
            elif recent_count >= 2:  # 2+ reports is slightly suspicious
                return 0.3
            
            return 0.0
            
        except ImportError:
            logger.warning("datetime module unavailable")
            return 0.0
        except Exception as e:
            logger.error(f"Error checking temporal patterns: {e}")
            return 0.0
    
    def _validate_content(self, text: str, image_path: Optional[str]) -> Tuple[bool, float]:
        """
        Validate report content for basic quality checks.
        
        Args:
            text: Report text
            image_path: Path to uploaded image
            
        Returns:
            Tuple of (is_valid, suspicion_score)
        """
        suspicion_score = 0.0
        
        # Check if both text and image are missing
        if not text and not image_path:
            logger.warning("Report has no text or image content")
            return False, 0.9
        
        if text:
            # Check text length
            if len(text.strip()) < self.min_text_length:
                suspicion_score += 0.3
            
            # Check for gibberish (too many repeated characters)
            if len(set(text.lower())) < len(text) * 0.3:  # Less than 30% unique characters
                suspicion_score += 0.4
            
            # Check for spam patterns
            spam_indicators = ['click here', 'free', 'win now', 'limited time', 'act now']
            spam_count = sum(1 for indicator in spam_indicators if indicator in text.lower())
            if spam_count > 0:
                suspicion_score += 0.5
            
            # Check for excessive uppercase
            if text.isupper() and len(text) > 20:
                suspicion_score += 0.2
        
        # Validate image if provided
        if image_path:
            try:
                import os
                if not os.path.exists(image_path):
                    suspicion_score += 0.3
                elif os.path.getsize(image_path) < 1024:  # Less than 1KB is suspicious
                    suspicion_score += 0.4
            except Exception as e:
                logger.warning(f"Error validating image: {e}")
                suspicion_score += 0.2
        
        return suspicion_score < 0.7, min(suspicion_score, 1.0)
    
    def is_fake(self,
                text: str,
                image_path: Optional[str],
                latitude: Optional[str],
                longitude: Optional[str],
                recent_reports: Optional[List[Dict]] = None) -> Tuple[bool, float]:
        """
        Determine if a report is potentially fake or duplicate.
        
        Args:
            text: Report description text
            image_path: Path to uploaded image
            latitude: Location latitude as string
            longitude: Location longitude as string
            recent_reports: List of recent report dictionaries
            
        Returns:
            Tuple of (is_fake, fake_score) where fake_score is 0-1
        """
        logger.debug("Starting fake detection analysis")
        
        recent_reports = recent_reports or []
        total_score = 0.0
        weight_sum = 0.0
        
        # 1. Content validation (weight: 0.3)
        content_valid, content_score = self._validate_content(text, image_path)
        if not content_valid:
            logger.warning("Content validation failed")
        
        total_score += content_score * 0.3
        weight_sum += 0.3
        
        # 2. Text similarity check (weight: 0.4)
        if text and recent_reports:
            corpus = []
            for report in recent_reports:
                report_text = report.get("text") or report.get("voice_text") or ""
                if report_text:
                    corpus.append(report_text)
            
            if corpus:
                text_similarity = self._calculate_text_similarity(text, corpus)
                total_score += text_similarity * 0.4
                weight_sum += 0.4
                
                if text_similarity > 0.8:
                    logger.warning(f"High text similarity detected: {text_similarity:.3f}")
        
        # 3. Location proximity check (weight: 0.2)
        if latitude is not None and longitude is not None and recent_reports:
            is_near = self._check_location_proximity(latitude, longitude, recent_reports)
            proximity_score = 0.7 if is_near else 0.0
            total_score += proximity_score * 0.2
            weight_sum += 0.2
            
            if is_near:
                logger.warning("Report location is very close to recent reports")
        
        # 4. Temporal patterns (weight: 0.1)
        temporal_score = self._check_temporal_patterns(recent_reports)
        total_score += temporal_score * 0.1
        weight_sum += 0.1
        
        # Normalize score
        if weight_sum > 0:
            final_score = total_score / weight_sum
        else:
            final_score = 0.0
        
        # Determine if fake based on threshold
        is_fake = final_score >= self.similarity_threshold
        
        logger.info(f"Fake detection result: {'FAKE' if is_fake else 'GENUINE'} "
                   f"(score: {final_score:.3f})")
        
        return is_fake, final_score
    
    def get_detection_info(self) -> Dict:
        """Get information about the fake detection system."""
        return {
            "vectorizer_available": self.vectorizer is not None,
            "proximity_threshold_m": self.proximity_threshold_km * 1000,
            "similarity_threshold": self.similarity_threshold,
            "temporal_window_minutes": self.temporal_window_minutes,
            "min_text_length": self.min_text_length
        }
