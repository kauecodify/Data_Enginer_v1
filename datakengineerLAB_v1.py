"""
================================================================================
DATAKENGINEERLAB v1.0 — Enterprise Data Analytics Desktop
================================================================================

INSTALAÇÃO:
    pip ou conda install ...
    conda install pandas numpy scikit-learn matplotlib openpyxl scipy
    conda install pyarrow  # opcional para Parquet

USO:
    python datakenengineerLAB.py

v1.0:
    📜 (Estatísticas sem scroll)
    📑 Seleção de Abas Excel → Escolha qual sheet carregar
    🏷️ Coluna ID → Identifica registros (texto ou número)
    🎯 Filtro Duplo → Colunas + Linhas nas estatísticas

FUNCIONALIDADES:
    📊 Dados & Preview  → Importa Excel/CSV, visualiza, gerencia tabelas
    ⭐ Rating ML         → Score ponderado com heatmap de cores
    📈 Estatísticas      → Filtros completos
    🔧 Engenharia        → Join entre tabelas + SQL engine em memória

EXPORTAÇÃO:
    💾 Salvar em: CSV, Excel (.xlsx), Parquet, JSON

AUTOR: K. Caires
VERSÃO: 1.0
================================================================================
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
import sqlite3
import threading
import os
import logging
import json
from datetime import datetime

from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LinearRegression
from scipy.stats import skew, kurtosis, zscore
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# =======================
# CONFIGURAÇÕES GERAIS
# =======================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

THEME = {
    "bg": "#121212",
    "panel": "#1e1e1e",
    "fg": "#e0e0e0",
    "accent": "#00e676",
    "accent_dark": "#00b359",
    "border": "#333333",
    "error": "#cf6679",
    "text_field": "#2c2c2c",
    "warning": "#ff9800"
}

# =======================
# GERENCIADOR DE DADOS
# =======================
class DataManager:
    def __init__(self):
        self.tables = {}
        self.active_table = None
        self.file_sheets = {}

    def load_file(self, path, sheet_name=None):
        try:
            if path.endswith(".csv"):
                df = pd.read_csv(path)
                table_name = f"{os.path.basename(path)}_{datetime.now().strftime('%H%M%S')}"
                self.tables[table_name] = df
                self.active_table = table_name
                return True, table_name, []
            else:
                excel_file = pd.ExcelFile(path)
                sheet_names = excel_file.sheet_names
                
                if sheet_name is None:
                    sheet_name = sheet_names[0]
                
                df = pd.read_excel(path, sheet_name=sheet_name)
                base_name = os.path.basename(path)
                
                if len(sheet_names) > 1:
                    table_name = f"{base_name}_{sheet_name}_{datetime.now().strftime('%H%M%S')}"
                else:
                    table_name = f"{base_name}_{datetime.now().strftime('%H%M%S')}"
                
                self.file_sheets[table_name] = {
                    "path": path,
                    "sheets": sheet_names,
                    "current_sheet": sheet_name
                }
                
                self.tables[table_name] = df
                self.active_table = table_name
                return True, table_name, sheet_names
        except Exception as e:
            return False, str(e), []

    def get_active_df(self):
        if self.active_table and self.active_table in self.tables:
            return self.tables[self.active_table]
        return None

    def add_table(self, name, df):
        self.tables[name] = df
        self.active_table = name

# =======================
# UTILITÁRIOS VISUAIS
# =======================
def score_to_color(score, alpha=0.6):
    score = max(0, min(100, score))
    if score < 50:
        r, g = 255, int(255 * (score / 50))
    else:
        r, g = int(255 * (1 - (score - 50) / 50)), 255
    b = 0
    r = int(r * alpha + 30 * (1 - alpha))
    g = int(g * alpha + 30 * (1 - alpha))
    b = int(b * alpha + 30 * (1 - alpha))
    return f'#{r:02x}{g:02x}{b:02x}'

class LoggerPanel(tk.Text):
    def __init__(self, parent):
        super().__init__(parent, height=6, bg=THEME["panel"], fg=THEME["fg"], 
                         font=("Consolas", 9), state='disabled', borderwidth=0)
        self.tag_config("INFO", foreground="#4fc3f7")
        self.tag_config("SUCCESS", foreground=THEME["accent"])
        self.tag_config("ERROR", foreground=THEME["error"])
        self.tag_config("WARNING", foreground=THEME["warning"])
    
    def log(self, message, level="INFO"):
        self.configure(state='normal')
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.insert(tk.END, f"[{timestamp}] {level}: {message}\n", level)
        self.see(tk.END)
        self.configure(state='disabled')

# =======================
# DIÁLOGO DE SELEÇÃO DE SHEET
# =======================
class SheetSelectorDialog:
    def __init__(self, parent, sheet_names, file_path):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("📑 Selecionar Aba do Excel")
        self.dialog.geometry("500x400")
        self.dialog.configure(bg=THEME["bg"])
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        tk.Label(self.dialog, text=f"Arquivo: {os.path.basename(file_path)}", 
                bg=THEME["bg"], fg=THEME["fg"], font=("Segoe UI", 11, "bold")).pack(pady=10)
        tk.Label(self.dialog, text=f"Encontradas {len(sheet_names)} abas. Selecione uma:", 
                bg=THEME["bg"], fg=THEME["fg"]).pack(pady=5)
        
        list_frame = tk.Frame(self.dialog, bg=THEME["panel"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.sheet_list = tk.Listbox(list_frame, bg=THEME["text_field"], fg=THEME["fg"], 
                                     selectbackground=THEME["accent"], selectforeground="black",
                                     font=("Consolas", 10), height=10)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.sheet_list.yview)
        self.sheet_list.configure(yscrollcommand=scrollbar.set)
        
        for sheet in sheet_names:
            self.sheet_list.insert(tk.END, f"📄 {sheet}")
        
        self.sheet_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        btn_frame = tk.Frame(self.dialog, bg=THEME["bg"])
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(btn_frame, text="✅ Carregar Selecionada", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ Cancelar", command=self.on_cancel).pack(side=tk.RIGHT, padx=5)
        
        if sheet_names:
            self.sheet_list.selection_set(0)
        
        self.dialog.wait_window()
    
    def on_ok(self):
        sel = self.sheet_list.curselection()
        if sel:
            sheet_name = self.sheet_list.get(sel[0]).replace("📄 ", "")
            self.result = sheet_name
        self.dialog.destroy()
    
    def on_cancel(self):
        self.result = None
        self.dialog.destroy()

# =======================
# APLICAÇÃO PRINCIPAL
# =======================
class DataKenEngineerLab:
    def __init__(self, root):
        self.root = root
        self.root.title("DATAKENGINEERLAB v1.0 — Enterprise Edition")
        self.root.geometry("1400x850")
        self.root.configure(bg=THEME["bg"])
        
        self.dm = DataManager()
        self.stats_col_vars = {}
        self.stats_selected_cols = []
        self.row_filter_mode = tk.StringVar(value="all")
        self.row_filter_entries = {}
        self.row_count_lbl = None
        self.id_column_var = tk.StringVar(value="")
        
        self._setup_styles()
        self._setup_ui()
        self._setup_menu()
        
        self.logger = LoggerPanel(self.root)
        self.logger.pack(side=tk.BOTTOM, fill=tk.X)
        self.logger.log("Sistema inicializado. Aguardando dados...", "SUCCESS")
        
        self.status_var = tk.StringVar(value="Pronto")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, 
                                   relief=tk.SUNKEN, anchor=tk.W, bg=THEME["panel"], fg=THEME["fg"])
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background=THEME["bg"])
        style.configure("TLabel", background=THEME["bg"], foreground=THEME["fg"], font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=5)
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=6)
        style.map("TButton", background=[("active", THEME["accent"])])
        style.configure("Treeview", background=THEME["panel"], fieldbackground=THEME["panel"], 
                        foreground=THEME["fg"], rowheight=25, borderwidth=0)
        style.configure("Treeview.Heading", background=THEME["border"], foreground=THEME["fg"], 
                        font=("Segoe UI", 10, "bold"), padding=5)
        style.configure("TNotebook", background=THEME["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=THEME["panel"], foreground=THEME["fg"], 
                        padding=[15, 5], font=("Segoe UI", 11, "bold"))
        style.map("TNotebook.Tab", background=[("selected", THEME["border"])])

    def _setup_ui(self):
        header = tk.Frame(self.root, bg=THEME["panel"], height=50)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        tk.Label(header, text="DATAKENGINEERLAB v1.0", font=("Segoe UI", 16, "bold"), 
                 bg=THEME["panel"], fg=THEME["accent"]).pack(side=tk.LEFT, padx=20)
        save_btn = tk.Button(header, text="💾 Salvar Dados", bg=THEME["accent_dark"], 
                            fg="black", font=("Segoe UI", 10, "bold"), 
                            command=self.save_data, cursor="hand2", relief=tk.FLAT)
        save_btn.pack(side=tk.RIGHT, padx=10, pady=8)
        save_btn.bind("<Enter>", lambda e: save_btn.config(bg=THEME["accent"]))
        save_btn.bind("<Leave>", lambda e: save_btn.config(bg=THEME["accent_dark"]))
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tab_data = ttk.Frame(self.notebook)
        self.tab_rating = ttk.Frame(self.notebook)
        self.tab_stats = ttk.Frame(self.notebook)
        self.tab_engine = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_data, text="📊 Dados & Preview")
        self.notebook.add(self.tab_rating, text="⭐ Rating ML")
        self.notebook.add(self.tab_stats, text="📈 Estatísticas")
        self.notebook.add(self.tab_engine, text="🔧 Engenharia (Join/SQL)")
        self._build_data_tab()
        self._build_rating_tab()
        self._build_stats_tab()
        self._build_engine_tab()

    def _setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="📂 Importar Arquivo", command=self.load_file_thread)
        file_menu.add_command(label="💾 Salvar Como...", command=self.save_data)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.quit)
        menubar.add_cascade(label="Arquivo", menu=file_menu)

    # =======================
    # SALVAMENTO UNIVERSAL
    # =======================
    def save_data(self):
        df = self.dm.get_active_df()
        if df is None:
            messagebox.showwarning("Aviso", "Nenhuma tabela selecionada para salvar.")
            self.logger.log("Nenhuma tabela para exportar.", "ERROR")
            return
        filetypes = [("CSV", "*.csv"), ("Excel", "*.xlsx"), ("Parquet", "*.parquet"), ("JSON", "*.json"), ("Todos", "*.*")]
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=filetypes,
                                            initialfile=f"{self.dm.active_table}_export", title="Salvar Dados")
        if not path: return
        def task():
            try:
                self.status_var.set("Salvando arquivo...")
                if path.endswith(".csv"):
                    df.to_csv(path, index=False, encoding='utf-8-sig')
                elif path.endswith(".xlsx"):
                    df.to_excel(path, index=False, engine='openpyxl')
                elif path.endswith(".parquet"):
                    df.to_parquet(path, index=False, engine='pyarrow')
                elif path.endswith(".json"):
                    df_json = df.copy()
                    for col in df_json.select_dtypes(include=[np.datetime64]).columns:
                        df_json[col] = df_json[col].astype(str)
                    df_json.to_json(path, orient='records', force_ascii=False, indent=2)
                else:
                    df.to_csv(path, index=False, encoding='utf-8-sig')
                file_size = os.path.getsize(path) / 1024
                self.root.after(0, lambda: self.logger.log(f"Arquivo salvo: {os.path.basename(path)} ({file_size:.1f} KB)", "SUCCESS"))
                self.root.after(0, lambda: self.status_var.set(f"Salvo: {os.path.basename(path)}"))
            except ImportError:
                self.root.after(0, lambda: self.logger.log("Biblioteca faltando: pip install openpyxl ou pyarrow", "ERROR"))
                self.root.after(0, lambda: messagebox.showerror("Erro de Dependência", "Excel: pip install openpyxl\nParquet: pip install pyarrow"))
            except Exception as e:
                self.root.after(0, lambda: self.logger.log(f"Erro ao salvar: {str(e)}", "ERROR"))
                self.root.after(0, lambda: self.status_var.set("Erro ao salvar"))
        threading.Thread(target=task, daemon=True).start()

    # =======================
    # TAB 1: DADOS & PREVIEW
    # =======================
    def _build_data_tab(self):
        left = tk.Frame(self.tab_data, bg=THEME["bg"], width=250)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        left.pack_propagate(False)
        ttk.Button(left, text="📂 Importar Excel/CSV", command=self.load_file_thread).pack(fill=tk.X, pady=5)
        ttk.Button(left, text="💾 Exportar Esta Tabela", command=self.save_data).pack(fill=tk.X, pady=5)
        tk.Label(left, text="Tabelas Carregadas:", bg=THEME["bg"], fg=THEME["fg"]).pack(pady=(10,5))
        self.table_list = tk.Listbox(left, bg=THEME["text_field"], fg=THEME["fg"], 
                                     selectbackground=THEME["accent"], selectforeground="black", 
                                     font=("Consolas", 9), highlightthickness=0)
        self.table_list.pack(fill=tk.BOTH, expand=True)
        self.table_list.bind('<<ListboxSelect>>', self.on_table_select)
        right = tk.Frame(self.tab_data, bg=THEME["bg"])
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.info_lbl = tk.Label(right, text="Nenhum dado selecionado", bg=THEME["bg"], 
                                 fg=THEME["fg"], anchor="w", font=("Segoe UI", 10))
        self.info_lbl.pack(fill=tk.X, pady=(0, 5))
        tree_frame = ttk.Frame(right)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        self.preview_tree = ttk.Treeview(tree_frame)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.preview_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.preview_tree.xview)
        self.preview_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

    def load_file_thread(self):
        path = filedialog.askopenfilename(filetypes=[("Arquivos", "*.xlsx *.xls *.csv")])
        if not path: return
        def task():
            try:
                if path.endswith(".csv"):
                    success, result, sheet_names = self.dm.load_file(path)
                else:
                    excel_file = pd.ExcelFile(path)
                    sheet_names = excel_file.sheet_names
                    excel_file.close()
                    
                    if len(sheet_names) > 1:
                        self.root.after(0, lambda: self._show_sheet_selector(path, sheet_names))
                        return
                    else:
                        success, result, sheet_names = self.dm.load_file(path)
                
                if success:
                    self.root.after(0, lambda: self.logger.log(f"Arquivo carregado: {result}", "SUCCESS"))
                    self.root.after(0, self.refresh_table_list)
                    self.root.after(0, self.update_preview)
                    self.root.after(0, self.update_engine_combos)
                    self.root.after(0, self.refresh_stats_columns)
                    self.root.after(0, self.refresh_row_filter)
                    self.root.after(0, self.refresh_id_column_selector)
                else:
                    self.root.after(0, lambda: self.logger.log(f"Erro: {result}", "ERROR"))
            except Exception as e:
                self.root.after(0, lambda: self.logger.log(f"Erro: {str(e)}", "ERROR"))
        threading.Thread(target=task, daemon=True).start()

    def _show_sheet_selector(self, path, sheet_names):
        dialog = SheetSelectorDialog(self.root, sheet_names, path)
        if dialog.result:
            def load_selected():
                success, result, _ = self.dm.load_file(path, sheet_name=dialog.result)
                if success:
                    self.logger.log(f"Sheet '{dialog.result}' carregada: {result}", "SUCCESS")
                    self.refresh_table_list()
                    self.update_preview()
                    self.update_engine_combos()
                    self.refresh_stats_columns()
                    self.refresh_row_filter()
                    self.refresh_id_column_selector()
                else:
                    self.logger.log(f"Erro: {result}", "ERROR")
            threading.Thread(target=load_selected, daemon=True).start()
        else:
            self.logger.log("Seleção de sheet cancelada.", "INFO")

    def refresh_table_list(self):
        self.table_list.delete(0, tk.END)
        for name in self.dm.tables.keys():
            sheet_info = self.dm.file_sheets.get(name, {})
            sheets = sheet_info.get("sheets", [])
            icon = "📑" if len(sheets) > 1 else "📄"
            self.table_list.insert(tk.END, f"{icon} {name}")
        if self.dm.active_table:
            try:
                idx = list(self.dm.tables.keys()).index(self.dm.active_table)
                self.table_list.selection_set(idx)
                self.table_list.see(idx)
            except: pass

    def on_table_select(self, event):
        sel = self.table_list.curselection()
        if sel:
            name = self.table_list.get(sel[0]).replace("📑 ", "").replace("📄 ", "")
            for table_name in self.dm.tables.keys():
                if name in table_name or table_name in name:
                    self.dm.active_table = table_name
                    break
            self.update_preview()
            self.refresh_stats_columns()
            self.refresh_row_filter()
            self.refresh_id_column_selector()

    def update_preview(self):
        df = self.dm.get_active_df()
        if df is None: return
        rows, cols = df.shape
        mem = df.memory_usage(deep=True).sum() / 1024 ** 2
        sheet_info = self.dm.file_sheets.get(self.dm.active_table, {})
        sheets = sheet_info.get("sheets", [])
        current_sheet = sheet_info.get("current_sheet", "")
        sheet_text = f" | Sheet: {current_sheet}/{len(sheets)}" if len(sheets) > 1 else ""
        self.info_lbl.config(text=f"Tabela: {self.dm.active_table} | Linhas: {rows} | Colunas: {cols} | Mem: {mem:.2f} MB{sheet_text}")
        self.preview_tree.delete(*self.preview_tree.get_children())
        self.preview_tree["columns"] = list(df.columns)
        self.preview_tree["show"] = "headings"
        for col in df.columns:
            self.preview_tree.heading(col, text=str(col))
            self.preview_tree.column(col, width=100, anchor="center")
        for _, row in df.head(100).iterrows():
            self.preview_tree.insert("", tk.END, values=list(row))

    # =======================
    # TAB 2: RATING ML
    # =======================
    def _build_rating_tab(self):
        cfg = ttk.LabelFrame(self.tab_rating, text="Configuração do Score", padding=10)
        cfg.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        tk.Label(cfg, text="Colunas para Peso:", bg=THEME["bg"], fg=THEME["fg"]).pack(anchor=tk.W)
        self.rating_cols_canvas = tk.Canvas(cfg, bg=THEME["panel"], height=150, highlightthickness=0)
        self.rating_cols_canvas.pack(fill=tk.X, pady=5)
        self.rating_cols_frame = tk.Frame(self.rating_cols_canvas, bg=THEME["panel"])
        self.rating_cols_scrollbar = ttk.Scrollbar(cfg, orient="vertical", command=self.rating_cols_canvas.yview)
        self.rating_cols_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.rating_cols_frame.bind("<Configure>", lambda e: self.rating_cols_canvas.configure(scrollregion=self.rating_cols_canvas.bbox("all")))
        self.rating_cols_canvas.create_window((0, 0), window=self.rating_cols_frame, anchor="nw")
        self.rating_cols_canvas.configure(yscrollcommand=self.rating_cols_scrollbar.set)
        self.rating_vars = {}
        tk.Label(cfg, text="Peso Global (0-1):", bg=THEME["bg"], fg=THEME["fg"]).pack(anchor=tk.W)
        self.rating_weight_scale = ttk.Scale(cfg, from_=0.1, to=1.0, orient=tk.HORIZONTAL)
        self.rating_weight_scale.set(1.0)
        self.rating_weight_scale.pack(fill=tk.X, pady=5)
        ttk.Button(cfg, text="🔄 Atualizar Colunas", command=self.refresh_rating_cols).pack(fill=tk.X, pady=5)
        ttk.Button(cfg, text="🚀 Calcular Rating", command=self.calculate_rating_thread, style="Accent.TButton").pack(fill=tk.X, pady=20)
        ttk.Button(cfg, text="💾 Salvar Resultado", command=self.save_data).pack(fill=tk.X, pady=5)
        res = ttk.LabelFrame(self.tab_rating, text="Resultado (Heatmap)", padding=10)
        res.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.rating_tree = ttk.Treeview(res)
        vsb = ttk.Scrollbar(res, orient="vertical", command=self.rating_tree.yview)
        self.rating_tree.configure(yscrollcommand=vsb.set)
        self.rating_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def refresh_rating_cols(self):
        for widget in self.rating_cols_frame.winfo_children():
            widget.destroy()
        self.rating_vars = {}
        df = self.dm.get_active_df()
        if df is None: return
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        for col in num_cols:
            var = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(self.rating_cols_frame, text=col, variable=var)
            cb.pack(anchor=tk.W)
            self.rating_vars[col] = var

    def calculate_rating_thread(self):
        df = self.dm.get_active_df()
        if df is None:
            messagebox.showwarning("Aviso", "Selecione uma tabela na aba Dados.")
            return
        selected_cols = [c for c, v in self.rating_vars.items() if v.get()]
        if not selected_cols:
            messagebox.showwarning("Aviso", "Selecione pelo menos uma coluna numérica.")
            return
        def task():
            try:
                subset = df[selected_cols].copy().fillna(0)
                scaler = MinMaxScaler((0, 100))
                scaled_data = scaler.fit_transform(subset)
                weights = np.ones(len(selected_cols)) / len(selected_cols)
                scores = np.dot(scaled_data, weights)
                df_result = df.copy()
                df_result["Score_Rating"] = scores.round(2)
                df_result = df_result.sort_values(by="Score_Rating", ascending=False)
                self.root.after(0, lambda: self.render_rating_table(df_result, selected_cols))
                self.root.after(0, lambda: self.logger.log("Rating calculado com sucesso.", "SUCCESS"))
                self.dm.add_table(f"Rating_{datetime.now().strftime('%H%M%S')}", df_result)
                self.root.after(0, self.refresh_table_list)
            except Exception as e:
                self.root.after(0, lambda: self.logger.log(f"Erro no Rating: {str(e)}", "ERROR"))
        threading.Thread(target=task, daemon=True).start()

    def render_rating_table(self, df, cols):
        self.rating_tree.delete(*self.rating_tree.get_children())
        display_cols = cols + ["Score_Rating"]
        self.rating_tree["columns"] = display_cols
        self.rating_tree["show"] = "headings"
        for c in display_cols:
            self.rating_tree.heading(c, text=c)
            self.rating_tree.column(c, width=100, anchor="center")
        mean_score = df["Score_Rating"].mean()
        std_score = df["Score_Rating"].std() or 1
        for i, row in df.iterrows():
            score = row["Score_Rating"]
            alpha = min(abs(score - mean_score) / (std_score * 2), 1)
            color = score_to_color(score, alpha=0.8)
            tag = f"row_{i}"
            self.rating_tree.tag_configure(tag, background=color, foreground="white" if score < 40 else "black")
            values = [row[c] for c in display_cols]
            self.rating_tree.insert("", tk.END, values=values, tags=(tag,))

    # =======================
    # TAB 3: ESTATÍSTICAS ✅ COM SCROLL EM TODOS PAINÉIS
    # =======================
    def _build_stats_tab(self):
        ctrl = tk.Frame(self.tab_stats, bg=THEME["bg"])
        ctrl.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        # === COLUNA ID ===
        id_frame = ttk.LabelFrame(ctrl, text="🏷️ Coluna ID (Identificador)", padding=10)
        id_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(id_frame, text="Selecione coluna para identificar registros:", 
                bg=THEME["bg"], fg=THEME["fg"]).pack(anchor=tk.W)
        self.id_column_combo = ttk.Combobox(id_frame, state="readonly", width=30)
        self.id_column_combo.pack(fill=tk.X, pady=5)
        self.id_column_combo.bind("<<ComboboxSelected>>", lambda e: self._on_id_column_selected())
        id_info_frame = tk.Frame(id_frame, bg=THEME["bg"])
        id_info_frame.pack(fill=tk.X, pady=5)
        tk.Label(id_info_frame, text="✅ Aceita texto ou número", 
                bg=THEME["bg"], fg=THEME["accent"], font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=5)
        tk.Label(id_info_frame, text="• Ex: CPF, Código, Nome, Email", 
                bg=THEME["bg"], fg=THEME["warning"], font=("Segoe UI", 8)).pack(side=tk.LEFT)
        
        # === FILTRO DE COLUNAS COM SCROLL ===
        col_filter_frame = ttk.LabelFrame(ctrl, text="🔍 Filtrar COLUNAS (numéricas)", padding=10)
        col_filter_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(col_filter_frame, text="Selecione colunas para análise:", bg=THEME["bg"], fg=THEME["fg"]).pack(anchor=tk.W)
        self.stats_cols_canvas = tk.Canvas(col_filter_frame, bg=THEME["panel"], height=120, highlightthickness=0)
        self.stats_cols_canvas.pack(fill=tk.X, pady=5)
        self.stats_cols_frame = tk.Frame(self.stats_cols_canvas, bg=THEME["panel"])
        self.stats_cols_scrollbar = ttk.Scrollbar(col_filter_frame, orient="vertical", command=self.stats_cols_canvas.yview)
        self.stats_cols_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.stats_cols_frame.bind("<Configure>", lambda e: self.stats_cols_canvas.configure(scrollregion=self.stats_cols_canvas.bbox("all")))
        self.stats_cols_canvas.create_window((0, 0), window=self.stats_cols_frame, anchor="nw")
        self.stats_cols_canvas.configure(yscrollcommand=self.stats_cols_scrollbar.set)
        btn_frame = tk.Frame(col_filter_frame, bg=THEME["bg"])
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="✅ Todas", command=lambda: self._set_all_stats_cols(True), width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="❌ Nenhuma", command=lambda: self._set_all_stats_cols(False), width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🔄 Atualizar", command=self.refresh_stats_columns, width=12).pack(side=tk.RIGHT)
        
        # === FILTRO DE LINHAS ===
        row_filter_frame = ttk.LabelFrame(ctrl, text="🎯 Filtrar LINHAS", padding=10)
        row_filter_frame.pack(fill=tk.X, pady=(0, 10))
        mode_frame = tk.Frame(row_filter_frame, bg=THEME["bg"])
        mode_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Radiobutton(mode_frame, text="📋 Todas", variable=self.row_filter_mode, value="all", 
                      bg=THEME["bg"], fg=THEME["fg"], selectcolor=THEME["panel"], 
                      command=self._toggle_row_filter_ui).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="🔢 Por Índice", variable=self.row_filter_mode, value="index", 
                      bg=THEME["bg"], fg=THEME["fg"], selectcolor=THEME["panel"], 
                      command=self._toggle_row_filter_ui).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="🔤 Por Valor", variable=self.row_filter_mode, value="value", 
                      bg=THEME["bg"], fg=THEME["fg"], selectcolor=THEME["panel"], 
                      command=self._toggle_row_filter_ui).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="🎲 Amostra", variable=self.row_filter_mode, value="sample", 
                      bg=THEME["bg"], fg=THEME["fg"], selectcolor=THEME["panel"], 
                      command=self._toggle_row_filter_ui).pack(side=tk.LEFT, padx=10)
        self.row_count_lbl = tk.Label(row_filter_frame, text="Linhas: 0 (selecione uma tabela)", 
                                     bg=THEME["panel"], fg=THEME["fg"], font=("Segoe UI", 9))
        self.row_count_lbl.pack(fill=tk.X, pady=(5, 0))
        self.row_filter_ui_frame = tk.Frame(row_filter_frame, bg=THEME["bg"])
        self.row_filter_ui_frame.pack(fill=tk.X, pady=5)
        self._toggle_row_filter_ui()
        
        stats_frame = ttk.LabelFrame(ctrl, text="📊 Análises", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_btns_canvas = tk.Canvas(stats_frame, bg=THEME["panel"], height=180, highlightthickness=0)
        self.stats_btns_canvas.pack(fill=tk.X, pady=5)
        
        self.stats_btns_frame = tk.Frame(self.stats_btns_canvas, bg=THEME["panel"])
        self.stats_btns_scrollbar = ttk.Scrollbar(stats_frame, orient="vertical", command=self.stats_btns_canvas.yview)
        self.stats_btns_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.stats_btns_frame.bind("<Configure>", lambda e: self.stats_btns_canvas.configure(scrollregion=self.stats_btns_canvas.bbox("all")))
        self.stats_btns_canvas.create_window((0, 0), window=self.stats_btns_frame, anchor="nw")
        self.stats_btns_canvas.configure(yscrollcommand=self.stats_btns_scrollbar.set)
        
        stats_btns = [
            ("📊 Descritivas", self.run_desc_stats),
            ("🔗 Correlação", self.run_correlation),
            ("🚨 Outliers IQR", self.run_outliers_iqr),
            ("🚨 Outliers Z-Score", self.run_outliers_z),
            ("📈 Regressão Linear", self.run_regression),
        ]
        
        for text, cmd in stats_btns:
            ttk.Button(self.stats_btns_frame, text=text, command=cmd).pack(fill=tk.X, pady=3, padx=5)
        
        ttk.Button(ctrl, text="💾 Salvar Stats", command=self.save_data).pack(fill=tk.X, pady=20)
        
        # === ÁREA DE VISUALIZAÇÃO ===
        self.stats_canvas_frame = tk.Frame(self.tab_stats, bg=THEME["bg"])
        self.stats_canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(self.stats_canvas_frame, text="Selecione tabela → defina ID → filtre colunas E linhas → clique na análise", 
                 bg=THEME["bg"], fg=THEME["fg"], font=("Segoe UI", 11)).pack(pady=20)

    def refresh_id_column_selector(self):
        df = self.dm.get_active_df()
        if df is None:
            self.id_column_combo["values"] = []
            self.id_column_var.set("")
            return
        all_cols = df.columns.tolist()
        self.id_column_combo["values"] = ["(nenhum)"] + all_cols
        id_candidates = [c for c in all_cols if c.lower() in ['id', 'codigo', 'código', 'cpf', 'cnpj', 'nome', 'email', 'chave', 'key']]
        if id_candidates:
            self.id_column_combo.set(id_candidates[0])
            self.id_column_var.set(id_candidates[0])
        else:
            self.id_column_combo.set("(nenhum)")
            self.id_column_var.set("")

    def _on_id_column_selected(self):
        selected = self.id_column_combo.get()
        if selected == "(nenhum)":
            self.id_column_var.set("")
        else:
            self.id_column_var.set(selected)
        self.logger.log(f"Coluna ID definida: {selected}", "INFO")

    def _toggle_row_filter_ui(self):
        for widget in self.row_filter_ui_frame.winfo_children():
            widget.destroy()
        self.row_filter_entries = {}
        mode = self.row_filter_mode.get()
        df = self.dm.get_active_df()
        if mode == "all":
            tk.Label(self.row_filter_ui_frame, text="✓ Todas as linhas serão analisadas", 
                    bg=THEME["bg"], fg=THEME["accent"], font=("Segoe UI", 9, "italic")).pack(pady=5)
        elif mode == "index":
            idx_frame = tk.Frame(self.row_filter_ui_frame, bg=THEME["bg"])
            idx_frame.pack(fill=tk.X, pady=5)
            tk.Label(idx_frame, text="Índice:", bg=THEME["bg"], fg=THEME["fg"]).pack(side=tk.LEFT)
            self.row_filter_entries["index_from"] = ttk.Entry(idx_frame, width=8)
            self.row_filter_entries["index_from"].pack(side=tk.LEFT, padx=5)
            tk.Label(idx_frame, text="até", bg=THEME["bg"], fg=THEME["fg"]).pack(side=tk.LEFT)
            self.row_filter_entries["index_to"] = ttk.Entry(idx_frame, width=8)
            self.row_filter_entries["index_to"].pack(side=tk.LEFT, padx=5)
            tk.Label(idx_frame, text="(deixa vazio para até o fim)", bg=THEME["bg"], fg=THEME["warning"], font=("Segoe UI", 8)).pack(fill=tk.X, pady=(5,0))
            if df is not None:
                self.row_filter_entries["index_from"].insert(0, "0")
                self.row_filter_entries["index_to"].insert(0, str(len(df)))
        elif mode == "value":
            val_frame = tk.Frame(self.row_filter_ui_frame, bg=THEME["bg"])
            val_frame.pack(fill=tk.X, pady=5)
            tk.Label(val_frame, text="Coluna:", bg=THEME["bg"], fg=THEME["fg"]).pack(side=tk.LEFT)
            self.row_filter_entries["value_col"] = ttk.Combobox(val_frame, width=15, state="readonly")
            self.row_filter_entries["value_col"].pack(side=tk.LEFT, padx=5)
            if df is not None:
                cols = df.select_dtypes(include=[np.number, 'object', 'bool']).columns.tolist()
                self.row_filter_entries["value_col"]["values"] = cols
                if cols: self.row_filter_entries["value_col"].set(cols[0])
            tk.Label(val_frame, text="Operador:", bg=THEME["bg"], fg=THEME["fg"]).pack(side=tk.LEFT, padx=(10,0))
            self.row_filter_entries["value_op"] = ttk.Combobox(val_frame, values=["==", "!=", ">", "<", ">=", "<=", "contains"], width=8, state="readonly")
            self.row_filter_entries["value_op"].pack(side=tk.LEFT, padx=5)
            self.row_filter_entries["value_op"].set("==")
            tk.Label(val_frame, text="Valor:", bg=THEME["bg"], fg=THEME["fg"]).pack(side=tk.LEFT, padx=(10,0))
            self.row_filter_entries["value_val"] = ttk.Entry(val_frame, width=15)
            self.row_filter_entries["value_val"].pack(side=tk.LEFT, padx=5)
            tk.Label(val_frame, text="Ex: status == 'ativo'", bg=THEME["bg"], fg=THEME["warning"], font=("Segoe UI", 8)).pack(fill=tk.X, pady=(5,0))
        elif mode == "sample":
            samp_frame = tk.Frame(self.row_filter_ui_frame, bg=THEME["bg"])
            samp_frame.pack(fill=tk.X, pady=5)
            tk.Label(samp_frame, text="Tamanho:", bg=THEME["bg"], fg=THEME["fg"]).pack(side=tk.LEFT)
            self.row_filter_entries["sample_n"] = ttk.Spinbox(samp_frame, from_=1, to=10000, width=8)
            self.row_filter_entries["sample_n"].pack(side=tk.LEFT, padx=5)
            self.row_filter_entries["sample_n"].set("100")
            tk.Label(samp_frame, text="linhas", bg=THEME["bg"], fg=THEME["fg"]).pack(side=tk.LEFT)
            tk.Label(samp_frame, text="| Aleatorizar:", bg=THEME["bg"], fg=THEME["fg"]).pack(side=tk.LEFT, padx=(15,0))
            self.row_filter_entries["sample_random"] = tk.BooleanVar(value=True)
            tk.Checkbutton(samp_frame, variable=self.row_filter_entries["sample_random"], bg=THEME["bg"], 
                          activebackground=THEME["bg"], selectcolor=THEME["panel"]).pack(side=tk.LEFT)
            tk.Label(samp_frame, text="Ex: 100 linhas aleatórias", bg=THEME["bg"], fg=THEME["warning"], font=("Segoe UI", 8)).pack(fill=tk.X, pady=(5,0))
        self._update_row_count_label()

    def refresh_stats_columns(self):
        for widget in self.stats_cols_frame.winfo_children():
            widget.destroy()
        self.stats_col_vars = {}
        df = self.dm.get_active_df()
        if df is None:
            tk.Label(self.stats_cols_frame, text="⚠️ Selecione uma tabela primeiro", 
                    bg=THEME["panel"], fg=THEME["error"], font=("Segoe UI", 9)).pack(pady=10)
            return
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not num_cols:
            tk.Label(self.stats_cols_frame, text="⚠️ Sem colunas numéricas", 
                    bg=THEME["panel"], fg=THEME["error"], font=("Segoe UI", 9)).pack(pady=10)
            return
        for col in num_cols:
            var = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(self.stats_cols_frame, text=col, variable=var)
            cb.pack(anchor=tk.W, pady=1)
            self.stats_col_vars[col] = var
        self._update_selected_stats_cols()

    def refresh_row_filter(self):
        self._toggle_row_filter_ui()
        self._update_row_count_label()

    def _set_all_stats_cols(self, value):
        for var in self.stats_col_vars.values():
            var.set(value)
        self._update_selected_stats_cols()

    def _update_selected_stats_cols(self):
        self.stats_selected_cols = [c for c, v in self.stats_col_vars.items() if v.get()]

    def _get_entry_value(self, key, default=""):
        widget = self.row_filter_entries.get(key)
        if widget is None:
            return default
        if isinstance(widget, (ttk.Entry, tk.Entry)):
            return widget.get() or default
        elif isinstance(widget, ttk.Combobox):
            return widget.get() or default
        elif isinstance(widget, ttk.Spinbox):
            return widget.get() or default
        elif isinstance(widget, tk.BooleanVar):
            return widget.get()
        return default

    def _apply_row_filter(self, df):
        if df is None or df.empty:
            return df
        mode = self.row_filter_mode.get()
        if mode == "all":
            return df.copy()
        elif mode == "index":
            try:
                from_idx = int(self._get_entry_value("index_from", "0"))
                to_val = self._get_entry_value("index_to", str(len(df)))
                to_idx = int(to_val) if to_val else len(df)
                return df.iloc[from_idx:to_idx].copy()
            except (ValueError, TypeError):
                self.logger.log("Índice inválido no filtro de linhas.", "ERROR")
                return None
        elif mode == "value":
            try:
                col = self._get_entry_value("value_col")
                op = self._get_entry_value("value_op", "==")
                val = self._get_entry_value("value_val")
                if not col or val == "":
                    self.logger.log("Preencha coluna e valor para filtrar.", "WARNING")
                    return df.copy()
                series = df[col]
                if pd.api.types.is_numeric_dtype(series):
                    try: val = float(val)
                    except: pass
                if op == "==": mask = series == val
                elif op == "!=": mask = series != val
                elif op == ">": mask = series > val
                elif op == "<": mask = series < val
                elif op == ">=": mask = series >= val
                elif op == "<=": mask = series <= val
                elif op == "contains": mask = series.astype(str).str.contains(val, case=False, na=False)
                else: mask = pd.Series([True] * len(df), index=df.index)
                result = df[mask].copy()
                if result.empty:
                    self.logger.log(f"Filtro por valor não retornou linhas. Verifique os critérios.", "WARNING")
                return result
            except Exception as e:
                self.logger.log(f"Erro no filtro por valor: {str(e)}", "ERROR")
                return None
        elif mode == "sample":
            try:
                n = int(self._get_entry_value("sample_n", "100"))
                randomize = self._get_entry_value("sample_random", True)
                if n >= len(df):
                    return df.copy()
                return df.sample(n=n, random_state=42 if randomize else None).copy()
            except (ValueError, TypeError):
                self.logger.log("Tamanho de amostra inválido.", "ERROR")
                return None
        return df.copy()

    def _update_row_count_label(self):
        if not hasattr(self, 'row_count_lbl') or self.row_count_lbl is None:
            return
        df = self.dm.get_active_df()
        if df is None:
            self.row_count_lbl.config(text="Linhas: 0 (selecione uma tabela)")
            return
        filtered = self._apply_row_filter(df)
        if filtered is not None:
            self.row_count_lbl.config(text=f"Linhas: {len(filtered)} de {len(df)} (após filtro)")
        else:
            self.row_count_lbl.config(text="Linhas: erro no filtro")

    def _get_filtered_df_for_stats(self):
        df = self.dm.get_active_df()
        if df is None: return None
        df_filtered = self._apply_row_filter(df)
        if df_filtered is None or df_filtered.empty:
            return None
        if not self.stats_col_vars:
            return df_filtered.select_dtypes(include=[np.number]).dropna()
        selected = [c for c, v in self.stats_col_vars.items() if v.get()]
        if not selected:
            return None
        available = [c for c in selected if c in df_filtered.columns]
        if not available:
            return None
        result = df_filtered[available].dropna()
        return result

    def _get_id_column(self):
        id_col = self.id_column_var.get().strip()
        if id_col and id_col != "(nenhum)":
            return id_col
        return None

    def show_stats_table(self, df, title, id_col=None):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("700x500")
        win.configure(bg=THEME["bg"])
        btn_frame = tk.Frame(win, bg=THEME["bg"])
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        if id_col:
            tk.Label(btn_frame, text=f"🏷️ ID: {id_col}", bg=THEME["bg"], 
                    fg=THEME["accent"], font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="💾 Salvar Esta Tabela", 
                  command=lambda: self._save_dataframe(df, title)).pack(side=tk.RIGHT)
        tree = ttk.Treeview(win)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        tree["columns"] = list(df.columns)
        tree["show"] = "headings"
        for c in df.columns:
            tree.heading(c, text=c)
            tree.column(c, width=120)
        for _, row in df.iterrows():
            tree.insert("", tk.END, values=list(row))

    def _save_dataframe(self, df, title):
        filetypes = [("CSV", "*.csv"), ("Excel", "*.xlsx"), ("JSON", "*.json")]
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=filetypes,
                                            initialfile=f"{title}_export", title="Salvar Resultados")
        if not path: return
        try:
            if path.endswith(".csv"):
                df.to_csv(path, index=False, encoding='utf-8-sig')
            elif path.endswith(".xlsx"):
                df.to_excel(path, index=False, engine='openpyxl')
            elif path.endswith(".json"):
                df.to_json(path, orient='records', force_ascii=False, indent=2)
            self.logger.log(f"Resultados salvos: {os.path.basename(path)}", "SUCCESS")
        except Exception as e:
            self.logger.log(f"Erro ao salvar: {str(e)}", "ERROR")

    # === FUNÇÕES DE ESTATÍSTICA ===
    def run_desc_stats(self):
        self._update_selected_stats_cols()
        df = self._get_filtered_df_for_stats()
        id_col = self._get_id_column()
        if df is None: 
            self.logger.log("Nenhum dado válido após filtros de colunas e linhas.", "ERROR")
            messagebox.showwarning("Aviso", "Selecione colunas numéricas e ajuste o filtro de linhas.")
            return
        if df.empty:
            self.logger.log("Dados filtrados resultaram em dataframe vazio.", "ERROR")
            return
        stats = pd.DataFrame({
            "Média": df.mean(), "Mediana": df.median(), "Desvio": df.std(),
            "Mín": df.min(), "Máx": df.max(),
            "Assimetria": df.apply(skew), "Curtose": df.apply(kurtosis)
        })
        if id_col and id_col in self.dm.get_active_df().columns:
            id_data = self.dm.get_active_df()[id_col]
            stats.loc["ID_Únicos"] = [id_data.nunique()] * len(stats.columns)
            stats.loc["ID_Primeiro"] = [str(id_data.iloc[0]) if len(id_data) > 0 else "N/A"] * len(stats.columns)
            stats.loc["ID_Último"] = [str(id_data.iloc[-1]) if len(id_data) > 0 else "N/A"] * len(stats.columns)
            self.logger.log(f"Estatísticas geradas com ID '{id_col}': {len(df)} linhas × {len(df.columns)} colunas.", "SUCCESS")
        else:
            self.logger.log(f"Estatísticas geradas: {len(df)} linhas × {len(df.columns)} colunas.", "SUCCESS")
        self.show_stats_table(stats, "Estatísticas_Descritivas", id_col)

    def run_correlation(self):
        self._update_selected_stats_cols()
        df = self._get_filtered_df_for_stats()
        id_col = self._get_id_column()
        if df is None or df.shape[1] < 2:
            self.logger.log("Selecione pelo menos 2 colunas para correlação.", "ERROR")
            messagebox.showwarning("Aviso", "Correlação requer mínimo de 2 colunas numéricas.")
            return
        corr = df.corr()
        self.show_stats_table(corr, "Matriz_Correlacao", id_col)
        self._plot_in_tab(corr, "heatmap")
        self.logger.log(f"Correlação calculada: {len(df)} linhas × {len(df.columns)} colunas.", "SUCCESS")

    def run_outliers_iqr(self):
        self._update_selected_stats_cols()
        df = self._get_filtered_df_for_stats()
        id_col = self._get_id_column()
        if df is None:
            self.logger.log("Nenhuma coluna selecionada para outliers.", "ERROR")
            return
        Q1 = df.quantile(0.25)
        Q3 = df.quantile(0.75)
        IQR = Q3 - Q1
        outliers = ((df < (Q1 - 1.5 * IQR)) | (df > (Q3 + 1.5 * IQR))).sum()
        self.show_stats_table(outliers.to_frame(name="Qtd_Outliers"), "Outliers_IQR", id_col)
        self.logger.log("Outliers IQR calculados.", "SUCCESS")

    def run_outliers_z(self):
        self._update_selected_stats_cols()
        df = self._get_filtered_df_for_stats()
        id_col = self._get_id_column()
        if df is None:
            self.logger.log("Nenhuma coluna selecionada para outliers.", "ERROR")
            return
        z = np.abs(zscore(df))
        outliers = (z > 3).sum()
        self.show_stats_table(outliers.to_frame(name="Qtd_Outliers"), "Outliers_ZScore", id_col)
        self.logger.log("Outliers Z-Score calculados.", "SUCCESS")

    def run_regression(self):
        self._update_selected_stats_cols()
        df = self._get_filtered_df_for_stats()
        id_col = self._get_id_column()
        if df is None or df.shape[1] < 2:
            messagebox.showwarning("Erro", "Selecione pelo menos 2 colunas numéricas para regressão.")
            return
        x = df.iloc[:, [0]]
        y = df.iloc[:, 1]
        model = LinearRegression().fit(x, y)
        r2 = model.score(x, y)
        res = pd.DataFrame({"Metrica": ["Coeficiente", "Intercepto", "R²"],
                           "Valor": [model.coef_[0], model.intercept_, r2]})
        self.show_stats_table(res, "Regressao_Linear", id_col)
        self._plot_in_tab(df, "regression", x.name, y.name, model)
        self.logger.log("Regressão linear calculada.", "SUCCESS")

    def _plot_in_tab(self, data, type_, x_name=None, y_name=None, model=None):
        for widget in self.stats_canvas_frame.winfo_children():
            widget.destroy()
        fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
        fig.patch.set_facecolor(THEME["panel"])
        ax.set_facecolor(THEME["panel"])
        ax.tick_params(colors=THEME["fg"])
        ax.xaxis.label.set_color(THEME["fg"])
        ax.yaxis.label.set_color(THEME["fg"])
        ax.title.set_color(THEME["fg"])
        if type_ == "heatmap":
            cax = ax.matshow(data.corr() if hasattr(data, 'corr') else data, cmap='coolwarm')
            fig.colorbar(cax)
            ax.set_title("Heatmap de Correlação")
        elif type_ == "regression":
            ax.scatter(data.iloc[:, 0], data.iloc[:, 1], alpha=0.5, color=THEME["accent"])
            ax.plot(data.iloc[:, 0], model.predict(data.iloc[:, [0]]), color='red', linewidth=2)
            ax.set_xlabel(x_name)
            ax.set_ylabel(y_name)
            ax.set_title("Regressão Linear")
            ax.grid(True, linestyle='--', alpha=0.3)
        canvas = FigureCanvasTkAgg(fig, master=self.stats_canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # =======================
    # TAB 4: ENGENHARIA
    # =======================
    def _build_engine_tab(self):
        join_frame = ttk.LabelFrame(self.tab_engine, text="Pipeline de Join", padding=10)
        join_frame.pack(fill=tk.X, padx=10, pady=10)
        self.join_left = ttk.Combobox(join_frame, state="readonly")
        self.join_left.pack(side=tk.LEFT, padx=5)
        tk.Label(join_frame, text="⟶", bg=THEME["bg"], fg=THEME["fg"]).pack(side=tk.LEFT)
        self.join_right = ttk.Combobox(join_frame, state="readonly")
        self.join_right.pack(side=tk.LEFT, padx=5)
        tk.Label(join_frame, text="Chave A:", bg=THEME["bg"], fg=THEME["fg"]).pack(side=tk.LEFT, padx=5)
        self.join_key_a = ttk.Entry(join_frame, width=10)
        self.join_key_a.insert(0, "id")
        self.join_key_a.pack(side=tk.LEFT, padx=5)
        tk.Label(join_frame, text="Chave B:", bg=THEME["bg"], fg=THEME["fg"]).pack(side=tk.LEFT, padx=5)
        self.join_key_b = ttk.Entry(join_frame, width=10)
        self.join_key_b.insert(0, "id")
        self.join_key_b.pack(side=tk.LEFT, padx=5)
        self.join_type = ttk.Combobox(join_frame, values=["inner", "left", "right", "outer"], state="readonly", width=8)
        self.join_type.set("inner")
        self.join_type.pack(side=tk.LEFT, padx=5)
        ttk.Button(join_frame, text="Executar Join", command=self.run_join).pack(side=tk.LEFT, padx=10)
        ttk.Button(join_frame, text="💾 Salvar Resultado", command=self.save_data).pack(side=tk.LEFT)
        sql_frame = ttk.LabelFrame(self.tab_engine, text="SQL Query (Tabela Atual = 'data')", padding=10)
        sql_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.sql_entry = tk.Text(sql_frame, height=5, bg=THEME["text_field"], fg=THEME["fg"])
        self.sql_entry.pack(fill=tk.X, padx=5, pady=5)
        self.sql_entry.insert(tk.END, "SELECT * FROM data LIMIT 50")
        ttk.Button(sql_frame, text="Executar SQL", command=self.run_sql).pack(pady=5)
        self.sql_status = tk.Label(sql_frame, text="", bg=THEME["bg"], fg=THEME["accent"])
        self.sql_status.pack()

    def update_engine_combos(self):
        vals = list(self.dm.tables.keys())
        self.join_left['values'] = vals
        self.join_right['values'] = vals
        if vals:
            self.join_left.set(vals[0])
            if len(vals) > 1: self.join_right.set(vals[1])

    def run_join(self):
        t1, t2 = self.join_left.get(), self.join_right.get()
        k1, k2 = self.join_key_a.get(), self.join_key_b.get()
        how = self.join_type.get()
        if not t1 or not t2:
            messagebox.showwarning("Erro", "Selecione as tabelas.")
            return
        df1, df2 = self.dm.tables.get(t1), self.dm.tables.get(t2)
        if df1 is None or df2 is None: return
        try:
            res = pd.merge(df1, df2, left_on=k1, right_on=k2, how=how)
            name = f"Join_{t1}_{t2}_{datetime.now().strftime('%H%M%S')}"
            self.dm.add_table(name, res)
            self.refresh_table_list()
            self.logger.log(f"Join realizado: {name}", "SUCCESS")
        except Exception as e:
            self.logger.log(f"Erro no Join: {str(e)}", "ERROR")

    def run_sql(self):
        df = self.dm.get_active_df()
        if df is None:
            self.logger.log("Nenhuma tabela selecionada para SQL.", "ERROR")
            return
        query = self.sql_entry.get("1.0", tk.END)
        try:
            conn = sqlite3.connect(":memory:")
            df.to_sql("data", conn, index=False)
            res = pd.read_sql_query(query, conn)
            conn.close()
            name = f"SQL_{datetime.now().strftime('%H%M%S')}"
            self.dm.add_table(name, res)
            self.refresh_table_list()
            self.sql_status.config(text=f"Sucesso! {len(res)} linhas.")
            self.logger.log("Query SQL executada.", "SUCCESS")
        except Exception as e:
            self.sql_status.config(text=f"Erro: {str(e)}")
            self.logger.log(f"SQL Error: {str(e)}", "ERROR")

if __name__ == "__main__":
    app = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    DataKenEngineerLab(app)
    app.mainloop()
