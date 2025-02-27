# MusicXML Analyzer

This package is licensed under the **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License**.
To view the full license, visit: [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/)

---

A comprehensive tool for analyzing and visualizing musical scores in **MusicXML** format, focusing on **dynamics, note density, and spectral analysis**.

## **Features**

- **Dynamics Analysis**: Visualize and analyze dynamic markings (`p`, `f`, `mf`, etc.) throughout the score.
- **Density Analysis**: Calculate and present note density over time.
- **Spectral Analysis**: Provide **Piano Roll** and **Heat Map** visualizations of pitch distribution.
- **Modern Graphical Interface**: Intuitive and responsive interface with customizable themes.
- **Result Export**: Export visualizations in **PNG, PDF, and SVG** formats.

## **Installation**

### **Prerequisites**

- Python 3.8 or higher
- Dependencies listed in `requirements.txt`

```md
# MusicXML Analyzer

## Installation

### **Via pip**
```bash
pip install musicxml-analyzer
```

### **Manual Installation**

#### **Clone the repository:**
```bash
git clone https://github.com/your-username/musicxml-analyzer.git
cd musicxml-analyzer
```

#### **Install dependencies:**
```bash
pip install -r requirements.txt
```

#### **Install the package in development mode:**
```bash
pip install -e .
```

## Usage

### **Graphical Interface**
To start the graphical interface:
```bash
musicxml-gui
```
Or:
```bash
python -m musicxml_analyzer.gui.modern_gui
```

### **Command Line**
For command line analysis:
```bash
musicxml-analyzer path/to/file.xml
```

#### **Additional options:**
```bash
--no-dynamics       # Disable dynamics analysis
--no-density        # Disable density analysis
--no-spectral       # Disable spectral analysis
--interval N        # Set density analysis interval (centiseconds)
--save-path PATH    # Path to save results
```

### **Library Usage**
```python
from musicxml_analyzer.main import process_musicxml

# Analyze a MusicXML file
results = process_musicxml('path/to/file.xml')

# Access results
dynamics_data = results['dynamics']
density_data = results['density']
spectrum_data = results['spectrum']

# Access generated figures
figures = results['figures']
```

## Project Structure
```
musicxml_analyzer/
├── core/               # Core system components
│   ├── cache.py        # Caching system for heavy analyses
│   ├── exceptions.py   # Custom exception handling
│   └── model.py        # Unified data model
├── gui/                # Graphical user interface
│   └── modern_gui.py   # Main interface
├── modules/            # Analysis modules
│   ├── dynamics.py     # Dynamics analysis
│   ├── density.py      # Density analysis
│   └── spectrum.py     # Spectral analysis
├── visualization/      # Visualization components
│   ├── export.py       # Results export
│   └── plotters.py     # Plotting functions
├── __init__.py
├── config.py           # Global settings
└── main.py             # Main entry point
```

## Contributing
Contributions are welcome! Please follow these steps:

1. **Fork the repository.**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Commit your changes:**
   ```bash
   git commit -m "Adding AmazingFeature"
   ```
4. **Push to the branch:**
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **Open a Pull Request.**

## Acknowledgments
This software was developed by **Luís Raimundo**, as part of a broader study on Music Analysis.

🔗 **DOI: [10.54499/2020.08817.BD 8D](https://doi.org/10.54499/2020.08817.BD)**

### **Funded by:**
- **Foundation for Science and Technology (FCT) - Portugal**

### **Supported by:**
- **Universidade NOVA de Lisboa**
- **Centre for the Study of Sociology and Musical Aesthetics (CESEM)**
- **Contemporary Music Group Investigation (GIMC)**
- **In2Past**

---

## Other Acknowledgements
- **music21** - Toolkit for computational music analysis.
- **matplotlib** - Used for visualizations.
- **All contributors** and testers who helped make this project possible.

---

## Contact
If you have any questions or suggestions, please open an issue on the GitHub repository or contact the maintainer.

**Luís Miguel da Luz Raimundo**  
**ORCID Profile:** [https://orcid.org/0000-0003-1712-6358](https://orcid.org/0000-0003-1712-6358)

### **Email Addresses:**
- lmr.2020@outlook.pt
- luisraimundo@fcsh.unl.pt

---

## License

This package is licensed under the **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License**.  
To view the full license, visit: [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/)

---

## **You are free to:**
✅ **Share** - Copy and redistribute the material in any medium, mode, or format for **non-commercial purposes**.

The licensor **cannot revoke these freedoms** as long as you follow the license terms.

---

## **Under the following conditions:**
- **Attribution**:  
  - You must **give appropriate credit**, provide a **link to the license**, and indicate if changes were made.
  - You may do so in any **reasonable manner**, but **not in a way that suggests the licensor endorses you or your use**.

- **NonCommercial**:  
  - 🚫 **You may not use the material for commercial purposes**.

- **NoDerivatives**:  
  - 🚫 **If you remix, transform, or build upon the material, you may not distribute the modified material**.

---

## **Disclaimer**
🚨 **No warranties are given**.  
You **may not** use this material for **commercial purposes** or **create derivatives** of it.
```



## **Disclaimer**
🚨 **No warranties are given**.  
You **may not** use this material for **commercial purposes** or **create derivatives** of it.

