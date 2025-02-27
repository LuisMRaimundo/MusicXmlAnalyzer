# core/cache.py

"""
Caching utilities for expensive analysis operations.
"""

import os
import json
import hashlib
import pickle
from dataclasses import asdict
from typing import Any, Dict, Optional
import logging
from functools import wraps

from .model import ScoreData

logger = logging.getLogger(__name__)

class AnalysisCache:
    """Manages caching of analysis results to avoid redundant calculations."""
    
    def __init__(self, cache_dir: str = ".musicxml_cache"):
        """Initialize cache with specified directory."""
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_cache_key(self, score_data: ScoreData, analysis_type: str, params: Dict) -> str:
        """Generate a unique cache key for the score and analysis parameters."""
        # Create a simplified representation of the score for hashing
        score_hash_data = {
            'title': score_data.title,
            'composer': score_data.composer,
            'time_signature': score_data.time_signature,
            'note_count': len(score_data.notes),
            'dynamic_count': len(score_data.dynamics),
            # Include first and last few notes to capture content
            'sample_notes': [asdict(n) for n in (score_data.notes[:2] + score_data.notes[-2:] if len(score_data.notes) >= 4 else score_data.notes)]
        }
        
        # Combine with analysis type and parameters
        hash_data = {
            'score': score_hash_data,
            'analysis_type': analysis_type,
            'params': params
        }
        
        # Generate hash
        hash_str = hashlib.md5(json.dumps(hash_data, sort_keys=True).encode()).hexdigest()
        return f"{analysis_type}_{hash_str}"
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached analysis result."""
        cache_path = os.path.join(self.cache_dir, f"{key}.pkl")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                logger.info(f"Cache hit for {key}")
                return data
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        return None
    
    def store(self, key: str, data: Any) -> None:
        """Store analysis result in cache."""
        cache_path = os.path.join(self.cache_dir, f"{key}.pkl")
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            logger.info(f"Stored result in cache as {key}")
        except Exception as e:
            logger.warning(f"Failed to store in cache: {e}")


# Create a singleton cache instance
_cache = AnalysisCache()

def cached_analysis(analysis_type: str):
    """
    Decorator for caching analysis functions.
    
    Example usage:
    
    @cached_analysis("density")
    def analyze_density(score_data, interval=10.0, **kwargs):
        # Analysis implementation...
        return result
    """
    def decorator(func):
        @wraps(func)
        def wrapper(score_data, *args, **kwargs):
            # Generate cache key from score data and parameters
            params = {**kwargs}
            if args:
                params['_args'] = args
            
            key = _cache.get_cache_key(score_data, analysis_type, params)
            
            # Check cache
            cached_result = _cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # Run analysis
            result = func(score_data, *args, **kwargs)
            
            # Store in cache
            _cache.store(key, result)
            
            return result
        return wrapper
    return decorator
