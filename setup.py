from setuptools import setup, find_packages

setup(
    name="musicxml_analyzer",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "music21",
        "numpy",
        "scipy",
        "matplotlib",
        "pandas",
    ],
    entry_points={
        'console_scripts': [
            'musicxml-analyzer=musicxml_analyzer.main:main',
            'musicxml-gui=musicxml_analyzer.gui.modern_gui:main',
        ],
    }
)