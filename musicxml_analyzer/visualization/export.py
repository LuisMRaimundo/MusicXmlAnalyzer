# visualization/export.py

"""
Export capabilities for analysis results and visualizations.
"""

import os
import json
from typing import Dict, List, Optional, Union, Any
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import xml.etree.ElementTree as ET
import csv

logger = logging.getLogger(__name__)

class AnalysisExporter:
    """Handles exporting of analysis results in various formats."""
    
    SUPPORTED_FORMATS = {
        "image": [".png", ".jpg", ".svg", ".pdf"],
        "data": [".csv", ".json", ".xml", ".xlsx"],
        "report": [".html", ".md"]
    }
    
    def __init__(self):
        pass
        
    @staticmethod
    def export_figure(fig: Figure, filename: str, dpi: int = 300) -> bool:
        """
        Export a matplotlib figure to an image file.
        
        Args:
            fig: The matplotlib figure to export
            filename: Target filename with extension
            dpi: Resolution for raster formats
            
        Returns:
            bool: Success status
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            # Save the figure
            fig.savefig(filename, dpi=dpi, bbox_inches='tight')
            
            logger.info(f"Exported figure to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export figure: {e}")
            return False
    
    @staticmethod
    def export_data(data: Union[Dict, List, pd.DataFrame], 
                   filename: str, 
                   format_hints: Optional[Dict] = None) -> bool:
        """
        Export analysis data to a file.
        
        Args:
            data: The data to export (dict, list, or DataFrame)
            filename: Target filename with extension
            format_hints: Optional formatting hints
            
        Returns:
            bool: Success status
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            # Get file extension
            _, ext = os.path.splitext(filename)
            ext = ext.lower()
            
            # Export based on format
            if ext == '.csv':
                return AnalysisExporter._export_csv(data, filename, format_hints)
            elif ext == '.json':
                return AnalysisExporter._export_json(data, filename, format_hints)
            elif ext == '.xml':
                return AnalysisExporter._export_xml(data, filename, format_hints)
            elif ext == '.xlsx':
                return AnalysisExporter._export_excel(data, filename, format_hints)
            else:
                logger.error(f"Unsupported export format: {ext}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return False
    
    @staticmethod
    def _export_csv(data: Union[Dict, List, pd.DataFrame], 
                   filename: str,
                   format_hints: Optional[Dict] = None) -> bool:
        """Export data as CSV."""
        # Convert to DataFrame if needed
        if isinstance(data, (dict, list)):
            df = pd.DataFrame(data)
        else:
            df = data
            
        # Apply format hints
        if format_hints:
            if format_hints.get('transpose', False):
                df = df.transpose()
                
        # Export
        df.to_csv(filename, index=format_hints.get('include_index', True))
        logger.info(f"Exported CSV to {filename}")
        return True
    
    @staticmethod
    def _export_json(data: Union[Dict, List, pd.DataFrame], 
                    filename: str,
                    format_hints: Optional[Dict] = None) -> bool:
        """Export data as JSON."""
        # Convert DataFrame to dict if needed
        if isinstance(data, pd.DataFrame):
            if format_hints and format_hints.get('orient'):
                orient = format_hints.get('orient')
            else:
                orient = 'records'
            export_data = data.to_dict(orient=orient)
        else:
            export_data = data
            
        # Use custom encoder for numpy types
        class NumpyEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return super(NumpyEncoder, self).default(obj)
        
        # Export with formatting
        indent = format_hints.get('indent', 2) if format_hints else 2
        with open(filename, 'w') as f:
            json.dump(export_data, f, cls=NumpyEncoder, indent=indent)
            
        logger.info(f"Exported JSON to {filename}")
        return True
    
    @staticmethod
    def _export_xml(data: Union[Dict, List, pd.DataFrame], 
                   filename: str,
                   format_hints: Optional[Dict] = None) -> bool:
        """Export data as XML."""
        
        def _dict_to_xml(parent, data):
            """Convert a dictionary to XML recursively."""
            if isinstance(data, dict):
                for key, value in data.items():
                    # Create a valid XML tag name (no spaces, special chars)
                    tag = ''.join(c for c in key if c.isalnum() or c == '_')
                    if not tag:
                        tag = "item"
                    
                    # Create element
                    element = ET.SubElement(parent, tag)
                    
                    # Process contents
                    if isinstance(value, (dict, list)):
                        _dict_to_xml(element, value)
                    else:
                        element.text = str(value)
            elif isinstance(data, list):
                for item in data:
                    item_elem = ET.SubElement(parent, "item")
                    _dict_to_xml(item_elem, item)
            else:
                parent.text = str(data)
        
        # Convert DataFrame to dict if needed
        if isinstance(data, pd.DataFrame):
            export_data = data.to_dict(orient='records')
        else:
            export_data = data
            
        # Create root
        root_name = format_hints.get('root_name', 'analysis_data') if format_hints else 'analysis_data'
        root = ET.Element(root_name)
        
        # Build XML
        _dict_to_xml(root, export_data)
        
        # Export
        tree = ET.ElementTree(root)
        tree.write(filename, encoding='utf-8', xml_declaration=True)
        
        logger.info(f"Exported XML to {filename}")
        return True
    
    @staticmethod
    def _export_excel(data: Union[Dict, List, pd.DataFrame], 
                     filename: str,
                     format_hints: Optional[Dict] = None) -> bool:
        """Export data as Excel file."""
        # Convert to DataFrame if needed
        if isinstance(data, (dict, list)):
            df = pd.DataFrame(data)
        else:
            df = data
            
        # Apply format hints
        if format_hints:
            if format_hints.get('transpose', False):
                df = df.transpose()
                
        # Set up Excel writer
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            sheet_name = format_hints.get('sheet_name', 'Analysis Results') if format_hints else 'Analysis Results'
            df.to_excel(writer, sheet_name=sheet_name, index=format_hints.get('include_index', True))
            
        logger.info(f"Exported Excel to {filename}")
        return True
    
    @staticmethod
    def export_html_report(title: str, 
                         sections: List[Dict[str, Any]], 
                         filename: str, 
                         include_css: bool = True) -> bool:
        """
        Export a full HTML report with multiple sections.
        
        Args:
            title: Report title
            sections: List of section dictionaries (with keys: 'title', 'content', 'figures')
            filename: Target filename
            include_css: Whether to include default CSS styling
            
        Returns:
            bool: Success status
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            # Basic CSS styling
            default_css = """
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }
            h1 { color: #2c3e50; border-bottom: 1px solid #ddd; padding-bottom: 10px; }
            h2 { color: #3498db; margin-top: 30px; }
            .section { margin-bottom: 30px; }
            .figure { margin: 20px 0; text-align: center; }
            .figure img { max-width: 100%; }
            .figure-caption { color: #666; font-style: italic; }
            table { border-collapse: collapse; width: 100%; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            """
            
            # Start HTML
            html = ['<!DOCTYPE html>',
                   '<html>',
                   '<head>',
                   f'<title>{title}</title>',
                   '<meta charset="UTF-8">']
            
            # Add CSS
            if include_css:
                html.append(f'<style>{default_css}</style>')
            
            # Add responsive meta tag
            html.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
            html.append('</head>')
            html.append('<body>')
            
            # Add report title
            html.append(f'<h1>{title}</h1>')
            
            # Add sections
            for section in sections:
                html.append(f'<div class="section">')
                html.append(f'<h2>{section["title"]}</h2>')
                
                # Add content
                if 'content' in section:
                    if isinstance(section['content'], str):
                        html.append(f'<p>{section["content"]}</p>')
                    elif isinstance(section['content'], list):
                        html.append('<ul>')
                        for item in section['content']:
                            html.append(f'<li>{item}</li>')
                        html.append('</ul>')
                    elif isinstance(section['content'], pd.DataFrame):
                        html.append(section['content'].to_html())
                
                # Add figures
                if 'figures' in section:
                    for i, fig in enumerate(section['figures']):
                        # Generate a filename for the figure
                        fig_filename = f"{os.path.splitext(filename)[0]}_fig_{i+1}.png"
                        
                        # Save the figure
                        fig.savefig(fig_filename, dpi=300, bbox_inches='tight')
                        
                        # Get just the basename for the HTML
                        fig_basename = os.path.basename(fig_filename)
                        
                        # Add to HTML
                        html.append('<div class="figure">')
                        html.append(f'<img src="{fig_basename}" alt="Figure {i+1}">')
                        if 'caption' in section and i < len(section['caption']):
                            html.append(f'<div class="figure-caption">{section["caption"][i]}</div>')
                        html.append('</div>')
                
                html.append('</div>')
            
            # Close HTML
            html.append('</body>')
            html.append('</html>')
            
            # Write to file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(html))
                
            logger.info(f"Exported HTML report to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export HTML report: {e}")
            return False
    
    @staticmethod
    def export_markdown_report(title: str, 
                             sections: List[Dict[str, Any]], 
                             filename: str) -> bool:
        """
        Export a Markdown report with multiple sections.
        
        Args:
            title: Report title
            sections: List of section dictionaries (with keys: 'title', 'content', 'figures')
            filename: Target filename
            
        Returns:
            bool: Success status
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            # Start Markdown
            md = [f'# {title}\n']
            
            # Add sections
            for section in sections:
                md.append(f'## {section["title"]}')
                
                # Add content
                if 'content' in section:
                    if isinstance(section['content'], str):
                        md.append(f'\n{section["content"]}\n')
                    elif isinstance(section['content'], list):
                        for item in section['content']:
                            md.append(f'- {item}')
                        md.append('')
                    elif isinstance(section['content'], pd.DataFrame):
                        df = section['content']
                        # Create table header
                        header = '| ' + ' | '.join(str(col) for col in df.columns) + ' |'
                        separator = '| ' + ' | '.join(['---'] * len(df.columns)) + ' |'
                        md.append(header)
                        md.append(separator)
                        
                        # Add rows
                        for _, row in df.iterrows():
                            md.append('| ' + ' | '.join(str(cell) for cell in row) + ' |')
                        md.append('')
                
                # Add figures
                if 'figures' in section:
                    for i, fig in enumerate(section['figures']):
                        # Generate a filename for the figure
                        fig_filename = f"{os.path.splitext(filename)[0]}_fig_{i+1}.png"
                        
                        # Save the figure
                        fig.savefig(fig_filename, dpi=300, bbox_inches='tight')
                        
                        # Get just the basename for the Markdown
                        fig_basename = os.path.basename(fig_filename)
                        
                        # Add to Markdown with caption if available
                        if 'caption' in section and i < len(section['caption']):
                            md.append(f'![{section["caption"][i]}]({fig_basename})')
                        else:
                            md.append(f'![Figure {i+1}]({fig_basename})')
                        md.append('')
            
            # Write to file
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(md))
                
            logger.info(f"Exported Markdown report to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export Markdown report: {e}")
            return False


# Export public interface
__all__ = ['AnalysisExporter']