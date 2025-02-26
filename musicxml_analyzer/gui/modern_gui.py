# gui/modern_gui.py

"""
GUI Aprimorada para MusicXML Analyzer com componentes modernos e correções.
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
from pathlib import Path
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# Importações da aplicação
from musicxml_analyzer.core.exceptions import MusicXMLAnalysisError
from musicxml_analyzer.core.model import ScoreData, ScoreParser
from musicxml_analyzer.modules.dynamics import analyze_dynamics
from musicxml_analyzer.modules.density import analyze_density
from musicxml_analyzer.modules.spectrum import analyze_spectrum
from musicxml_analyzer.visualization.plotters import (
    plot_dynamics,
    plot_combined_dynamics,
    plot_density,
    plot_spectrum
)
from musicxml_analyzer.config import DEFAULT_DENSITY_INTERVAL

logger = logging.getLogger(__name__)


class ThemeManager:
    """Gerencia temas e estilos da aplicação."""
    
    # Define temas
    THEMES = {
        "Light": {
            "bg": "#ffffff",
            "fg": "#333333",
            "accent": "#4a6fa5",
            "button": "#e0e0e0",
            "highlight": "#dae5f4"
        },
        "Dark": {
            "bg": "#282c34",
            "fg": "#abb2bf",
            "accent": "#61afef",
            "button": "#3e4451",
            "highlight": "#3a4049"
        },
        "Contrast": {
            "bg": "#000000",
            "fg": "#ffffff",
            "accent": "#ffcc00",
            "button": "#333333",
            "highlight": "#444444"
        }
    }
    
    @staticmethod
    def apply_theme(root, theme_name):
        """Aplica o tema selecionado à aplicação."""
        if theme_name not in ThemeManager.THEMES:
            theme_name = "Light"  # Padrão
            
        theme = ThemeManager.THEMES[theme_name]
        
        # Configura estilos ttk
        style = ttk.Style()
        style.configure("TFrame", background=theme["bg"])
        style.configure("TLabel", background=theme["bg"], foreground=theme["fg"])
        style.configure("TButton", background=theme["button"], foreground=theme["fg"])
        style.configure("TCheckbutton", background=theme["bg"], foreground=theme["fg"])
        style.configure("TRadiobutton", background=theme["bg"], foreground=theme["fg"])
        
        # Configura estilos específicos da aplicação
        style.configure("Accent.TButton", background=theme["accent"], foreground="#ffffff")
        style.configure("Title.TLabel", font=("Helvetica", 14, "bold"))
        
        # Aplica à janela raiz
        root.configure(bg=theme["bg"])
        
        return theme


class SettingsManager:
    """Gerencia configurações e preferências da aplicação."""
    
    def __init__(self, settings_file="settings.json"):
        """Inicializa com o caminho do arquivo de configurações."""
        self.settings_file = settings_file
        self.settings = self._load_settings()
        
    def _load_settings(self) -> Dict:
        """Carrega configurações do arquivo ou retorna padrões."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Falha ao carregar configurações: {e}")
            
        # Configurações padrão
        return {
            "theme": "Light",
            "recent_files": [],
            "analysis": {
                "density_interval": DEFAULT_DENSITY_INTERVAL,
                "enable_dynamics": True,
                "enable_density": True,
                "enable_spectrum": True,
                "enable_heatmap": True,
                "enable_combined_dynamics": True
            },
            "visualization": {
                "colormap": "viridis",
                "dpi": 100,
                "show_grid": True
            },
            "export": {
                "default_format": "png",
                "default_directory": ""
            }
        }
        
    def save_settings(self):
        """Salva configurações atuais no arquivo."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.settings_file)), exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.warning(f"Falha ao salvar configurações: {e}")
            
    def get(self, key, default=None):
        """Obtém um valor de configuração por chave."""
        keys = key.split('.')
        value = self.settings
        for k in keys:
            if k not in value:
                return default
            value = value[k]
        return value
        
    def set(self, key, value):
        """Define um valor de configuração por chave."""
        keys = key.split('.')
        target = self.settings
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
        self.save_settings()
        
    def add_recent_file(self, file_path):
        """Adiciona um arquivo a arquivos recentes."""
        if not file_path:
            return
            
        recent = self.settings.get("recent_files", [])
        if file_path in recent:
            recent.remove(file_path)
        recent.insert(0, file_path)
        self.settings["recent_files"] = recent[:10]  # Mantém apenas 10 mais recentes
        self.save_settings()


class AnalysisTab(ttk.Frame):
    """Classe base para abas de análise."""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.score_data = None
        self.result = None
        self.setup_ui()
        
    def setup_ui(self):
        """Sobrescreva na subclasse para configurar a UI específica."""
        pass
        
    def update_data(self, score_data):
        """Atualiza com novos dados de partitura."""
        self.score_data = score_data
        self.clear()
        
    def run_analysis(self):
        """Sobrescreva na subclasse para executar análise específica."""
        pass
        
    def clear(self):
        """Limpa resultados e plots de análise."""
        for widget in self.winfo_children():
            if isinstance(widget, FigureCanvasTkAgg):
                widget.get_tk_widget().destroy()
        self.result = None


class DynamicsTab(AnalysisTab):
    """Aba para análise de dinâmica."""
    
    def setup_ui(self):
        """Configura UI de análise de dinâmica."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
    
        # Frame de controles
        controls = ttk.Frame(self)
        controls.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
    
        ttk.Button(controls, text="Executar Análise de Dinâmica", 
                  command=self.run_analysis).pack(side=tk.LEFT, padx=5)
    
        # Função para atualizar a visualização quando as opções mudam
        def update_on_change():
            if hasattr(self, 'result') and self.result:
                self.run_analysis()
    
        self.show_parts_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls, text="Mostrar Partes Individuais", 
                       variable=self.show_parts_var, 
                       command=update_on_change).pack(side=tk.LEFT, padx=5)
    
        self.show_gradual_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls, text="Mostrar Dinâmicas Graduais", 
                       variable=self.show_gradual_var,
                       command=update_on_change).pack(side=tk.LEFT, padx=5)
    
        self.show_combined_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls, text="Mostrar Dinâmica Geral", 
                       variable=self.show_combined_var,
                       command=update_on_change).pack(side=tk.LEFT, padx=5)
    
        # Frame de plotagem (será preenchido após análise)
        self.plot_frame = ttk.Frame(self)
        self.plot_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        
    def run_analysis(self):
        """Executa análise de dinâmica."""
        if not self.score_data:
            messagebox.showwarning("Aviso", "Nenhuma partitura carregada")
            return
        
        try:
            self.controller.set_status("Executando análise de dinâmica...")
            self.clear()
        
            # Executar análise
            self.result = analyze_dynamics(self.score_data)
        
            # Criar notebook para diferentes visualizações
            plot_notebook = ttk.Notebook(self.plot_frame)
            plot_notebook.pack(fill=tk.BOTH, expand=True)
        
            # Verificar quais visualizações devem ser mostradas com base nas checkboxes
            show_parts = self.show_parts_var.get()
            show_gradual = self.show_gradual_var.get()
            show_combined = self.show_combined_var.get()
        
            # Adicionar aba para dinâmicas por parte apenas se a opção estiver marcada
            if show_parts:
                parts_frame = ttk.Frame(plot_notebook)
                plot_notebook.add(parts_frame, text="Dinâmicas por Parte")
            
                fig_parts = Figure(figsize=(8, 5), dpi=100)
                ax_parts = fig_parts.add_subplot(111)
            
                plot_dynamics(
                    ax_parts, 
                    self.result, 
                    show_parts=True,
                    show_gradual=show_gradual
                )
            
                canvas_parts = FigureCanvasTkAgg(fig_parts, master=parts_frame)
                canvas_parts.draw()
                canvas_parts.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
                toolbar_parts = NavigationToolbar2Tk(canvas_parts, parts_frame)
                toolbar_parts.update()
        
            # Adicionar aba para dinâmica combinada apenas se a opção estiver marcada
            if show_combined:
                combined_frame = ttk.Frame(plot_notebook)
                plot_notebook.add(combined_frame, text="Curva de Dinâmica Geral")
            
                fig_combined = Figure(figsize=(8, 5), dpi=100)
                ax_combined = fig_combined.add_subplot(111)
            
                plot_combined_dynamics(ax_combined, self.result)
            
                canvas_combined = FigureCanvasTkAgg(fig_combined, master=combined_frame)
                canvas_combined.draw()
                canvas_combined.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
                toolbar_combined = NavigationToolbar2Tk(canvas_combined, combined_frame)
                toolbar_combined.update()
        
            # Verificar se ao menos uma visualização foi criada
            if not (show_parts or show_combined):
                messagebox.showinfo("Aviso", "Nenhuma visualização selecionada. Selecione pelo menos uma opção.")
            
            self.controller.set_status("Análise de dinâmica concluída")
        
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na análise de dinâmica: {e}")
            self.controller.set_status("Falha na análise de dinâmica", error=True)


class DensityTab(AnalysisTab):
    """Aba para análise de densidade de notas."""
    
    def setup_ui(self):
        """Configura UI de análise de densidade."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        
        # Frame de controles
        controls = ttk.Frame(self)
        controls.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        ttk.Label(controls, text="Intervalo (centisegundos):").pack(side=tk.LEFT, padx=5)
        
        self.interval_var = tk.DoubleVar(value=DEFAULT_DENSITY_INTERVAL)
        ttk.Entry(controls, textvariable=self.interval_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls, text="Executar Análise de Densidade", 
                  command=self.run_analysis).pack(side=tk.LEFT, padx=5)
        
        self.show_register_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls, text="Mostrar Distribuição de Registro", 
                       variable=self.show_register_var).pack(side=tk.LEFT, padx=5)
        
        # Frame de plotagem (será preenchido após análise)
        self.plot_frame = ttk.Frame(self)
        self.plot_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
    def run_analysis(self):
        """Executa análise de densidade."""
        if not self.score_data:
            messagebox.showwarning("Aviso", "Nenhuma partitura carregada")
            return
        
        try:
            interval = float(self.interval_var.get())
            if interval <= 0:
                messagebox.showwarning("Aviso", "O intervalo deve ser positivo")
                return
            
            self.controller.set_status("Executando análise de densidade...")
            self.clear()
        
            # Modificação aqui: Passar diretamente o score_data (sem converter para lista)
            # Em vez de:
            # notes_list = [(n.start_time, n.duration, n.pitch) for n in self.score_data.notes]
            # self.result = analyze_density(notes_list, density_interval=interval)
        
            # Faça:
            self.result = analyze_density(self.score_data, density_interval=interval)
        
            # Criar plot
            fig = Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)
        
            # Plotar usando a função de plotters.py
            plot_density(
                ax, 
                self.result, 
                show_register=self.show_register_var.get()
            )
        
            
            # Adicionar plot ao frame
            canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Adicionar barra de navegação
            toolbar = NavigationToolbar2Tk(canvas, self.plot_frame)
            toolbar.update()
            
            self.controller.set_status("Análise de densidade concluída")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na análise de densidade: {e}")
            self.controller.set_status("Falha na análise de densidade", error=True)


class SpectrumTab(AnalysisTab):
    """Aba para análise espectral."""
    
    def setup_ui(self):
        """Configura UI de análise espectral."""
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        
        # Frame de controles
        controls = ttk.Frame(self)
        controls.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        ttk.Button(controls, text="Executar Análise Espectral", 
                  command=self.run_analysis).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(controls, text="Exibição:").pack(side=tk.LEFT, padx=5)
        
        self.display_var = tk.StringVar(value="heatmap")
        ttk.Radiobutton(controls, text="Mapa de Calor", 
                      variable=self.display_var, value="heatmap").pack(side=tk.LEFT)
        ttk.Radiobutton(controls, text="Piano Roll", 
                      variable=self.display_var, value="piano_roll").pack(side=tk.LEFT)
        
        # Frame de plotagem (será preenchido após análise)
        self.plot_frame = ttk.Frame(self)
        self.plot_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
    def run_analysis(self):
        """Executa análise espectral."""
        if not self.score_data:
            messagebox.showwarning("Aviso", "Nenhuma partitura carregada")
            return
            
        try:
            self.controller.set_status("Executando análise espectral...")
            self.clear()
            
            # Executar análise
            self.result = analyze_spectrum(self.score_data)
            
            # Criar notebook para diferentes visualizações
            plot_notebook = ttk.Notebook(self.plot_frame)
            plot_notebook.pack(fill=tk.BOTH, expand=True)
            
            # Tab 1: Piano Roll aprimorado
            piano_frame = ttk.Frame(plot_notebook)
            plot_notebook.add(piano_frame, text="Piano Roll")
            
            fig_piano = Figure(figsize=(10, 6), dpi=100)
            ax_piano = fig_piano.add_subplot(111)
            
            plot_spectrum(ax_piano, self.result, mode="piano_roll")
            
            canvas_piano = FigureCanvasTkAgg(fig_piano, master=piano_frame)
            canvas_piano.draw()
            canvas_piano.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            toolbar_piano = NavigationToolbar2Tk(canvas_piano, piano_frame)
            toolbar_piano.update()
            
            # Tab 2: Mapa de calor aprimorado
            heatmap_frame = ttk.Frame(plot_notebook)
            plot_notebook.add(heatmap_frame, text="Mapa de Calor")
            
            fig_heatmap = Figure(figsize=(10, 6), dpi=100)
            ax_heatmap = fig_heatmap.add_subplot(111)
            
            plot_spectrum(ax_heatmap, self.result, mode="heatmap")
            
            canvas_heatmap = FigureCanvasTkAgg(fig_heatmap, master=heatmap_frame)
            canvas_heatmap.draw()
            canvas_heatmap.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            toolbar_heatmap = NavigationToolbar2Tk(canvas_heatmap, heatmap_frame)
            toolbar_heatmap.update()
            
            # Selecionar a visualização preferida do usuário
            if self.display_var.get() == "heatmap":
                plot_notebook.select(1)  # Índice da aba de mapa de calor
            else:
                plot_notebook.select(0)  # Índice da aba de piano roll
            
            self.controller.set_status("Análise espectral concluída")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na análise espectral: {e}")
            self.controller.set_status("Falha na análise espectral", error=True)


class EnhancedMusicXMLAnalyzer(tk.Tk):
    """Aplicação aprimorada de Análise MusicXML."""
    
    def __init__(self):
        super().__init__()
        
        # Configurar janela
        self.title("Analisador MusicXML Aprimorado")
        self.geometry("1200x800")
        
        # Carregar configurações
        self.settings = SettingsManager()
        
        # Aplicar tema
        self.theme = ThemeManager.apply_theme(self, self.settings.get("theme", "Light"))
        
        # Configurar frame principal
        self.setup_ui()
        
        # Inicializar estado
        self.file_path = None
        self.score_data = None
        self.busy = False
        
    def setup_ui(self):
        """Configura a interface do usuário aprimorada."""
        # Configurar grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Menu
        self.rowconfigure(1, weight=0)  # Informações do arquivo
        self.rowconfigure(2, weight=1)  # Abas
        self.rowconfigure(3, weight=0)  # Status
        
        # Configurar menu
        self.create_menu()
        
        # Frame de informações do arquivo
        self.file_frame = ttk.LabelFrame(self, text="Informações do Arquivo")
        self.file_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)

        # Primeira linha: selecionar arquivo
        file_select_frame = ttk.Frame(self.file_frame)
        file_select_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
        file_select_frame.columnconfigure(1, weight=1)  # Faz o campo de entrada expandir

        ttk.Label(file_select_frame, text="Arquivo:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.file_var = tk.StringVar()
        ttk.Entry(file_select_frame, textvariable=self.file_var, width=70).grid(row=0, column=1, padx=5, pady=2, sticky="ew")

        # Frame para botões de ação
        file_buttons_frame = ttk.Frame(file_select_frame)
        file_buttons_frame.grid(row=0, column=2, padx=5, pady=2, sticky="e")

        ttk.Button(file_buttons_frame, text="Procurar", command=self.browse_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(file_buttons_frame, text="Atualizar", command=self.refresh_ui, 
                style="Accent.TButton").pack(side=tk.LEFT, padx=2)
        
        # Criar exibição de metadados
        self.metadata_frame = ttk.Frame(self.file_frame)
        self.metadata_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        self.title_var = tk.StringVar(value="Título: ")
        self.composer_var = tk.StringVar(value="Compositor: ")
        self.time_sig_var = tk.StringVar(value="Fórmula de Compasso: ")
        self.key_sig_var = tk.StringVar(value="Tonalidade: ")
        self.parts_var = tk.StringVar(value="Partes: ")
        
        ttk.Label(self.metadata_frame, textvariable=self.title_var).pack(side=tk.LEFT, padx=10)
        ttk.Label(self.metadata_frame, textvariable=self.composer_var).pack(side=tk.LEFT, padx=10)
        ttk.Label(self.metadata_frame, textvariable=self.time_sig_var).pack(side=tk.LEFT, padx=10)
        ttk.Label(self.metadata_frame, textvariable=self.key_sig_var).pack(side=tk.LEFT, padx=10)
        ttk.Label(self.metadata_frame, textvariable=self.parts_var).pack(side=tk.LEFT, padx=10)
        
        # Criar controle de abas
        self.tab_control = ttk.Notebook(self)
        self.tab_control.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        
        # Criar abas de análise
        self.dynamics_tab = DynamicsTab(self.tab_control, self)
        self.tab_control.add(self.dynamics_tab, text="Dinâmicas")
        
        self.density_tab = DensityTab(self.tab_control, self)
        self.tab_control.add(self.density_tab, text="Densidade")
        
        self.spectrum_tab = SpectrumTab(self.tab_control, self)
        self.tab_control.add(self.spectrum_tab, text="Espectro")
        
        # Criar barra de status
        self.status_frame = ttk.Frame(self)
        self.status_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=5)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Pronto")
        ttk.Label(self.status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        
        self.progress = ttk.Progressbar(self.status_frame, mode='indeterminate', length=200)
        self.progress.pack(side=tk.RIGHT, padx=10)
        
    def create_menu(self):
        """Cria o menu da aplicação."""
        menubar = tk.Menu(self)
        
        # Menu Arquivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Abrir", command=self.browse_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Atualizar", command=self.refresh_ui, accelerator="Ctrl+R")
        
        # Submenu de arquivos recentes
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        self.update_recent_menu()
        file_menu.add_cascade(label="Abrir Recente", menu=self.recent_menu)
        
        file_menu.add_separator()
        file_menu.add_command(label="Exportar Resultados", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.quit)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        
        # Menu Análise
        analysis_menu = tk.Menu(menubar, tearoff=0)
        analysis_menu.add_command(label="Executar Todas as Análises", command=self.run_all_analyses)
        analysis_menu.add_separator()
        analysis_menu.add_command(label="Análise de Dinâmicas", 
                               command=lambda: (self.tab_control.select(0), self.dynamics_tab.run_analysis()))
        analysis_menu.add_command(label="Análise de Densidade", 
                               command=lambda: (self.tab_control.select(1), self.density_tab.run_analysis()))
        analysis_menu.add_command(label="Análise Espectral", 
                               command=lambda: (self.tab_control.select(2), self.spectrum_tab.run_analysis()))
        menubar.add_cascade(label="Análise", menu=analysis_menu)
        self.analysis_menu = analysis_menu  # Guardar referência
        
        # Menu Configurações
        settings_menu = tk.Menu(menubar, tearoff=0)
        
        # Submenu de temas
        theme_menu = tk.Menu(settings_menu, tearoff=0)
        self.theme_var = tk.StringVar(value=self.settings.get("theme", "Light"))
        for theme in ThemeManager.THEMES:
            theme_menu.add_radiobutton(label=theme, variable=self.theme_var, value=theme,
                                     command=lambda t=theme: self.change_theme(t))
        settings_menu.add_cascade(label="Tema", menu=theme_menu)
        
        # Outras configurações
        settings_menu.add_command(label="Preferências", command=self.show_preferences)
        menubar.add_cascade(label="Configurações", menu=settings_menu)
        
        # Menu Ajuda
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Guia do Usuário", command=self.show_help)
        help_menu.add_command(label="Sobre", command=self.show_about)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        
        self.config(menu=menubar)
        
        # Vincular atalhos de teclado
        self.bind("<Control-o>", lambda e: self.browse_file())
        self.bind("<Control-r>", lambda e: self.refresh_ui())
        
    def update_recent_menu(self):
        """Atualiza o menu de arquivos recentes."""
        self.recent_menu.delete(0, tk.END)
        recent_files = self.settings.get("recent_files", [])
        
        if not recent_files:
            self.recent_menu.add_command(label="Nenhum arquivo recente", state=tk.DISABLED)
        else:
            for file_path in recent_files:
                # Exibir apenas o nome do arquivo para economizar espaço
                file_name = os.path.basename(file_path)
                self.recent_menu.add_command(
                    label=file_name,
                    command=lambda fp=file_path: self.load_file(fp)
                )
            
            self.recent_menu.add_separator()
            self.recent_menu.add_command(label="Limpar Arquivos Recentes", 
                                      command=self.clear_recent_files)
        
    def clear_recent_files(self):
        """Limpa a lista de arquivos recentes."""
        self.settings.set("recent_files", [])
        self.update_recent_menu()
        
    def browse_file(self):
        """Abre diálogo de arquivo para selecionar arquivo MusicXML."""
        file_path = filedialog.askopenfilename(
            title="Selecionar Arquivo MusicXML",
            filetypes=[("Arquivos MusicXML", "*.xml;*.musicxml"), ("Todos os arquivos", "*.*")]
        )
        if file_path:
            self.load_file(file_path)
            
    def load_file(self, file_path):
        """Carrega um arquivo MusicXML."""
        if self.busy:
            return
            
        self.busy = True
        self.set_status("Carregando arquivo...")
        self.progress.start()
        
        self.file_path = file_path
        self.file_var.set(file_path)
        
        # Usar threading para evitar congelamento da UI
        threading.Thread(target=self._load_file_thread, args=(file_path,), daemon=True).start()
            
    def _load_file_thread(self, file_path):
        """Função de thread para carregamento de arquivo."""
        try:
            # Adicionar aos arquivos recentes
            self.settings.add_recent_file(file_path)
            
            # Importar aqui para evitar importações circulares
            from music21 import converter, environment
            
            # Configurar music21
            env = environment.Environment()
            env['warnings'] = 0
            
            # Analisar partitura
            score = converter.parse(file_path)
            
            # Converter para nosso modelo de dados
            self.score_data = ScoreParser.parse(score)
            
            # Atualizar UI com informações do arquivo
            self.after(0, lambda: self._update_file_info())
            
            # Atualizar abas de análise
            self.after(0, lambda: self._update_analysis_tabs())
            
            self.after(0, lambda: self.set_status(f"Carregado {os.path.basename(file_path)}"))
            
            # Habilitar opções de menu
            self.after(0, lambda: self._enable_analysis_menu())
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", f"Falha ao carregar arquivo: {e}"))
            self.after(0, lambda: self.set_status(f"Erro ao carregar arquivo", error=True))
            
        finally:
            self.after(0, lambda: self.progress.stop())
            self.after(0, lambda: self.update_recent_menu())
            self.busy = False
            
    def _update_file_info(self):
        """Atualiza a UI com informações do arquivo."""
        if self.score_data:
            self.title_var.set(f"Título: {self.score_data.title}")
            self.composer_var.set(f"Compositor: {self.score_data.composer}")
            self.time_sig_var.set(f"Fórmula de Compasso: {self.score_data.time_signature}")
            self.key_sig_var.set(f"Tonalidade: {self.score_data.key_signature}")
            
            # Mostrar número de partes
            part_count = len(self.score_data.parts)
            self.parts_var.set(f"Partes: {part_count}")
            
    def _update_analysis_tabs(self):
        """Atualiza abas de análise com novos dados de partitura."""
        self.dynamics_tab.update_data(self.score_data)
        self.density_tab.update_data(self.score_data)
        self.spectrum_tab.update_data(self.score_data)
    
    def refresh_ui(self):
        """Limpa o estado atual e prepara a interface para um novo arquivo."""
        if self.busy:
            messagebox.showinfo("Informação", "Aguarde a operação atual terminar antes de atualizar.")
            return
            
        # Confirmar com o usuário apenas se um arquivo foi carregado anteriormente
        if self.file_path and self.score_data:
            if not messagebox.askyesno("Confirmar Atualização", 
                                      "Isso irá limpar os dados carregados. Deseja continuar?"):
                return
        
        # Limpar referências de arquivo
        self.file_path = None
        self.file_var.set("")
        self.score_data = None
        
        # Resetar metadados
        self.title_var.set("Título: ")
        self.composer_var.set("Compositor: ")
        self.time_sig_var.set("Fórmula de Compasso: ")
        self.key_sig_var.set("Tonalidade: ")
        self.parts_var.set("Partes: ")
        
        # Limpar todas as abas de análise
        self.dynamics_tab.clear()
        self.density_tab.clear()
        self.spectrum_tab.clear()
        
        # Atualizar o estado da UI
        self.set_status("Interface atualizada. Selecione um novo arquivo.")
        
        # Desativar botões de análise até que um novo arquivo seja carregado
        try:
            for i in range(self.analysis_menu.index('end') + 1):
                try:
                    self.analysis_menu.entryconfig(i, state='disabled')
                except:
                    pass  # Ignora separadores e outros itens especiais
        except (tk.TclError, AttributeError):
            # Ignorar erro se o menu não estiver inicializado corretamente
            pass
        
        # Focar no botão "Procurar" para facilitar a seleção de um novo arquivo
        self.after(500, lambda: self.show_help_tip())
        
    def show_help_tip(self):
        """Mostra uma dica de ajuda para o usuário após o refresh."""
        messagebox.showinfo("Dica", "Clique em 'Procurar' para selecionar um novo arquivo MusicXML.")
    
    def _enable_analysis_menu(self):
        """Habilita as opções do menu de análise."""
        try:
            for i in range(self.analysis_menu.index('end') + 1):
                try:
                    self.analysis_menu.entryconfig(i, state='normal')
                except:
                    pass  # Ignora separadores e outros itens especiais
        except (tk.TclError, AttributeError):
            # Ignorar erro se o menu não estiver inicializado corretamente
            pass
        
    def run_all_analyses(self):
        """Executa todas as análises sequencialmente."""
        if not self.score_data:
            messagebox.showwarning("Aviso", "Nenhuma partitura carregada")
            return
            
        if self.busy:
            return
            
        self.busy = True
        self.set_status("Executando todas as análises...")
        self.progress.start()
        
        # Usar threading para evitar congelamento da UI
        threading.Thread(target=self._run_all_analyses_thread, daemon=True).start()
            
    def _run_all_analyses_thread(self):
        """Função de thread para executar todas as análises."""
        try:
            # Executar análise de dinâmicas
            self.after(0, lambda: self.set_status("Executando análise de dinâmicas..."))
            self.dynamics_tab.run_analysis()
            
            # Executar análise de densidade
            self.after(0, lambda: self.set_status("Executando análise de densidade..."))
            self.density_tab.run_analysis()
            
            # Executar análise espectral
            self.after(0, lambda: self.set_status("Executando análise espectral..."))
            self.spectrum_tab.run_analysis()
            
            self.after(0, lambda: self.set_status("Todas as análises concluídas"))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", f"Análise falhou: {e}"))
            self.after(0, lambda: self.set_status("Análise falhou", error=True))
            
        finally:
            self.after(0, lambda: self.progress.stop())
            self.busy = False
            
    def set_status(self, message, error=False):
        """Atualiza mensagem de status."""
        self.status_var.set(message)
        if error:
            logger.error(message)
        else:
            logger.info(message)
            
    def change_theme(self, theme_name):
        """Muda o tema da aplicação."""
        self.theme = ThemeManager.apply_theme(self, theme_name)
        self.settings.set("theme", theme_name)
        
    def show_preferences(self):
        """Mostra diálogo de preferências."""
        # Implementar diálogo de preferências aqui
        pref_window = tk.Toplevel(self)
        pref_window.title("Preferências")
        pref_window.geometry("500x400")
        pref_window.transient(self)
        pref_window.grab_set()
        
        # Criar notebook para categorias de configurações
        notebook = ttk.Notebook(pref_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba de análise
        analysis_frame = ttk.Frame(notebook)
        notebook.add(analysis_frame, text="Análise")
        
        # Configurações de densidade
        density_frame = ttk.LabelFrame(analysis_frame, text="Densidade")
        density_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(density_frame, text="Intervalo padrão (centisegundos):").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        interval_var = tk.StringVar(value=str(self.settings.get("analysis.density_interval", DEFAULT_DENSITY_INTERVAL)))
        ttk.Entry(density_frame, textvariable=interval_var, width=10).grid(row=0, column=1, padx=5, pady=2)
        
        # Aba de visualização
        vis_frame = ttk.Frame(notebook)
        notebook.add(vis_frame, text="Visualização")
        
        # Configurações de colormap
        colormap_frame = ttk.LabelFrame(vis_frame, text="Colormap")
        colormap_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(colormap_frame, text="Colormap para espectro:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        colormap_var = tk.StringVar(value=self.settings.get("visualization.colormap", "viridis"))
        ttk.Combobox(colormap_frame, textvariable=colormap_var, values=["viridis", "plasma", "magma", "inferno"]).grid(row=0, column=1, padx=5, pady=2)
        
        # Botões
        btn_frame = ttk.Frame(pref_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="OK", command=lambda: self._save_preferences(
            interval_var.get(),
            colormap_var.get(),
            pref_window
        )).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(btn_frame, text="Cancelar", command=pref_window.destroy).pack(side=tk.RIGHT, padx=5)
        
    def _save_preferences(self, interval, colormap, window):
        """Salva preferências e fecha a janela."""
        try:
            interval_val = float(interval)
            if interval_val <= 0:
                messagebox.showwarning("Aviso", "O intervalo deve ser positivo")
                return
            
            self.settings.set("analysis.density_interval", interval_val)
            self.settings.set("visualization.colormap", colormap)
            
            # Atualizar UI conforme necessário
            self.density_tab.interval_var.set(interval_val)
            
            window.destroy()
            
        except ValueError:
            messagebox.showwarning("Aviso", "Valores inválidos")
        
    def show_help(self):
        """Mostra documentação de ajuda."""
        help_window = tk.Toplevel(self)
        help_window.title("Guia do Usuário")
        help_window.geometry("700x500")
        help_window.transient(self)
        
        # Criar notebook para categorias de ajuda
        notebook = ttk.Notebook(help_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba de introdução
        intro_frame = ttk.Frame(notebook)
        notebook.add(intro_frame, text="Introdução")
        
        intro_text = """
        Bem-vindo ao Analisador MusicXML Aprimorado!
        
        Esta ferramenta permite analisar partituras em formato MusicXML para extrair 
        informações sobre dinâmicas, densidade de notas e distribuição espectral.
        
        Para começar, use o menu Arquivo > Abrir para carregar uma partitura.
        Em seguida, selecione uma das abas de análise para visualizar diferentes aspectos 
        da composição.
        """
        
        ttk.Label(intro_frame, text=intro_text, wraplength=650, justify=tk.LEFT).pack(padx=20, pady=20)
        
        # Aba de análises
        analyses_frame = ttk.Frame(notebook)
        notebook.add(analyses_frame, text="Tipos de Análise")
        
        analyses_text = """
        Tipos de Análise:
        
        1. Dinâmicas - Analisa marcações de dinâmica (p, f, mf, etc.) e calcula a intensidade 
           ao longo do tempo. Inclui uma visualização geral da intensidade sonora da peça.
        
        2. Densidade - Calcula a densidade de notas (quantas notas soam simultaneamente) 
           ao longo do tempo. Útil para identificar seções mais intensas ou mais esparsa.
        
        3. Espectro - Apresenta uma visualização da distribuição de alturas ao longo do tempo, 
           em formato de mapa de calor ou piano roll.
        """
        
        ttk.Label(analyses_frame, text=analyses_text, wraplength=650, justify=tk.LEFT).pack(padx=20, pady=20)
        
        # Fechar
        ttk.Button(help_window, text="Fechar", command=help_window.destroy).pack(pady=10)
        
    def show_about(self):
        """Mostra diálogo sobre."""
        messagebox.showinfo(
            "Sobre", 
            "Analisador MusicXML Aprimorado\nVersão 1.1.0\n\n"
            "Uma ferramenta abrangente para análise e visualização "
            "de partituras musicais em formato MusicXML, com foco em "
            "dinâmica, densidade e análise espectral."
        )
        
    def export_results(self):
        """Exporta resultados de análise."""
        if not self.score_data:
            messagebox.showwarning("Aviso", "Nenhuma partitura carregada")
            return
        
        # Verificar se alguma análise foi executada
        has_analysis = (
            hasattr(self.dynamics_tab, 'result') and self.dynamics_tab.result is not None or
            hasattr(self.density_tab, 'result') and self.density_tab.result is not None or
            hasattr(self.spectrum_tab, 'result') and self.spectrum_tab.result is not None
        )
        
        if not has_analysis:
            messagebox.showwarning("Aviso", "Nenhuma análise executada ainda")
            return
            
        # Criar diálogo para seleção de opções de exportação
        export_window = tk.Toplevel(self)
        export_window.title("Exportar Resultados")
        export_window.geometry("400x350")
        export_window.transient(self)
        export_window.grab_set()
        
        # Frame principal
        main_frame = ttk.Frame(export_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Quais análises exportar
        export_frame = ttk.LabelFrame(main_frame, text="Selecione as análises para exportar")
        export_frame.pack(fill=tk.X, pady=5)
        
        dynamics_var = tk.BooleanVar(value=hasattr(self.dynamics_tab, 'result') and self.dynamics_tab.result is not None)
        density_var = tk.BooleanVar(value=hasattr(self.density_tab, 'result') and self.density_tab.result is not None)
        spectrum_var = tk.BooleanVar(value=hasattr(self.spectrum_tab, 'result') and self.spectrum_tab.result is not None)
        
        ttk.Checkbutton(export_frame, text="Dinâmicas", variable=dynamics_var, 
                       state=tk.NORMAL if dynamics_var.get() else tk.DISABLED).pack(anchor=tk.W, padx=10, pady=2)
        ttk.Checkbutton(export_frame, text="Densidade", variable=density_var, 
                       state=tk.NORMAL if density_var.get() else tk.DISABLED).pack(anchor=tk.W, padx=10, pady=2)
        ttk.Checkbutton(export_frame, text="Espectro", variable=spectrum_var, 
                       state=tk.NORMAL if spectrum_var.get() else tk.DISABLED).pack(anchor=tk.W, padx=10, pady=2)
        
        # Formato de exportação
        format_frame = ttk.LabelFrame(main_frame, text="Formato de exportação")
        format_frame.pack(fill=tk.X, pady=5)
        
        format_var = tk.StringVar(value="png")
        ttk.Radiobutton(format_frame, text="PNG", variable=format_var, value="png").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(format_frame, text="PDF", variable=format_var, value="pdf").pack(anchor=tk.W, padx=10, pady=2)
        ttk.Radiobutton(format_frame, text="SVG", variable=format_var, value="svg").pack(anchor=tk.W, padx=10, pady=2)
        
        # Resolução
        res_frame = ttk.Frame(main_frame)
        res_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(res_frame, text="Resolução (DPI):").pack(side=tk.LEFT, padx=5)
        dpi_var = tk.StringVar(value="300")
        ttk.Entry(res_frame, textvariable=dpi_var, width=6).pack(side=tk.LEFT, padx=5)
        
        # Pasta destino
        dir_frame = ttk.Frame(main_frame)
        dir_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(dir_frame, text="Pasta de destino:").pack(anchor=tk.W, padx=5, pady=2)
        
        dir_path_var = tk.StringVar(value=self.settings.get("export.default_directory", ""))
        dir_entry = ttk.Entry(dir_frame, textvariable=dir_path_var, width=40)
        dir_entry.pack(side=tk.LEFT, padx=5, pady=2, fill=tk.X, expand=True)
        
        ttk.Button(dir_frame, text="...", width=3, 
                  command=lambda: dir_path_var.set(filedialog.askdirectory() or dir_path_var.get())
                 ).pack(side=tk.RIGHT, padx=5, pady=2)
        
        # Botões
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Exportar", 
                  command=lambda: self._do_export(
                      dynamics_var.get(), 
                      density_var.get(), 
                      spectrum_var.get(), 
                      format_var.get(), 
                      int(dpi_var.get()), 
                      dir_path_var.get(),
                      export_window
                  )).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(btn_frame, text="Cancelar", 
                  command=export_window.destroy).pack(side=tk.RIGHT, padx=5)
        
    def _do_export(self, export_dynamics, export_density, export_spectrum, 
                  format_ext, dpi, directory, window):
        """Realiza a exportação dos resultados."""
        try:
            # Validar DPI
            if dpi <= 0:
                messagebox.showwarning("Aviso", "O valor de DPI deve ser positivo")
                return
                
            # Validar diretório
            if not directory:
                directory = os.getcwd()  # Usar diretório atual se não especificado
            
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                
            # Salvar configurações
            self.settings.set("export.default_format", format_ext)
            self.settings.set("export.default_directory", directory)
            self.settings.set("visualization.dpi", dpi)
            
            # Obter nome base do arquivo
            if self.file_path:
                base_name = os.path.splitext(os.path.basename(self.file_path))[0]
            else:
                base_name = "musicxml_analysis"
                
            exported_files = []
            
            # Exportar dinâmicas
            if export_dynamics and hasattr(self.dynamics_tab, 'result') and self.dynamics_tab.result is not None:
                # Criar figuras para exportação
                fig_parts = Figure(figsize=(10, 6), dpi=dpi)
                ax_parts = fig_parts.add_subplot(111)
                plot_dynamics(ax_parts, self.dynamics_tab.result, show_parts=True, show_gradual=True)
                fig_parts.tight_layout()
                
                dynamics_file = os.path.join(directory, f"{base_name}_dynamics.{format_ext}")
                fig_parts.savefig(dynamics_file, dpi=dpi)
                exported_files.append(dynamics_file)
                
                # Curva geral de dinâmica
                fig_combined = Figure(figsize=(10, 6), dpi=dpi)
                ax_combined = fig_combined.add_subplot(111)
                plot_combined_dynamics(ax_combined, self.dynamics_tab.result)
                fig_combined.tight_layout()
                
                combined_file = os.path.join(directory, f"{base_name}_dynamics_combined.{format_ext}")
                fig_combined.savefig(combined_file, dpi=dpi)
                exported_files.append(combined_file)
                
            # Exportar densidade
            if export_density and hasattr(self.density_tab, 'result') and self.density_tab.result is not None:
                fig_density = Figure(figsize=(10, 6), dpi=dpi)
                ax_density = fig_density.add_subplot(111)
                plot_density(ax_density, self.density_tab.result, show_register=True)
                fig_density.tight_layout()
                
                density_file = os.path.join(directory, f"{base_name}_density.{format_ext}")
                fig_density.savefig(density_file, dpi=dpi)
                exported_files.append(density_file)
                
            # Exportar espectro
            if export_spectrum and hasattr(self.spectrum_tab, 'result') and self.spectrum_tab.result is not None:
                # Piano roll
                fig_piano = Figure(figsize=(10, 6), dpi=dpi)
                ax_piano = fig_piano.add_subplot(111)
                plot_spectrum(ax_piano, self.spectrum_tab.result, mode="piano_roll")
                fig_piano.tight_layout()
                
                piano_file = os.path.join(directory, f"{base_name}_spectrum_piano.{format_ext}")
                fig_piano.savefig(piano_file, dpi=dpi)
                exported_files.append(piano_file)
                
                # Mapa de calor
                fig_heatmap = Figure(figsize=(10, 6), dpi=dpi)
                ax_heatmap = fig_heatmap.add_subplot(111)
                plot_spectrum(ax_heatmap, self.spectrum_tab.result, mode="heatmap")
                fig_heatmap.tight_layout()
                
                heatmap_file = os.path.join(directory, f"{base_name}_spectrum_heatmap.{format_ext}")
                fig_heatmap.savefig(heatmap_file, dpi=dpi)
                exported_files.append(heatmap_file)
                
            # Fechar janela de exportação
            window.destroy()
            
            # Mostrar resultado
            if exported_files:
                messagebox.showinfo(
                    "Exportação concluída", 
                    f"Arquivos exportados com sucesso:\n\n{os.path.dirname(exported_files[0])}"
                )
            else:
                messagebox.showinfo("Nenhum arquivo exportado", "Nenhum arquivo foi exportado")
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro na exportação: {e}")

def main():
    """Executa a aplicação aprimorada."""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app = EnhancedMusicXMLAnalyzer()
    app.mainloop()

if __name__ == "__main__":
    main()
