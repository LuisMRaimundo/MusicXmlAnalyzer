# musicxml_analyzer/main.py

"""
Módulo principal do MusicXML Analyzer com API unificada e melhorias na visualização.
"""

import os
import logging
from typing import Dict, Optional, Union, List
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

# Importações com caminhos completos
from music21 import converter, environment
from musicxml_analyzer.core.model import ScoreData, ScoreParser
from musicxml_analyzer.core.exceptions import MusicXMLAnalysisError, handle_exceptions, AnalysisError

# Módulos de análise
from musicxml_analyzer.modules.dynamics import analyze_dynamics
from musicxml_analyzer.modules.density import analyze_density
from musicxml_analyzer.modules.spectrum import analyze_spectrum

# Funções de plotagem separadas
from musicxml_analyzer.visualization.plotters import (
    plot_dynamics, 
    plot_density, 
    plot_spectrum, 
    plot_combined_dynamics
)

from musicxml_analyzer.config import DEFAULT_DENSITY_INTERVAL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def configure_music21():
    """Configure music21 environment settings."""
    env = environment.Environment()
    env['warnings'] = 0


@handle_exceptions(AnalysisError, "Erro ao processar o arquivo MusicXML")
def process_musicxml(file_path: str, params: Optional[Dict] = None) -> Dict[str, Union[ScoreData, List, Figure]]:
    """
    Processa um arquivo MusicXML com análise completa e retorna os resultados.
    
    Args:
        file_path: Caminho para o arquivo MusicXML
        params: Parâmetros de configuração para análise
        
    Returns:
        Um dicionário contendo os resultados de todas as análises ativadas
    """
    if params is None:
        params = {}
    
    # Parâmetros padrão
    density_interval = params.get('density_interval', DEFAULT_DENSITY_INTERVAL)
    enable_dynamics = params.get('enable_dynamics', True)
    enable_density = params.get('enable_density', True)
    enable_spectral = params.get('enable_spectral', True)
    enable_combined_dynamics = params.get('enable_combined_dynamics', True)
    show_plots = params.get('show_plots', True)
    
    results = {}
    
    # Parse o score
    logger.info(f"Parsing score: {file_path}")
    
    # Primeiro, parse com music21
    music21_score = converter.parse(file_path)
    
    # Converte para nosso modelo de dados unificado
    score_data = ScoreParser.parse(music21_score)
    results['score_data'] = score_data
    
    # Figuras para cada análise
    figures = {}
    
    # Análise de dinâmicas
    if enable_dynamics:
        logger.info("Analisando dinâmicas")
        dynamics_results = analyze_dynamics(score_data)
        results['dynamics'] = dynamics_results
        
        if show_plots:
            fig_dynamics = Figure(figsize=(10, 6))
            ax = fig_dynamics.add_subplot(111)
            plot_dynamics(ax, dynamics_results, show_parts=True, show_gradual=True)
            figures['dynamics'] = fig_dynamics
            
            # Analyze combined dynamics if enabled
            if enable_combined_dynamics:
                fig_combined = Figure(figsize=(10, 6))
                ax_combined = fig_combined.add_subplot(111)
                plot_combined_dynamics(ax_combined, dynamics_results)
                figures['combined_dynamics'] = fig_combined
    
    # Análise de densidade
    if enable_density:
        logger.info("Analisando densidade")
        
        # Extrair informações de notas adequadamente do ScoreData
        notes_list = [(note.start_time, note.duration, note.pitch) for note in score_data.notes]
        
        # Realizar análise
        density_results = analyze_density(notes_list, density_interval=density_interval)
        results['density'] = density_results
        
        if show_plots:
            fig_density = Figure(figsize=(10, 6))
            ax = fig_density.add_subplot(111)
            plot_density(ax, density_results, show_register=True)
            figures['density'] = fig_density
    
    # Análise espectral
    if enable_spectral:
        logger.info("Analisando conteúdo espectral")
        spectral_results = analyze_spectrum(score_data)
        results['spectrum'] = spectral_results
        
        if show_plots:
            # Piano roll melhorado
            fig_piano_roll = Figure(figsize=(12, 8))
            ax_piano = fig_piano_roll.add_subplot(111)
            plot_spectrum(ax_piano, spectral_results, mode="piano_roll")
            figures['spectrum_piano_roll'] = fig_piano_roll
            
            # Heatmap melhorado
            fig_heatmap = Figure(figsize=(12, 8))
            ax_heatmap = fig_heatmap.add_subplot(111)
            plot_spectrum(ax_heatmap, spectral_results, mode="heatmap")
            figures['spectrum_heatmap'] = fig_heatmap
    
    # Adicionar as figuras ao resultado
    results['figures'] = figures
    
    logger.info("Análise concluída com sucesso")
    return results


def main():
    """Interface de linha de comando para o analisador."""
    configure_music21()
    
    import argparse
    parser = argparse.ArgumentParser(description='Analisar arquivos MusicXML')
    parser.add_argument('file', help='Caminho para o arquivo MusicXML')
    parser.add_argument('--no-dynamics', action='store_true',
                        help='Desativar análise de dinâmica')
    parser.add_argument('--no-density', action='store_true',
                        help='Desativar análise de densidade')
    parser.add_argument('--no-spectral', action='store_true',
                        help='Desativar análise espectral')
    parser.add_argument('--no-combined-dynamics', action='store_true',
                        help='Desativar análise de dinâmica combinada')
    parser.add_argument('--interval', type=float, default=DEFAULT_DENSITY_INTERVAL,
                        help='Intervalo de cálculo de densidade (centisegundos)')
    parser.add_argument('--save-path', type=str, default=None,
                        help='Caminho para salvar os resultados')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        logger.error("Arquivo não encontrado")
        return
        
    params = {
        'density_interval': args.interval,
        'enable_dynamics': not args.no_dynamics,
        'enable_density': not args.no_density,
        'enable_spectral': not args.no_spectral,
        'enable_combined_dynamics': not args.no_combined_dynamics,
        'show_plots': True
    }
    
    try:
        results = process_musicxml(args.file, params)
        
        # Mostrar gráficos
        for name, fig in results['figures'].items():
            fig.tight_layout()
            plt.figure(fig.number)
            plt.show()
            
        # Salvar resultados se especificado
        if args.save_path:
            save_path = args.save_path
            os.makedirs(save_path, exist_ok=True)
            
            for name, fig in results['figures'].items():
                fig.savefig(os.path.join(save_path, f"{name}.png"), dpi=300)
            
            logger.info(f"Resultados salvos em {save_path}")
            
    except Exception as e:
        logger.error(f"Falha na análise: {e}")


if __name__ == "__main__":
    main()
