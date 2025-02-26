# core/model.py

"""
Centralized data model for MusicXML analysis.
Provides efficient access to score data for all analysis modules.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from music21 import stream, note, chord, dynamics

@dataclass
class NoteEvent:
    """Unified representation of a note event."""
    start_time: float
    duration: float
    end_time: float
    pitch: int
    pitch_name: str
    velocity: float
    part: str
    measure: int
    beat: float
    voice: Optional[int] = None
    dynamic: Optional[str] = None
    articulation: Optional[str] = None

@dataclass
class DynamicEvent:
    """Representation of a dynamic marking."""
    time: float
    value: str
    intensity: float
    type: str  # 'instant', 'gradual_start', 'gradual_end'
    part: str
    measure: int
    duration: Optional[float] = None
    
@dataclass
class ScoreData:
    """Central data structure containing all extracted score information."""
    # Basic metadata
    title: str = ""
    composer: str = ""
    time_signature: str = "4/4"
    key_signature: str = "C"
    tempo: float = 120.0
    
    # Extracted events
    notes: List[NoteEvent] = field(default_factory=list)
    dynamics: List[DynamicEvent] = field(default_factory=list)
    
    # Cached calculations
    _time_range: Optional[Tuple[float, float]] = None
    _pitch_range: Optional[Tuple[int, int]] = None
    _parts: Optional[Set[str]] = None
    
    @property
    def time_range(self) -> Tuple[float, float]:
        """Get the time range of the score."""
        if self._time_range is None:
            if not self.notes:
                return (0.0, 0.0)
            min_time = min(n.start_time for n in self.notes)
            max_time = max(n.end_time for n in self.notes)
            self._time_range = (min_time, max_time)
        return self._time_range
    
    @property
    def pitch_range(self) -> Tuple[int, int]:
        """Get the pitch range of the score."""
        if self._pitch_range is None:
            if not self.notes:
                return (60, 72)  # Default middle C to C5
            min_pitch = min(n.pitch for n in self.notes)
            max_pitch = max(n.pitch for n in self.notes)
            self._pitch_range = (min_pitch, max_pitch)
        return self._pitch_range
    
    @property
    def parts(self) -> Set[str]:
        """Get the set of parts in the score."""
        if self._parts is None:
            self._parts = set(n.part for n in self.notes)
        return self._parts
    
    def get_notes_in_time_range(self, start: float, end: float) -> List[NoteEvent]:
        """Get all notes that sound within the given time range."""
        return [n for n in self.notes 
                if (start <= n.start_time < end) or  # Note starts in range
                   (n.start_time <= start < n.end_time)]  # Note is already sounding
    
    def get_dynamics_in_time_range(self, start: float, end: float) -> List[DynamicEvent]:
        """Get all dynamic events within the given time range."""
        return [d for d in self.dynamics if start <= d.time < end]
    
    def get_notes_by_part(self, part: str) -> List[NoteEvent]:
        """Get all notes for a specific part."""
        return [n for n in self.notes if n.part == part]
    
    def get_active_dynamics(self, time: float, part: str) -> Optional[DynamicEvent]:
        """Get the active dynamic marking at a given time for a part."""
        # Find the most recent dynamic marking before the given time
        relevant_dynamics = [d for d in self.dynamics 
                             if d.part == part and d.time <= time]
        if not relevant_dynamics:
            return None
        return max(relevant_dynamics, key=lambda d: d.time)


class ScoreParser:
    """Parser to extract a complete ScoreData object from a music21 score."""
    
    @staticmethod
    def parse(score: stream.Score) -> ScoreData:
        """Parse a music21 score into our centralized data model."""
        score_data = ScoreData()
        
        # Extract metadata
        if score.metadata:
            score_data.title = score.metadata.title or ""
            score_data.composer = score.metadata.composer or ""
        
        # Extract time signature
        from music21 import meter
        for ts in score.flat.getElementsByClass(meter.TimeSignature):
            score_data.time_signature = f"{ts.numerator}/{ts.denominator}"
            break
            
        # Extract key signature
        from music21 import key
        for ks in score.flat.getElementsByClass(key.KeySignature):
            score_data.key_signature = ks.asKey().name
            break
            
        # Extract tempo
        from music21 import tempo
        for mm in score.flat.getElementsByClass(tempo.MetronomeMark):
            score_data.tempo = mm.number
            break
            
        # Extract notes and dynamics from each part
        for part_idx, part in enumerate(score.parts):
            # Safely get part name with type checking
            if hasattr(part, 'partName') and part.partName:
                part_name = part.partName
            else:
                part_name = f"Part {part_idx + 1}"
            
            # Track current dynamic for this part
            current_dynamic = None
            
            # Extract all objects in part
            for element in part.flat:
                # Extract dynamic markings
                if isinstance(element, dynamics.Dynamic):
                    event = DynamicEvent(
                        time=float(element.offset),
                        value=element.value,
                        intensity=float(ScoreParser._get_dynamic_intensity(element.value)),
                        type='instant',
                        part=part_name,
                        measure=element.measureNumber
                    )
                    score_data.dynamics.append(event)
                    current_dynamic = element.value
                
                # Extract notes
                elif isinstance(element, note.Note):
                    if not hasattr(element, 'pitch'):
                        continue  # Skip rests or unpitched elements
                        
                    start_time = float(element.offset)
                    duration = float(element.duration.quarterLength)
                    
                    event = NoteEvent(
                        start_time=start_time,
                        duration=duration,
                        end_time=start_time + duration,
                        pitch=element.pitch.midi,
                        pitch_name=element.pitch.nameWithOctave,
                        velocity=ScoreParser._get_note_velocity(element),
                        part=part_name,
                        measure=element.measureNumber,
                        beat=element.beat,
                        voice=getattr(element, 'voice', None),  # Try to get element.voice directly
                        dynamic=current_dynamic
                    )
                    score_data.notes.append(event)
                
                # Extract chords (multiple notes)
                elif isinstance(element, chord.Chord):
                    start_time = float(element.offset)
                    duration = float(element.duration.quarterLength)
    
                    for pitch_obj in element.pitches:
                        event = NoteEvent(
                            start_time=start_time,
                            duration=duration,
                            end_time=start_time + duration,
                            pitch=pitch_obj.midi,
                            pitch_name=pitch_obj.nameWithOctave,
                            velocity=ScoreParser._get_note_velocity(element),
                            part=part_name,
                            measure=element.measureNumber,
                            beat=element.beat,
                            voice=getattr(element, 'voice', None),  # Using getattr for safe access
                            dynamic=current_dynamic
                        )
                        score_data.notes.append(event)
        
        # Sort events by time
        score_data.notes.sort(key=lambda x: (x.start_time, x.pitch))
        score_data.dynamics.sort(key=lambda x: x.time)
        
        return score_data
    
    @staticmethod
    def _get_note_velocity(note_obj) -> float:
        """Extract velocity from a note or chord object."""
        try:
            if hasattr(note_obj, 'volume') and note_obj.volume is not None:
                if hasattr(note_obj.volume, 'velocity') and note_obj.volume.velocity is not None:
                    return float(note_obj.volume.velocity) / 127.0
        except:
            pass
        return 0.8  # Default velocity
        
    @staticmethod
    def _get_dynamic_intensity(dynamic_value: str) -> float:
        """Convert dynamic marking to intensity value."""
        # Dynamic mapping (can be moved to config if needed)
        dynamics_map = {
            'pppp': 20, 'ppp': 30, 'pp': 40, 'p': 50,
            'mp': 60, 'mf': 70, 'f': 80, 'ff': 90,
            'fff': 100, 'ffff': 110
        }
        return dynamics_map.get(dynamic_value, 70)  # Default to mf