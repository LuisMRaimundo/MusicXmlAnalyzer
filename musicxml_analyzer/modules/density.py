# modules/density.py

"""
Módulo de Análise de Densidade Melhorado
Reescrito para retornar dados em um formato consistente e melhorar o desempenho.
"""

import numpy as np
from typing import List, Tuple, Optional, Union, Dict, Any
import logging
from dataclasses import dataclass

from musicxml_analyzer.core.exceptions import handle_exceptions, AnalysisError
from musicxml_analyzer.core.cache import cached_analysis
from musicxml_analyzer.config import DEFAULT_DENSITY_INTERVAL

logger = logging.getLogger(__name__)


@dataclass
class DensityEvent:
    """Representa uma única medição de densidade com contexto."""
    time: float
    note_count: int
    register_info: Optional[Dict[str, Any]] = None


@handle_exceptions(AnalysisError, "Erro na análise de densidade")
@cached_analysis("density")


def analyze_density(notes, density_interval=DEFAULT_DENSITY_INTERVAL):
    """
    Computa densidade de notas ao longo do tempo.

    Args:
        notes: Um objeto ScoreData ou uma lista de tuplas (start_time, duration, pitch).
        density_interval: Intervalo de tempo (em centisegundos) para agrupamento da densidade.
                         10.0 significa 10 centisegundos por bin.

    Returns:
        (time_array, density_array):
          - time_array: Array numpy 1D de pontos no tempo (em segundos).
          - density_array: Array numpy 1D de contagem de notas em cada intervalo de tempo.
    """
    # Verificar se temos um objeto ScoreData ou uma lista de tuplas
    if hasattr(notes, 'notes') and not isinstance(notes, list):
        # Converter ScoreData para lista de tuplas
        notes_data = [(n.start_time, n.duration, n.pitch) for n in notes.notes]
    else:
        notes_data = notes

    if not notes_data:
        logger.warning("Sem notas para analisar. Retornando arrays vazios.")
        return np.array([]), np.array([])

    try:
        # Validar formato das notas
        for i, note_tuple in enumerate(notes_data):
            if len(note_tuple) < 3:
                raise ValueError(f"Formato inválido de tupla na nota {i}, esperados 3 elementos: {note_tuple}")

        # 1) Encontrar tempo máximo das notas
        max_time = max(start + duration for start, duration, _pitch in notes_data)
        if max_time <= 0:
            logger.warning("Todas as notas têm tempo total zero ou negativo. Retornando arrays vazios.")
            return np.array([]), np.array([])

        # 2) Criar bins de tempo
        #    density_interval está em centisegundos => 1 segundo = 100 centisegundos
        #    então multiplique max_time por 100 / density_interval para obter o número de bins
        num_bins = int(np.ceil(max_time * 100.0 / density_interval))
        # Criar um array com espaçamento linear de 0 a max_time com num_bins pontos
        time_array = np.linspace(0.0, max_time, num_bins, endpoint=True)

        # 3) Criar um array de densidade inicializado com zero
        density_array = np.zeros(num_bins, dtype=float)

        # 4) Preencher o array de densidade
        for (start, duration, _pitch) in notes_data:
            note_end = start + duration
            # Converter início/fim em índices de bin
            start_idx = int(np.floor(start * 100.0 / density_interval))
            end_idx   = int(np.floor(note_end * 100.0 / density_interval))

            if start_idx < num_bins:
                # Adicionar 1 a cada bin de start_idx a end_idx
                density_array[start_idx : min(end_idx + 1, num_bins)] += 1

        # 5) Retornar os dados
        return time_array, density_array

    except Exception as e:
        logger.error(f"Erro em analyze_density: {str(e)}")
        raise AnalysisError(f"Erro na análise de densidade", e)


def analyze_density_with_register(notes: Union[List[Tuple[float, float, float]], 'ScoreData'],
                                 density_interval: float = DEFAULT_DENSITY_INTERVAL
                                ) -> Dict[str, Any]:
    """
    Análise avançada de densidade que inclui informações de registro.

    Args:
        notes: Lista de tuplas (start_time, duration, pitch) ou um objeto ScoreData.
        density_interval: Intervalo de tempo (em centisegundos).

    Returns:
        Um dicionário contendo arrays de tempo e densidade, além de informações de registro.
    """
    # Obter densidade básica
    time_array, density_array = analyze_density(notes, density_interval)
    
    # Verificar se temos um objeto ScoreData ou uma lista de tuplas
    if hasattr(notes, 'notes') and not isinstance(notes, list):
        # Converter ScoreData para lista de tuplas
        notes_data = [(n.start_time, n.duration, n.pitch) for n in notes.notes]
    else:
        notes_data = notes

    if not notes_data or len(time_array) == 0:
        return {
            'time': time_array,
            'density': density_array,
            'register': np.array([]),
            'register_high': np.array([]),
            'register_low': np.array([]),
            'register_mean': 0
        }

    # Analisar distribuição de registro
    register_array = np.zeros((128, len(time_array)))  # 128 possíveis valores MIDI pitch
    
    for (start, duration, pitch) in notes_data:
        if not (0 <= pitch < 128):
            continue  # Pular pitches inválidos
            
        note_end = start + duration
        # Converter para índices
        start_idx = int(np.floor(start * 100.0 / density_interval))
        end_idx = int(np.floor(note_end * 100.0 / density_interval))
        
        if start_idx < len(time_array):
            # Incrementar a contagem para este pitch nos bins relevantes
            register_array[int(pitch), start_idx:min(end_idx+1, len(time_array))] += 1
    
    # Calcular estatísticas de registro
    register_mean = np.zeros(len(time_array))
    register_high = np.zeros(len(time_array))
    register_low = np.zeros(len(time_array))
    
    for i in range(len(time_array)):
        pitches_at_time = np.where(register_array[:, i] > 0)[0]
        if len(pitches_at_time) > 0:
            register_mean[i] = np.mean(pitches_at_time)
            register_high[i] = np.max(pitches_at_time)
            register_low[i] = np.min(pitches_at_time)
    
    # Retornar resultados completos
    return {
        'time': time_array,
        'density': density_array,
        'register': register_array,
        'register_high': register_high,
        'register_low': register_low,
        'register_mean': register_mean
    }


# Função auxiliar para compatibilidade com versões anteriores
def visualize_density(time_array, density_array, show_details=True):
    """
    Placeholder para compatibilidade com versões anteriores.
    Agora usamos plot_density no módulo visualization.plotters.
    """
    logger.warning("visualize_density está obsoleta. Use plot_density do módulo visualization.plotters.")
    import matplotlib.pyplot as plt
    
    plt.figure(figsize=(12, 6))
    plt.plot(time_array, density_array)
    plt.grid(True)
    plt.xlabel('Time (seconds)')
    plt.ylabel('Note Count')
    plt.title('Note Density Analysis')
    plt.show()


__all__ = ['analyze_density', 'analyze_density_with_register', 'visualize_density', 'DensityEvent']