"""Tkinter user interface."""

from __future__ import annotations

import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .media import MediaError, VideoInfo, convert_video, probe_video

BG = "#101318"
PANEL = "#191e26"
TEXT = "#edf1f7"
MUTED = "#9aa6b5"
ACCENT = "#63a6ff"


class VideoStretcherApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("CS2 Video Stretcher | Esticador de vídeo")
        self.geometry("760x680")
        self.minsize(680, 620)
        self.configure(bg=BG)
        asset_dir = (Path(sys._MEIPASS) / "cs2_stretcher" / "assets" if getattr(sys, "frozen", False)
                     else Path(__file__).resolve().parent / "assets")
        icon_png = asset_dir / "icon.png"
        if icon_png.exists():
            self._window_icon = tk.PhotoImage(file=str(icon_png))
            self.iconphoto(True, self._window_icon)
        self.source: Path | None = None
        self.info: VideoInfo | None = None
        self.events: queue.Queue = queue.Queue()
        self._build_ui()
        self.after(100, self._poll_events)

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=PANEL, background=PANEL, foreground=TEXT, arrowcolor=TEXT,
                        selectbackground=ACCENT, selectforeground=TEXT)
        style.map("TCombobox", fieldbackground=[("readonly", PANEL)], foreground=[("readonly", TEXT)])
        style.configure("Horizontal.TProgressbar", troughcolor=PANEL, background=ACCENT)
        self.option_add("*TCombobox*Listbox*Background", PANEL)
        self.option_add("*TCombobox*Listbox*Foreground", TEXT)
        self.option_add("*TCombobox*Listbox*selectBackground", ACCENT)
        self.option_add("*TCombobox*Listbox*selectForeground", TEXT)
        self.columnconfigure(0, weight=1)
        container = tk.Frame(self, bg=BG, padx=30, pady=24)
        container.grid(sticky="nsew")
        container.columnconfigure(0, weight=1)
        tk.Label(container, text="CS2 VIDEO STRETCHER", bg=BG, fg=TEXT, font=("Segoe UI", 20, "bold")).grid(row=0, column=0, sticky="w")
        tk.Label(container, text="Estique a imagem para widescreen sem cortar nenhuma parte do vídeo.", bg=BG, fg=MUTED, font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=(4, 20))
        self._section(container, 3, "VÍDEO DE ORIGEM")
        source_row = tk.Frame(container, bg=PANEL, padx=14, pady=14)
        source_row.grid(row=4, column=0, sticky="ew")
        source_row.columnconfigure(0, weight=1)
        self.source_label = tk.Label(source_row, text="Selecione uma gravação de gameplay para começar", bg=PANEL, fg=MUTED, anchor="w")
        self.source_label.grid(row=0, column=0, sticky="ew")
        self.source_button = self._button(source_row, "Selecionar vídeo", self._choose_source)
        self.source_button.configure(width=18)
        self.source_button.grid(row=0, column=1, padx=(12, 0))
        self.info_label = tk.Label(container, text="A resolução e a duração aparecerão aqui após a seleção.", bg=BG, fg=MUTED, anchor="w", pady=12)
        self.info_label.grid(row=5, column=0, sticky="ew")
        self._section(container, 6, "EXPORTAÇÃO")
        panel = tk.Frame(container, bg=PANEL, padx=16, pady=16)
        panel.grid(row=7, column=0, sticky="ew")
        for col in range(4): panel.columnconfigure(col, weight=1)
        self._label(panel, "Resolução de saída", 0, 0)
        self.resolution = ttk.Combobox(panel, values=("1920 x 1080", "2560 x 1440", "3840 x 2160"), state="readonly", width=18)
        self.resolution.current(0); self.resolution.grid(row=1, column=0, sticky="ew", padx=(0, 12), pady=(5, 0))
        self._label(panel, "Qualidade (CRF)", 0, 1,
                    "O CRF controla a qualidade e o tamanho do arquivo. Número menor significa mais qualidade e arquivo maior. Para gameplay, 18 a 23 costuma ser uma boa faixa.")
        self.quality = ttk.Combobox(panel, values=("18 - Alta", "20 - Equilibrada", "23 - Arquivo menor", "28 - Compacta"), state="readonly", width=18)
        self.quality.current(1); self.quality.grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=(5, 0))
        self._label(panel, "Pasta de destino", 2, 0)
        self.destination = tk.StringVar(value=str(Path.home() / "Videos"))
        self.destination_entry = tk.Entry(panel, textvariable=self.destination, bg="#11151b", fg=TEXT, insertbackground=TEXT, relief="flat")
        self.destination_entry.grid(row=3, column=0, columnspan=3, sticky="ew", padx=(0, 10), pady=(5, 0), ipady=8)
        self.folder_button = self._button(panel, "Escolher pasta", self._choose_folder)
        self.folder_button.configure(width=18)
        self.folder_button.grid(row=3, column=3, sticky="ew", pady=(5, 0))
        self.convert_button = self._button(container, "Iniciar conversão", self._start_conversion, accent=True)
        self.convert_button.grid(row=8, column=0, sticky="ew", pady=(18, 10), ipady=4)
        self.progress = ttk.Progressbar(container, mode="determinate", maximum=100)
        self.progress.grid(row=9, column=0, sticky="ew")
        self.status = tk.Label(container, text="Pronto", bg=BG, fg=MUTED, anchor="w", pady=10)
        self.status.grid(row=10, column=0, sticky="ew")
        tk.Label(container, text="A imagem inteira será redimensionada; os elementos ficarão mais largos de propósito.", bg=BG, fg=MUTED, font=("Segoe UI", 9)).grid(row=11, column=0, sticky="w", pady=(5, 0))

    def _section(self, parent: tk.Widget, row: int, title: str) -> None:
        tk.Label(parent, text=title, bg=BG, fg=ACCENT, font=("Segoe UI", 9, "bold")).grid(row=row, column=0, sticky="w", pady=(4, 8))

    def _label(self, parent: tk.Widget, text: str, row: int, column: int, tooltip: str | None = None) -> None:
        label = tk.Label(parent, text=text, bg=PANEL, fg=MUTED, anchor="w")
        label.grid(row=row, column=column, sticky="w")
        if tooltip:
            pending = {"after_id": None, "window": None}

            def hide(_event=None) -> None:
                if pending["after_id"]:
                    self.after_cancel(pending["after_id"])
                    pending["after_id"] = None
                if pending["window"]:
                    pending["window"].destroy()
                    pending["window"] = None

            def show() -> None:
                pending["after_id"] = None
                if not label.winfo_exists():
                    return
                tip = tk.Toplevel(self)
                tip.wm_overrideredirect(True)
                tip.configure(bg="#344052")
                tip.wm_geometry(f"+{label.winfo_rootx()}+{label.winfo_rooty() + label.winfo_height() + 6}")
                tk.Label(tip, text=tooltip, bg="#252d39", fg=TEXT, justify="left", wraplength=300,
                         padx=10, pady=8, font=("Segoe UI", 9)).pack()
                pending["window"] = tip

            label.bind("<Enter>", lambda _event: pending.update(after_id=self.after(450, show)))
            label.bind("<Leave>", hide)

    def _button(self, parent: tk.Widget, text: str, command, accent: bool = False) -> tk.Button:
        return tk.Button(parent, text=text, command=command, bg=ACCENT if accent else "#29313d", fg="#08111d" if accent else TEXT, activebackground="#82b9ff", activeforeground="#08111d", relief="flat", padx=14, pady=8, font=("Segoe UI", 10, "bold" if accent else "normal"), cursor="hand2")

    def _choose_source(self) -> None:
        selected = filedialog.askopenfilename(title="Selecionar vídeo de gameplay", filetypes=[("Arquivos de vídeo", "*.mp4 *.mkv *.mov *.avi *.webm *.m4v"), ("Todos os arquivos", "*.*")])
        if not selected: return
        self.source = Path(selected)
        self.info = None
        self.source_label.configure(text=self.source.name, fg=TEXT)
        self.info_label.configure(text="Lendo as propriedades do vídeo…", fg=MUTED)
        threading.Thread(target=self._probe_worker, args=(self.source,), daemon=True).start()

    def _probe_worker(self, path: Path) -> None:
        try: self.events.put(("info", path, probe_video(path)))
        except MediaError as exc: self.events.put(("error", str(exc)))

    def _choose_folder(self) -> None:
        selected = filedialog.askdirectory(title="Escolher pasta de destino", initialdir=self.destination.get())
        if selected: self.destination.set(selected)

    def _start_conversion(self) -> None:
        if not self.source or not self.info:
            messagebox.showinfo("Selecione um vídeo", "Escolha um vídeo e aguarde o carregamento das informações."); return
        output_dir = Path(self.destination.get()).expanduser()
        try: output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("Pasta de destino indisponível", str(exc)); return
        width, height = (int(part.strip()) for part in self.resolution.get().split("x"))
        crf = int(self.quality.get().split(" ", 1)[0])
        target = output_dir / f"{self.source.stem}_stretched_{width}x{height}.mp4"
        if target.resolve() == self.source.resolve():
            messagebox.showerror("Destino inválido", "O arquivo de saída não pode substituir o vídeo original."); return
        self.convert_button.configure(state="disabled")
        self._set_input_state("disabled")
        self.progress.configure(value=0)
        self.status.configure(text=f"Convertendo para {target.name}…", fg=MUTED)
        threading.Thread(target=self._convert_worker, args=(self.source, self.info, target, width, height, crf), daemon=True).start()

    def _convert_worker(self, source: Path, info: VideoInfo, target: Path, width: int, height: int, crf: int) -> None:
        try:
            convert_video(source, target, width, height, crf, info.duration, lambda value: self.events.put(("progress", value)))
            self.events.put(("complete", target))
        except MediaError as exc: self.events.put(("error", str(exc)))

    def _set_input_state(self, state: str) -> None:
        self.source_button.configure(state=state)
        self.folder_button.configure(state=state)
        self.destination_entry.configure(state=state)
        self.resolution.configure(state="disabled" if state == "disabled" else "readonly")
        self.quality.configure(state="disabled" if state == "disabled" else "readonly")

    def _poll_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "info":
                    _, path, info = event
                    if self.source == path:
                        self.info = info
                        minutes, seconds = divmod(int(info.duration), 60)
                        self.info_label.configure(text=f"{info.width} × {info.height}   ·   {minutes}:{seconds:02d}", fg=TEXT)
                elif event[0] == "progress":
                    self.progress.configure(value=event[1] * 100)
                    self.status.configure(text=f"Convertendo… {event[1] * 100:.0f}%")
                elif event[0] == "complete":
                    self.convert_button.configure(state="normal")
                    self._set_input_state("normal")
                    self.progress.configure(value=100)
                    self.status.configure(
                        text="Conversão concluída com sucesso! Agora é só acessar a pasta selecionada e abrir o vídeo.",
                        fg="#76d7a5",
                    )
                elif event[0] == "error":
                    self.convert_button.configure(state="normal")
                    self._set_input_state("normal")
                    self.status.configure(text="Não foi possível concluir a conversão.", fg="#ff8282")
                    messagebox.showerror("Erro ao processar o vídeo", event[1])
        except queue.Empty:
            pass
        self.after(100, self._poll_events)
