# config.py

"""
Enhanced MusicXML Analysis Configuration
All constants synchronized across all modules
"""

# Basic Parameters (for backward compatibility)
STEVENS_COEFFICIENT = 0.67
ONSET_THRESHOLD = 0.1
REGISTER_WEIGHT_FACTOR = 0.1
METRIC_PRIMARY_WEIGHT = 1.0
METRIC_SECONDARY_WEIGHT = 0.8
DEFAULT_DENSITY_INTERVAL = 10

# Enhanced Psychoacoustic Parameters
STEVENS_COEFFICIENTS = {
    'intensity': 0.67,
    'duration': 1.1,
    'pitch': 0.6
}

# Register Analysis
REGISTER_WEIGHTS = {
    'weight_function': 'gaussian',
    'center': 65,
    'sigma': 12,
    'decay_rate': 0.1
}

# Metric Analysis
METRIC_WEIGHTS = {
    'primary': 1.0,
    'secondary': 0.8,
    'tertiary': 0.6,
    'weak': 0.4
}

# Temporal Analysis
TEMPORAL_INTEGRATION_WINDOW = 0.1
ONSET_THRESHOLDS = {
    'minimum': 0.05,
    'fusion': 0.1,
    'masking': 0.15
}

# Pitch Settings
PITCH_REFERENCE = {
    'frequency': 440,
    'midi': 69,
    'optimal_range': (60, 72)
}

# Texture Analysis
TEXTURE_ANALYSIS = {
    'polyphony_threshold': 0.7,
    'voice_leading_weight': 0.8,
    'maximum_voices': 8,
    'minimum_duration': 0.1
}

# Validation Parameters
VALIDATION = {
    'confidence_threshold': 0.95,
    'minimum_sample_size': 30,
    'outlier_threshold': 2.0,
    'cross_validation_folds': 5
}

# Enhanced Dynamics Mapping
DYNAMICS_MAP = {
    'pppp': {'value': 20, 'onset_weight': 0.4},
    'ppp': {'value': 30, 'onset_weight': 0.5},
    'pp': {'value': 40, 'onset_weight': 0.6},
    'p': {'value': 50, 'onset_weight': 0.7},
    'mp': {'value': 60, 'onset_weight': 0.8},
    'mf': {'value': 70, 'onset_weight': 0.9},
    'f': {'value': 80, 'onset_weight': 1.0},
    'ff': {'value': 90, 'onset_weight': 1.1},
    'fff': {'value': 100, 'onset_weight': 1.2},
    'ffff': {'value': 110, 'onset_weight': 1.3},
    'sf': {'value': 85, 'onset_weight': 1.15},
    'sff': {'value': 95, 'onset_weight': 1.25},
    'sfff': {'value': 105, 'onset_weight': 1.35},
    'sffff': {'value': 115, 'onset_weight': 1.45}
}

# Visualization Settings
VISUALIZATION = {
    'density': {
        'figsize': (12, 8),
        'colormap': 'viridis',
        'alpha_range': (0.3, 0.8),
        'dpi': 300
    },
    'spectrum': {
        'colormap': 'magma',
        'contour_levels': 20,
        'frequency_scaling': 'mel',
        'normalization': 'peak'
    }
}

# Plot Styles (for backward compatibility)
PLOT_STYLES = {
    'density': {
        'figsize': (16, 9),
        'colors': ['#6a040f', '#fb8500'],
        'alpha': 0.3,
    },
    'spectrum': {
        'figsize': (15, 12),
        'cmap': 'YlOrRd',
        'alpha': 0.6,
    }
}
