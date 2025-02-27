# modules/dynamics.py

"""
Enhanced Dynamic Analysis Module
"""

import numpy as np
from scipy import signal, stats
import matplotlib.pyplot as plt
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from music21 import dynamics, expressions, note, chord

from musicxml_analyzer.config import (
    STEVENS_COEFFICIENT,
    STEVENS_COEFFICIENTS,
    TEMPORAL_INTEGRATION_WINDOW,
    ONSET_THRESHOLDS,
    DYNAMICS_MAP,
    VISUALIZATION
)

logger = logging.getLogger(__name__)

def validate_score(score):
    """Validate score structure before analysis."""
    if not score:
        raise ValueError("Score is None")
        
    if not hasattr(score, 'parts'):
        raise ValueError("Score does not have parts attribute")
        
    valid_parts = 0
    for part in score.parts:
        if hasattr(part, 'flat'):
            valid_parts += 1
            
    if valid_parts == 0:
        raise ValueError("No valid parts found in score")
        
    return True

@dataclass
class DynamicEvent:
    """Represents a single dynamic event with perceptual properties."""
    time: float
    value: str
    intensity: float
    duration: Optional[float]
    type: str  # 'instant', 'gradual_start', 'gradual_end'
    context: Dict
    part: str

class EnhancedDynamicsAnalyzer:
    def __init__(self):
        """Initialize the enhanced dynamics analyzer with psychoacoustic parameters."""
        self.stevens_coef = STEVENS_COEFFICIENTS['intensity']
        self.temporal_window = TEMPORAL_INTEGRATION_WINDOW
        self.onset_thresholds = ONSET_THRESHOLDS
        self.dynamics_map = DYNAMICS_MAP

    def calculate_perceived_intensity(self, 
                                   base_intensity: float,
                                   context: Dict) -> float:
        """Calculate perceived intensity using Stevens' Power Law with context."""
        stevens_intensity = np.power(base_intensity/100, self.stevens_coef) * 100
        
        if context.get('temporal_density', 0) > 1/self.temporal_window:
            stevens_intensity *= 0.9  # Reduce perceived intensity in dense passages
            
        if context.get('masked', False):
            stevens_intensity *= 0.8
            
        return stevens_intensity

    def analyze_dynamics(self, score) -> List[DynamicEvent]:
        """
        Extract and analyze dynamics with enhanced perception modeling.
        Works with both music21 Score objects and ScoreData objects.
    
        Args:
            score: Either a music21 Score object or a ScoreData object
        
        Returns:
            List[DynamicEvent]: List of analyzed dynamic events
        """
        dynamic_events = []
    
        try:
            # Check if we have a ScoreData object
            if hasattr(score, 'dynamics') and isinstance(score.dynamics, list):
                # Already processed ScoreData, just return its dynamics
                return score.dynamics
            
            # Otherwise, process as music21 Score
            if not hasattr(score, 'parts'):
                raise ValueError("Score does not have parts attribute")
            
            for part_idx, part in enumerate(score.parts):
                # Skip if not a proper part object
                if not hasattr(part, 'flat'):
                    logger.warning(f"Skipping invalid part: {part}")
                    continue
            
                # Safely get part name with type checking
                if hasattr(part, 'partName') and part.partName:
                    part_name = part.partName
                else:
                    # Use enumeration to avoid .index() on potential set
                    part_name = f"Part {part_idx + 1}"
            
                # Track current dynamic for this part
                current_dynamic = None
            
                # Now safe to access .flat
                for element in part.flat:
                    if isinstance(element, (dynamics.Dynamic, expressions.TextExpression)):
                        time = float(element.offset)  # Convert to float explicitly
                    
                        # Extract dynamic value and type
                        if isinstance(element, dynamics.Dynamic):
                            value = element.value
                            type_str = 'instant'
                        else:
                            # Handle text expressions
                            if not hasattr(element, 'content'):
                                continue
                            
                            content = element.content.lower()
                            # Basic dynamic marking detection
                            value = content.strip()
                            type_str = 'text'
                    
                        # Handle gradual dynamics (crescendo, diminuendo)
                        if 'cresc' in value or 'dim' in value:
                            type_str = 'gradual'
                    
                        # Clean up the value
                        value = value.strip().lower().replace('-', '')
                    
                        # Only process if we recognize this dynamic marking
                        if value in self.dynamics_map:
                            # Calculate context
                            context = {
                                'temporal_density': len([
                                    e for e in dynamic_events
                                    if abs(e.time - time) < self.temporal_window
                                ]) / self.temporal_window if self.temporal_window > 0 else 0,
                                'previous_dynamic': current_dynamic
                            }
                        
                            # Get base intensity from the dynamics map
                            base_intensity = self.dynamics_map[value]['value']
                        
                            # Calculate perceived intensity
                            perceived_intensity = self.calculate_perceived_intensity(
                                base_intensity, context
                            )
                        
                            # Create dynamic event
                            event = DynamicEvent(
                                time=time,
                                value=value,
                                intensity=perceived_intensity,
                                duration=None,
                                type=type_str,
                                context=context,
                                part=part_name
                            )
                            dynamic_events.append(event)
                            current_dynamic = value  # Update the current dynamic
    
        except Exception as e:
            logger.error(f"Error in analyze_dynamics: {str(e)}")
            raise AnalysisError(f"Dynamic analysis failed: {str(e)}", e)
        
        # Sort events by time
        dynamic_events.sort(key=lambda x: x.time)
        return dynamic_events

    def visualize_dynamics(self, events: List[DynamicEvent], show_contexts: bool = False):
        """Generate enhanced visualization of dynamics analysis."""
        if not events:
            logger.warning("No dynamics events to visualize")
            return
            
        try:
            # Setup plot
            plt.figure(figsize=(12, 6))
            
            # Plot dynamics per part
            parts = sorted(set(e.part for e in events))
            colors = plt.cm.tab10(np.linspace(0, 1, len(parts)))
            
            for part, color in zip(parts, colors):
                part_events = [e for e in events if e.part == part]
                times = [e.time for e in part_events]
                intensities = [e.intensity for e in part_events]
                
                plt.plot(times, intensities, 'o-', 
                        color=color, 
                        label=part,
                        alpha=0.7)
            
            # Configure plot
            plt.grid(True, alpha=0.3)
            plt.xlabel('Time (beats)')
            plt.ylabel('Dynamic Level')
            plt.title('Dynamic Analysis')
            
            # Add dynamic markings on y-axis
            levels = sorted(set(self.dynamics_map.keys()))
            plt.yticks(
                [self.dynamics_map[d]['value'] for d in levels],
                levels
            )
            
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            logger.error(f"Error in visualize_dynamics: {str(e)}")
            raise

# Initialize analyzer
_analyzer = EnhancedDynamicsAnalyzer()

def analyze_dynamics(score) -> List[DynamicEvent]:
    """Public function to perform dynamics analysis."""
    return _analyzer.analyze_dynamics(score)

def visualize_dynamics(events: List[DynamicEvent], show_contexts: bool = False):
    """Public function to visualize dynamics analysis."""
    _analyzer.visualize_dynamics(events, show_contexts)

# Export public interface
__all__ = ['analyze_dynamics', 'visualize_dynamics', 'DynamicEvent']