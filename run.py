import sys
import os

# Add the current directory to Python's path
sys.path.insert(0, os.path.abspath('.'))

# Import and run the main function
from musicxml_analyzer.main import main

if __name__ == "__main__":
    main()
