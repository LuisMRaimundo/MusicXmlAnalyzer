# modules/spectrum.py

"""
Módulo de Análise Espectral Melhorado
Reescrito para retornar dados em um formato consistente e aprimorar a visualização.
"""

import numpy as np
import logging
from dataclasses import dataclass
from typing import List, Tuple, Optional, Union, Dict, Any
from scipy.ndimage import gaussian_filter

from musicxml_analyzer.core.exceptions import handle_exceptions, AnalysisError
from musicxml_analyzer.core.cache import cached_analysis
from musicxml_analyzer.config import VISUALIZATION

logger = logging.getLogger(__name__)

@dataclass
class NoteEvent:
    """Representa uma única nota com propriedades espectrais."""
    start_time: float
    end_time: float
    pitch: int
    pitch_name: str
    velocity: float
    part: str
    measure: int
    beat: float


@handle_exceptions(AnalysisError, "Erro na análise espectral")
@cached_analysis("spectrum")
def analyze_spectrum(score) -> List[NoteEvent]:
    """
    Extrai informações detalhadas de notas a partir de um objeto Score ou ScoreData.
    Retorna uma lista de objetos NoteEvent (start, end, pitch, velocity, etc.).
    
    Args:
        score: Um objeto music21.Score ou ScoreData
        
    Returns:
        Uma lista de objetos NoteEvent
    """
    events = []
    try:
        # Se for um objeto ScoreData com .notes
        if hasattr(score, 'notes') and isinstance(score.notes, list):
            for n in score.notes:
                # Validar atributos necessários
                needed = ['start_time','end_time','pitch','pitch_name','velocity','part','measure','beat']
                if not all(hasattr(n, attr) for attr in needed):
                    logger.warning(f"Pulando nota com atributos faltando: {n}")
                    continue
                events.append(NoteEvent(
                    start_time=n.start_time,
                    end_time=n.end_time,
                    pitch=n.pitch,
                    pitch_name=n.pitch_name,
                    velocity=n.velocity,
                    part=n.part,
                    measure=n.measure,
                    beat=n.beat
                ))
        # Se for um objeto music21.Score
        elif hasattr(score, 'parts'):
            from music21 import chord, note
            
            for part_idx, part in enumerate(score.parts):
                if not hasattr(part, 'flat'):
                    logger.warning(f"Pulando parte {part_idx}, sem 'flat'")
                    continue
                part_name = getattr(part, 'partName', f"Parte {part_idx+1}")

                for obj in part.flat.notes:
                    if not isinstance(obj, (note.Note, chord.Chord)):
                        continue

                    offset_val = float(getattr(obj, 'offset', 0.0))
                    dur_val    = float(getattr(obj.duration, 'quarterLength', 0.0))
                    end_val    = offset_val + dur_val
                    measure    = getattr(obj, 'measureNumber', 0)
                    beat       = getattr(obj, 'beat', 0.0)

                    def get_velocity(o):
                        vol = getattr(o, 'volume', None)
                        if vol and vol.velocity is not None:
                            return float(vol.velocity) / 127.0
                        return 0.8

                    if isinstance(obj, note.Note):
                        midi_pitch   = getattr(obj.pitch, 'midi', None)
                        pitch_name   = getattr(obj.pitch, 'nameWithOctave', "N/A")
                        if midi_pitch is None:
                            continue
                        velocity_val = get_velocity(obj)

                        events.append(NoteEvent(
                            start_time=offset_val,
                            end_time=end_val,
                            pitch=midi_pitch,
                            pitch_name=pitch_name,
                            velocity=velocity_val,
                            part=part_name,
                            measure=measure,
                            beat=beat
                        ))
                    else:
                        # obj é um acorde
                        for p in obj.pitches:
                            midi_pitch = getattr(p, 'midi', None)
                            pitch_name = getattr(p, 'nameWithOctave', "N/A")
                            if midi_pitch is None:
                                continue
                            velocity_val = get_velocity(obj)
                            events.append(NoteEvent(
                                start_time=offset_val,
                                end_time=end_val,
                                pitch=midi_pitch,
                                pitch_name=pitch_name,
                                velocity=velocity_val,
                                part=part_name,
                                measure=measure,
                                beat=beat
                            ))
        else:
            raise ValueError("Objeto de partitura não reconhecido (deve ter .notes ou .parts)")

        # Ordenar por start_time
        events.sort(key=lambda e: e.start_time)
        return events

    except Exception as e:
        logger.error(f"Erro analisando espectro: {e}")
        raise


def analyze_spectral_density(notes: List[NoteEvent], 
                           resolution: Tuple[int, int] = (128, 400),
                           smoothing: float = 1.5) -> Dict[str, Any]:
    """
    Calcula a densidade espectral da música (distribuição de alturas ao longo do tempo).
    
    Args:
        notes: Lista de objetos NoteEvent
        resolution: Tupla (resolução_pitch, resolução_tempo)
        smoothing: Fator de suavização gaussiana
        
    Returns:
        Um dicionário contendo matrizes de energia espectral e informações de contexto
    """
    if not notes:
        return {
            'energy': np.array([]),
            'time_range': (0, 0),
            'pitch_range': (60, 72)
        }
    
    try:
        # Extrair tempos e alturas
        t_min = min(n.start_time for n in notes)
        t_max = max(n.end_time for n in notes)
        p_min = min(n.pitch for n in notes)
        p_max = max(n.pitch for n in notes)
        
        # Adicionar um pouco de espaço
        pitch_padding = (p_max - p_min) * 0.1
        time_padding = (t_max - t_min) * 0.05
        
        p_min = max(0, p_min - pitch_padding)
        p_max = min(127, p_max + pitch_padding)
        t_min = max(0, t_min - time_padding)
        t_max = t_max + time_padding
        
        # Configurar dimensões
        pitch_res, time_res = resolution
        
        # Criar matriz de energia
        energy = np.zeros((pitch_res, time_res), dtype=float)
        
        # Criar bordas de tempo
        time_edges = np.linspace(t_min, t_max, time_res)
        
        # Preencher matriz de energia
        for n in notes:
            # Tempos de início e fim
            start_t = n.start_time
            end_t = n.end_time
            
            # Velocidade/intensidade
            intensity = n.velocity
            
            # Bins de tempo para esta nota
            time_mask = (time_edges >= start_t) & (time_edges <= end_t)
            if not np.any(time_mask):
                continue
                
            # Bin de altura
            if p_max > p_min:
                pitch_idx = int((n.pitch - p_min) / (p_max - p_min) * (pitch_res - 1))
            else:
                pitch_idx = 0
                
            # Adicionar energia
            if 0 <= pitch_idx < pitch_res:
                energy[pitch_idx, time_mask] += intensity
        
        # Aplicar suavização
        if np.any(energy) and smoothing > 0:
            energy = gaussian_filter(energy, sigma=(smoothing, smoothing))
            
        # Retornar dados completos
        return {
            'energy': energy,
            'time_range': (t_min, t_max),
            'pitch_range': (p_min, p_max),
            'time_edges': time_edges,
            'pitch_resolution': pitch_res,
            'time_resolution': time_res
        }
        
    except Exception as e:
        logger.error(f"Erro em analyze_spectral_density: {e}")
        raise


# Função auxiliar para compatibilidade com versões anteriores
def visualize_spectrum(notes, mode="piano_roll"):
    """
    Placeholder para compatibilidade com versões anteriores.
    Agora usamos plot_spectrum do módulo visualization.plotters.
    """
    logger.warning("visualize_spectrum está obsoleta. Use plot_spectrum do módulo visualization.plotters.")
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    if mode == "piano_roll":
        import matplotlib.patches as patches
        
        t_min = min(n.start_time for n in notes)
        t_max = max(n.end_time for n in notes)
        p_min = min(n.pitch for n in notes)
        p_max = max(n.pitch for n in notes)
        
        for n in notes:
            rect = patches.Rectangle(
                (n.start_time, n.pitch - 0.4),
                n.end_time - n.start_time,
                0.8,
                facecolor='blue',
                alpha=n.velocity,
                edgecolor='black'
            )
            ax.add_patch(rect)
            
        ax.set_xlim(t_min, t_max)
        ax.set_ylim(p_min - 1, p_max + 1)
    
    elif mode == "heatmap":
        result = analyze_spectral_density(notes)
        
        if len(result['energy']) > 0:
            t_min, t_max = result['time_range']
            p_min, p_max = result['pitch_range']
            
            ax.imshow(
                result['energy'],
                origin='lower',
                aspect='auto',
                extent=[t_min, t_max, p_min, p_max],
                cmap='magma'
            )
    
    ax.set_xlabel('Tempo (batidas)')
    ax.set_ylabel('Altura (MIDI)')
    ax.set_title(f'Análise Espectral ({mode})')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


__all__ = [
    "NoteEvent",
    "analyze_spectrum",
    "analyze_spectral_density",
    "visualize_spectrum"
]