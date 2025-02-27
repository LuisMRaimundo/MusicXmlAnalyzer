# modules/__init__.py

"""
Music XML Analysis Package
A comprehensive tool for analyzing and visualizing musical scores in MusicXML format.
"""

from .dynamics import analyze_dynamics, visualize_dynamics
from .density import analyze_density, visualize_density
from .spectrum import analyze_spectrum  # note: no visualize_spectrum

__all__ = [
    'analyze_dynamics',
    'visualize_dynamics',
    'analyze_density',
    'visualize_density',
    'analyze_spectrum'
    # removed 'visualize_spectrum'
]
