# modules/heatmap_spectrum.py

import numpy as np
from scipy import ndimage
import logging
from typing import Tuple
from matplotlib.colors import LinearSegmentedColormap
from music21 import note as m21note, chord, stream

logger = logging.getLogger(__name__)

def analyze_spectral_energy(score,
                            resolution: Tuple[int, int] = (100, 200),
                            smoothing: float = 1.5
                           ) -> Tuple[np.ndarray, Tuple[float, float], Tuple[float, float]]:
    """
    Analyze spectral energy distribution with enhanced resolution and smoothing,
    but do NOT plot anything. Returns the 2D array + time/pitch ranges.

    Args:
        score: A music21 Score or a ScoreData object with `notes`.
        resolution: (pitch_resolution, time_resolution)
        smoothing: Gaussian smoothing factor for energy map

    Returns:
        energy: 2D numpy array, shape = (pitch_res, time_res)
        (t_min, t_max): time range
        (p_min, p_max): pitch range
    """
    import math

    # 1) Gather note data from either ScoreData or music21 Score
    notes_data = []
    try:
        # If it's a ScoreData object with .notes
        if hasattr(score, 'notes') and isinstance(score.notes, list):
            for note_event in score.notes:
                if not all(hasattr(note_event, attr) for attr in ['start_time', 'duration', 'pitch', 'velocity']):
                    logger.warning("Skipping note with missing attributes.")
                    continue
                notes_data.append({
                    'start': float(note_event.start_time),
                    'duration': float(note_event.duration),
                    'pitch': int(note_event.pitch),
                    'velocity': float(note_event.velocity * 127.0),
                })

        # Else if it's a music21 Score
        elif hasattr(score, 'parts'):
            for part_idx, part in enumerate(score.parts):
                if not hasattr(part, 'flat'):
                    logger.warning(f"Skipping invalid part {part_idx}. No 'flat' attribute.")
                    continue
                for note_obj in part.flat.notes:
                    # Skip rests or unpitched
                    if not hasattr(note_obj, 'pitch') or note_obj.pitch is None:
                        continue

                    offset_val = float(getattr(note_obj, 'offset', 0.0))
                    dur_val    = float(getattr(note_obj.duration, 'quarterLength', 0.0))
                    midi_val   = getattr(note_obj.pitch, 'midi', None)
                    if midi_val is None:
                        continue

                    velocity_val = 64
                    if hasattr(note_obj, 'volume') and note_obj.volume and note_obj.volume.velocity is not None:
                        velocity_val = note_obj.volume.velocity

                    notes_data.append({
                        'start': offset_val,
                        'duration': dur_val,
                        'pitch': int(midi_val),
                        'velocity': int(velocity_val),
                    })

        else:
            raise ValueError("Invalid score object: must have 'notes' or 'parts'")

        # 2) Check if we have any notes
        if not notes_data:
            raise ValueError("No notes found in score")

        # 3) Determine time/pitch range
        min_time = min(n['start'] for n in notes_data)
        max_time = max(n['start'] + n['duration'] for n in notes_data)
        min_pitch = min(n['pitch'] for n in notes_data)
        max_pitch = max(n['pitch'] for n in notes_data)

        # 4) Add a bit of padding
        pitch_padding = (max_pitch - min_pitch) * 0.1
        time_padding  = (max_time - min_time) * 0.05

        min_pitch = max(0, min_pitch - pitch_padding)
        max_pitch = min(127, max_pitch + pitch_padding)
        min_time  = max(0, min_time - time_padding)
        max_time  = max_time + time_padding

        pitch_res, time_res = resolution
        energy = np.zeros((pitch_res, time_res), dtype=float)

        # 5) Build time edges
        time_edges = np.linspace(min_time, max_time, time_res)

        # 6) Fill energy array
        for n in notes_data:
            start_t    = n['start']
            end_t      = start_t + n['duration']
            intensity  = float(n['velocity']) / 127.0
            intensity  = max(0, min(intensity, 1))  # clamp to [0,1]

            # Time bins
            time_mask = (time_edges >= start_t) & (time_edges <= end_t)
            if not np.any(time_mask):
                continue

            # Pitch bin
            if max_pitch > min_pitch:
                pitch_idx = int((n['pitch'] - min_pitch) / (max_pitch - min_pitch) * (pitch_res - 1))
            else:
                pitch_idx = 0

            if 0 <= pitch_idx < pitch_res:
                energy[pitch_idx, time_mask] += intensity

        # 7) Optional smoothing
        if np.any(energy) and smoothing > 0:
            energy = ndimage.gaussian_filter(energy, sigma=(smoothing, smoothing))

        return energy, (min_time, max_time), (min_pitch, max_pitch)

    except Exception as e:
        logger.error(f"Error in analyze_spectral_energy: {e}")
        raise


def plot_spectral_heatmap_on_ax(ax,
                                score,
                                analyze_spectral_energy_func,
                                show_contour: bool = True):
    """
    Plot a spectral heatmap onto a given Matplotlib axis, using the output of
    `analyze_spectral_energy_func(score)`.

    Args:
        ax: A Matplotlib axes object
        score: A ScoreData or music21 Score
        analyze_spectral_energy_func: A reference to your function that returns (energy, (t_min, t_max), (p_min, p_max))
        show_contour: Whether to overlay contour lines
    """
    try:
        # 1) Compute energy
        energy, (t_min, t_max), (p_min, p_max) = analyze_spectral_energy_func(score)

        # 2) Colormap
        colors = [
            (1, 1, 1, 0),
            (0.8, 0.8, 1, 0.3),
            (0.5, 0.5, 1, 0.6),
            (1, 0.6, 0.6, 0.7),
            (1, 0.3, 0.3, 0.8),
            (0.8, 0, 0, 1),
        ]
        cmap = LinearSegmentedColormap.from_list("custom", colors, N=100)

        # 3) Plot on the axis
        im = ax.imshow(
            energy,
            origin='lower',
            aspect='auto',
            extent=[t_min, t_max, p_min, p_max],
            cmap=cmap
        )

        # 4) Y-axis pitch labels
        pitch_ticks = np.arange(int(p_min), int(p_max) + 1, 2)
        pitch_labels = []
        for val in pitch_ticks:
            try:
                pitch_labels.append(m21note.Note(midi=val).nameWithOctave)
            except:
                pitch_labels.append(str(val))

        ax.set_yticks(pitch_ticks)
        ax.set_yticklabels(pitch_labels)

        # 5) Contours
        if show_contour and energy.max() > 0:
            levels = np.linspace(energy.max() * 0.2, energy.max() * 0.8, 8)
            X = np.linspace(t_min, t_max, energy.shape[1])
            Y = np.linspace(p_min, p_max, energy.shape[0])
            ax.contour(X, Y, energy, levels=levels, colors='black', alpha=0.3)

        # 6) If it's music21 Score, draw measure lines
        if hasattr(score, 'parts'):
            for part in score.parts:
                measures = part.getElementsByClass('Measure')
                for m in measures:
                    if m.offset is not None:
                        ax.axvline(x=float(m.offset), color='gray', linestyle=':', alpha=0.3)

        ax.set_title("Spectral Energy Distribution")
        ax.set_xlabel("Time (beats)")
        ax.set_ylabel("Pitch")
        ax.grid(True, alpha=0.2)

        # 7) Colorbar
        fig = ax.figure
        fig.colorbar(im, ax=ax, label="Energy Intensity")

    except Exception as e:
        logger.error(f"Error in plot_spectral_heatmap_on_ax: {e}")
        raise

__all__ = [
    "analyze_spectral_energy",
    "plot_spectral_heatmap_on_ax"
]
