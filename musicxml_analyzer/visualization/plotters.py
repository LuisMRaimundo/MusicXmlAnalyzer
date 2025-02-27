# visualization/plotters.py

"""
Funções de plotagem melhoradas para análise MusicXML.
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from typing import List, Dict, Optional, Any
import logging
from scipy.ndimage import gaussian_filter

logger = logging.getLogger(__name__)

def plot_dynamics(ax, events, show_parts=True, show_gradual=True):
    """
    Plota resultados de análise de dinâmica em um eixo matplotlib.
    
    Args:
        ax: Eixo matplotlib para plotar
        events: Lista de objetos DynamicEvent
        show_parts: Se deve mostrar diferentes partes com cores diferentes
        show_gradual: Se deve mostrar dinâmicas graduais
    """
    if not events:
        logger.warning("Nenhum evento de dinâmica para visualizar")
        ax.text(0.5, 0.5, "Nenhuma dinâmica encontrada na partitura", 
                ha='center', va='center', transform=ax.transAxes)
        return
        
    try:
        # Obter mapa de dinâmicas
        dynamics_map = {}
        for level in ['pppp', 'ppp', 'pp', 'p', 'mp', 'mf', 'f', 'ff', 'fff', 'ffff']:
            # Valores aproximados, substitua pelos valores reais da sua configuração
            dynamics_map[level] = {'value': 20 + (level.count('f') - level.count('p')) * 10}
            
        # Plotar dinâmicas por parte
        if show_parts:
            parts = sorted(set(e.part for e in events))
            colors = plt.cm.tab10(np.linspace(0, 1, len(parts)))
            
            for part, color in zip(parts, colors):
                part_events = [e for e in events if e.part == part]
                times = [e.time for e in part_events]
                intensities = [e.intensity for e in part_events]
                
                ax.plot(times, intensities, 'o-', 
                        color=color, 
                        label=part,
                        alpha=0.7)
        else:
            # Plotar todos os eventos em uma cor
            times = [e.time for e in events]
            intensities = [e.intensity for e in events]
            ax.plot(times, intensities, 'o-', label='Dinâmicas')
        
        # Adicionar marcações graduais, se solicitado
        if show_gradual:
            gradual_events = [e for e in events if hasattr(e, 'type') and e.type == 'gradual']
            if gradual_events:
                for event in gradual_events:
                    ax.axvline(x=event.time, color='gray', linestyle='--', alpha=0.5)
        
        # Configurar o plot
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Tempo (batidas)')
        ax.set_ylabel('Nível de Dinâmica')
        ax.set_title('Análise de Dinâmica por Parte')
        
        # Adicionar marcações de dinâmica no eixo y
        levels = sorted(set(dynamics_map.keys()))
        ax.set_yticks([dynamics_map[d]['value'] for d in levels if d in dynamics_map])
        ax.set_yticklabels([d for d in levels if d in dynamics_map])
        
        # Adicionar legenda se mostrar partes
        if show_parts:
            ax.legend(loc='best')
            
    except Exception as e:
        logger.error(f"Erro em plot_dynamics: {e}")
        ax.text(0.5, 0.5, f"Erro: {str(e)}", 
                ha='center', va='center', transform=ax.transAxes)


def plot_combined_dynamics(ax, events):
    """
    Plota uma linha geral de dinâmica combinando todas as partes.
    
    Args:
        ax: Eixo matplotlib para plotar
        events: Lista de objetos DynamicEvent
    """
    if not events:
        logger.warning("Nenhum evento de dinâmica para visualizar")
        ax.text(0.5, 0.5, "Nenhuma dinâmica encontrada na partitura", 
                ha='center', va='center', transform=ax.transAxes)
        return
    
    try:
        # Obter mapa de dinâmicas para configuração do eixo y
        dynamics_map = {}
        for level in ['pppp', 'ppp', 'pp', 'p', 'mp', 'mf', 'f', 'ff', 'fff', 'ffff']:
            dynamics_map[level] = {'value': 20 + (level.count('f') - level.count('p')) * 10}
        
        # Ordenar todos os eventos por tempo
        sorted_events = sorted(events, key=lambda e: e.time)
        
        # Se nenhum evento, retornar
        if not sorted_events:
            ax.text(0.5, 0.5, "Nenhuma dinâmica encontrada", 
                    ha='center', va='center', transform=ax.transAxes)
            return
        
        # Coletar todos os tempos e intensidades
        all_times = [e.time for e in sorted_events]
        all_intensities = [e.intensity for e in sorted_events]
        
        # Criar uma linha do tempo unificada
        min_time = min(all_times)
        max_time = max(all_times)
        
        # Crie uma linha do tempo com incrementos regulares
        timeline = np.linspace(min_time, max_time, 500)
        
        # Calcular intensidades para cada ponto da linha do tempo
        # Usamos interpolação ponderada por proximidade
        def calculate_intensity_at_time(t):
            # Encontrar o índice do evento mais próximo antes e depois de t
            before_idx = [i for i, et in enumerate(all_times) if et <= t]
            after_idx = [i for i, et in enumerate(all_times) if et > t]
            
            if not before_idx and not after_idx:
                return 0  # Nenhum evento
            
            if not before_idx:
                return all_intensities[after_idx[0]]  # Use o primeiro evento
            
            if not after_idx:
                return all_intensities[before_idx[-1]]  # Use o último evento
            
            # Interpolar
            before = before_idx[-1]
            after = after_idx[0]
            
            t_before = all_times[before]
            t_after = all_times[after]
            
            # Calcular peso (inversamente proporcional à distância)
            if t_after == t_before:
                weight = 1.0
            else:
                weight = (t - t_before) / (t_after - t_before)
            
            # Interpolar
            i_before = all_intensities[before]
            i_after = all_intensities[after]
            
            return i_before * (1 - weight) + i_after * weight
        
        # Calcular intensidades combinadas
        combined_intensities = [calculate_intensity_at_time(t) for t in timeline]
        
        # Suavizar a curva para uma visualização mais clara
        combined_intensities = gaussian_filter(combined_intensities, sigma=5)
        
        # Plotar a curva combinada
        ax.plot(timeline, combined_intensities, 'r-', linewidth=2.5, label='Dinâmica Geral')
        
        # Adicionar todos os pontos de dinâmica como referência
        ax.scatter(all_times, all_intensities, color='blue', alpha=0.3, s=15, label='Marcações de Dinâmica')
        
        # Configurar o plot
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Tempo (batidas)')
        ax.set_ylabel('Nível de Dinâmica')
        ax.set_title('Curva de Dinâmica Geral')
        
        # Adicionar marcações de dinâmica no eixo y
        levels = sorted(set(dynamics_map.keys()))
        ax.set_yticks([dynamics_map[d]['value'] for d in levels if d in dynamics_map])
        ax.set_yticklabels([d for d in levels if d in dynamics_map])
        
        # Adicionar legenda
        ax.legend(loc='best')
        
    except Exception as e:
        logger.error(f"Erro em plot_combined_dynamics: {e}")
        ax.text(0.5, 0.5, f"Erro: {str(e)}", 
                ha='center', va='center', transform=ax.transAxes)


def plot_density(ax, density_data, show_register=True):
    """
    Plota resultados de análise de densidade em um eixo matplotlib.
    
    Args:
        ax: Eixo matplotlib para plotar
        density_data: Tupla (time_array, density_array)
        show_register: Se deve mostrar distribuição de registro
    """
    time_array, density_array = density_data
    
    if len(time_array) == 0:
        ax.text(0.5, 0.5, "Nenhum dado de densidade para visualizar",
                ha='center', va='center', transform=ax.transAxes)
        return
    
    ax.plot(time_array, density_array, label='Densidade de Notas', color='#1f77b4', linewidth=2)
    ax.fill_between(time_array, density_array, alpha=0.3, color='#1f77b4')
    ax.set_xlabel('Tempo (segundos)')
    ax.set_ylabel('Número de Notas')
    ax.set_title('Densidade de Notas ao Longo do Tempo')
    
    # Melhorar a aparência
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Adicionar estatísticas básicas
    if len(density_array) > 0:
        max_density = np.max(density_array)
        avg_density = np.mean(density_array)
        
        ax.axhline(y=avg_density, color='red', linestyle='--', alpha=0.7, label=f'Média: {avg_density:.1f}')
        
        # Marcar pontos de maior densidade
        peak_threshold = max_density * 0.8
        peak_indices = np.where(density_array > peak_threshold)[0]
        
        if len(peak_indices) > 0:
            peak_times = time_array[peak_indices]
            peak_values = density_array[peak_indices]
            ax.scatter(peak_times, peak_values, color='red', s=50, alpha=0.7, label='Picos')
    
    ax.legend()


def plot_spectrum(ax, notes, mode="heatmap"):
    """
    Plota um espectro básico no eixo fornecido, com melhorias visuais.
    
    Args:
        ax: Um eixo matplotlib
        notes: lista de objetos NoteEvent (start_time, end_time, pitch, velocity, etc.)
        mode: "heatmap" ou "piano_roll"
    """
    if not notes:
        ax.text(0.5, 0.5, "Nenhuma nota para visualizar", ha='center', va='center', transform=ax.transAxes)
        return
    
    # Determinar os limites de tempo e tom
    t_min = min(n.start_time for n in notes)
    t_max = max(n.end_time for n in notes)
    p_min = min(n.pitch for n in notes)
    p_max = max(n.pitch for n in notes)

    # Adicionar espaçamento
    t_range = t_max - t_min
    p_range = p_max - p_min
    
    t_min = max(0, t_min - 0.02 * t_range)
    t_max = t_max + 0.02 * t_range
    p_min = max(0, p_min - 2)
    p_max = min(127, p_max + 2)
    
    # Modo Piano Roll (MELHORADO)
    if mode == "piano_roll":
        import matplotlib.patches as patches
        
        # Agrupar notas por parte para cores diferentes
        parts = sorted(set(n.part for n in notes))
        part_colors = plt.cm.tab10(np.linspace(0, 1, len(parts)))
        part_color_dict = {part: color for part, color in zip(parts, part_colors)}
        
        # Definir transparência baseada no valor de velocidade
        for n in notes:
            # Altura personalizada baseada na velocidade
            # Notas mais intensas são mais altas
            height = 0.6 + 0.4 * n.velocity
            
            # Cor personalizada para cada parte
            color = part_color_dict.get(n.part, 'blue')
            
            # Criar retângulo com bordas mais escuras
            rect = patches.Rectangle(
                (n.start_time, n.pitch - height/2),
                n.end_time - n.start_time,
                height,
                facecolor=color,
                alpha=min(0.9, 0.3 + n.velocity * 0.7),  # Mais visível para notas mais fortes
                edgecolor='black',
                linewidth=0.5
            )
            ax.add_patch(rect)
        
        # Adicionar legenda das partes
        legend_patches = [patches.Patch(color=color, label=part) 
                        for part, color in zip(parts, part_colors)]
        ax.legend(handles=legend_patches, loc='upper right')
        
        # Adicionar fundo de piano para melhor visualização
        for pitch in range(int(p_min), int(p_max) + 1):
            is_black = pitch % 12 in [1, 3, 6, 8, 10]  # notas pretas do piano
            color = '#e6e6e6' if not is_black else '#f8f8f8'
            ax.axhspan(pitch - 0.5, pitch + 0.5, color=color, alpha=0.2, linewidth=0)
        
        # Adicionar linhas para oitavas
        for octave in range(0, 11):
            pitch = octave * 12
            if p_min <= pitch <= p_max:
                ax.axhline(y=pitch, color='gray', linestyle='-', alpha=0.3)
                
        ax.set_title("Piano Roll (Visualização de Notas)")
        
    # Modo Heatmap (MELHORADO COM MAIS CONTRASTE)
    elif mode == "heatmap":
        # Criar um mapa de calor de maior resolução e com melhor contraste
        time_bins = 400
        pitch_range = int(p_max - p_min + 1)
        energy = np.zeros((pitch_range, time_bins), dtype=float)
        times = np.linspace(t_min, t_max, time_bins)

        # Preencher com valores de todas as notas
        for n in notes:
            # Identificar bins de início e fim
            start_idx = np.searchsorted(times, n.start_time)
            end_idx = np.searchsorted(times, n.end_time)
            
            # Índice de pitch
            pitch_idx = int(n.pitch - p_min)
            
            # Garantir que estamos dentro dos limites
            if 0 <= pitch_idx < pitch_range and start_idx < time_bins:
                # Usar a velocidade como valor para enfatizar notas mais fortes
                # Amplificar para maior contraste
                velocity = n.velocity * 1.5  # Aumentar o efeito da velocidade
                end_idx = min(end_idx, time_bins - 1)
                energy[pitch_idx, start_idx:end_idx+1] += velocity
        
        # Aplicar suavização gaussiana para um mapa mais suave, mas manter detalhes
        energy = gaussian_filter(energy, sigma=(0.8, 0.3))  # Reduzido para preservar picos
        
        # Amplificar os valores mais altos para aumentar o contraste
        energy = np.power(energy, 1.3)  # Exponencial para aumentar os altos valores
        
        # Colormap personalizado com MUITO mais contraste e brilho
        # Do transparente a cores muito brilhantes
        colors = [
            (1.0, 1.0, 1.0, 0.0),      # Transparente para áreas vazias
            (0.9, 0.9, 1.0, 0.15),     # Azul muito claro quase transparente
            (0.7, 0.7, 1.0, 0.3),      # Azul claro
            (0.4, 0.4, 1.0, 0.5),      # Azul médio
            (0.0, 0.5, 1.0, 0.7),      # Azul forte
            (0.0, 1.0, 1.0, 0.8),      # Ciano/turquesa brilhante
            (1.0, 1.0, 0.0, 0.85),     # Amarelo vivo
            (1.0, 0.5, 0.0, 0.9),      # Laranja brilhante
            (1.0, 0.0, 0.0, 0.95),     # Vermelho vivo
            (1.0, 0.0, 0.5, 1.0)       # Magenta intenso
        ]
        
        custom_cmap = LinearSegmentedColormap.from_list("custom_high_contrast", colors, N=256)
        
        # Normalização melhorada para destacar áreas de alta densidade
        if np.max(energy) > 0:
            vmax = np.max(energy)
            vmin = 0
            
            # Comprimir a faixa dinâmica para destacar valores altos
            vmax_display = vmax * 0.7  # Mostrar 70% do máximo como saturação
            
            img = ax.imshow(
                energy,
                origin='lower',
                aspect='auto',
                extent=[t_min, t_max, p_min, p_max],
                cmap=custom_cmap,
                interpolation='bilinear',  # Suavização para melhor visual
                vmin=vmin,
                vmax=vmax_display
            )
            
            # Adicionar barra de cores com mais divisões
            cbar = plt.colorbar(img, ax=ax, label="Intensidade de Eventos", ticks=np.linspace(0, vmax_display, 6))
            cbar.ax.set_yticklabels([f"{int(100*v/vmax)}%" for v in np.linspace(0, vmax_display, 6)])
        else:
            # Fallback se não houver energia
            img = ax.imshow(
                energy,
                origin='lower',
                aspect='auto',
                extent=[t_min, t_max, p_min, p_max],
                cmap=custom_cmap,
                interpolation='bilinear'
            )
            plt.colorbar(img, ax=ax, label="Intensidade de Eventos")
        
        # Adicionar contornos para destacar áreas de alta intensidade
        if np.max(energy) > 0:
            # Adicionar contornos apenas para valores altos
            contour_levels = np.linspace(vmax * 0.6, vmax, 3)
            contours = ax.contour(
                times, 
                np.arange(p_min, p_max + 1), 
                energy, 
                levels=contour_levels,
                colors=['white'],
                linewidths=0.8,
                alpha=0.7
            )
        
        ax.set_title("Mapa de Calor Espectral (Alta Definição)")
    
    else:
        ax.text(0.5, 0.5, f"Modo desconhecido: {mode}",
                ha='center', va='center', transform=ax.transAxes)
        return
    
    # Configurações comuns
    ax.set_xlim(t_min, t_max)
    ax.set_ylim(p_min, p_max)
    ax.set_xlabel("Tempo (batidas)")
    ax.set_ylabel("Altura (MIDI)")
    
    # Adicionar marcações de notas no eixo y
    pitch_ticks = []
    pitch_labels = []
    
    # Adicionar notas C de cada oitava (Dó)
    for octave in range(0, 10):
        pitch = 12 * octave + 0  # C (Dó)
        if p_min <= pitch <= p_max:
            pitch_ticks.append(pitch)
            pitch_labels.append(f"C{octave}")  # Dó{oitava}
    
    ax.set_yticks(pitch_ticks)
    ax.set_yticklabels(pitch_labels)
    
    # Adicionar linhas de grade apenas para as notas principais
    ax.grid(True, alpha=0.3, linestyle=':')
