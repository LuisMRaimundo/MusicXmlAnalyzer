# musicxml_analyzer/__init__.py

"""
MusicXML Analysis Package
"""

from .modules.dynamics import analyze_dynamics
from .modules.density import analyze_density 
from .modules.spectrum import analyze_spectrum
from .visualization.plotters import plot_dynamics, plot_density, plot_spectrum

__version__ = '1.1.0'

# Export all public functions
__all__ = [
    'analyze_dynamics',
    'analyze_density',
    'analyze_spectrum',
    'plot_dynamics',
    'plot_density',
    'plot_spectrum',
]