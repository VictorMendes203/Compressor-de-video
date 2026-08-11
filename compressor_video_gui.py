#!/usr/bin/env python3
"""
compressor_video_gui.py — App desktop com interface gráfica para comprimir vídeos.

Requisitos:
    1) FFmpeg instalado e no PATH
       Windows: winget install ffmpeg
       Mac:     brew install ffmpeg
       Linux:   sudo apt install ffmpeg

    2) Biblioteca customtkinter:
       pip install customtkinter

Uso:
    python compressor_video_gui.py
"""

import shutil
import subprocess
import sys
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

try:
    import customtkinter as ctk
except ImportError:
    print("❌ Biblioteca 'customtkinter' não encontrada.")
    print("   Instale com: pip install customtkinter")
    sys.exit(1)

PRESETS_QUALIDADE = {
    "Alta qualidade": 20,
    "Média (recomendado)": 24,
    "Compressão forte": 28,
    "Compressão extrema": 32,
}

RESOLUCOES = {
    "Original": None,
    "1080p": 1080,
    "720p": 720,
    "480p": 480,
    "360p": 360,
}

EXTENSOES_VIDEO = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".wmv", ".flv"}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def formatar_tamanho(bytes_: int) -> str:
    tamanho = float(bytes_)
    for unidade in ["B", "KB", "MB", "GB"]:
        if tamanho < 1024:
            return f"{tamanho:.1f} {unidade}"
        tamanho /= 1024
    return f"{tamanho:.1f} TB"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Compressor de Vídeo")
        self.geometry("640x600")
        self.minsize(560, 560)

        self.arquivos: list[Path] = []
        self.pasta_saida: Path | None = None
        self.processando = False

        self._montar_interface()

    # ---------- UI ----------

    def _montar_interface(self):
        pad = 20

        titulo = ctk.CTkLabel(self, text="🎬 Compressor de Vídeo",
                               font=ctk.CTkFont(size=22, weight="bold"))
        titulo.pack(pady=(pad, 5))

        subtitulo = ctk.CTkLabel(self, text="Comprima vídeos localmente usando FFmpeg",
                                  font=ctk.CTkFont(size=13), text_color="gray")
        subtitulo.pack(pady=(0, pad))

        # --- Área de seleção de arquivos ---
        frame_arquivos = ctk.CTkFrame(self)
        frame_arquivos.pack(fill="x", padx=pad, pady=(0, 10))

        botoes_frame = ctk.CTkFrame(frame_arquivos, fg_color="transparent")
        botoes_frame.pack(fill="x", padx=15, pady=(15, 5))

        ctk.CTkButton(botoes_frame, text="📄 Escolher vídeo(s)",
                      command=self.escolher_arquivos).pack(side="left", padx=(0, 10))
        ctk.CTkButton(botoes_frame, text="📁 Escolher pasta",
                      command=self.escolher_pasta).pack(side="left")
        ctk.CTkButton(botoes_frame, text="Limpar", fg_color="gray30", hover_color="gray20",
                      command=self.limpar_selecao).pack(side="right")

        self.label_selecionados = ctk.CTkLabel(
            frame_arquivos, text="Nenhum vídeo selecionado", justify="left", anchor="w",
            wraplength=560, text_color="gray"
        )
        self.label_selecionados.pack(fill="x", padx=15, pady=(5, 15))

        # --- Opções ---
        frame_opcoes = ctk.CTkFrame(self)
        frame_opcoes.pack(fill="x", padx=pad, pady=10)

        ctk.CTkLabel(frame_opcoes, text="Qualidade", anchor="w").grid(
            row=0, column=0, sticky="w", padx=15, pady=(15, 5))
        self.combo_qualidade = ctk.CTkOptionMenu(frame_opcoes, values=list(PRESETS_QUALIDADE.keys()))
        self.combo_qualidade.set("Média (recomendado)")
        self.combo_qualidade.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))

        ctk.CTkLabel(frame_opcoes, text="Resolução", anchor="w").grid(
            row=0, column=1, sticky="w", padx=15, pady=(15, 5))
        self.combo_resolucao = ctk.CTkOptionMenu(frame_opcoes, values=list(RESOLUCOES.keys()))
        self.combo_resolucao.set("Original")
        self.combo_resolucao.grid(row=1, column=1, sticky="ew", padx=15, pady=(0, 15))

        ctk.CTkLabel(frame_opcoes, text="Codec", anchor="w").grid(
            row=0, column=2, sticky="w", padx=15, pady=(15, 5))
        self.combo_codec = ctk.CTkOptionMenu(frame_opcoes, values=["H.264 (compatível)", "H.265 (menor arquivo)"])
        self.combo_codec.set("H.264 (compatível)")
        self.combo_codec.grid(row=1, column=2, sticky="ew", padx=15, pady=(0, 15))

        frame_opcoes.grid_columnconfigure((0, 1, 2), weight=1)

        self.check_audio = ctk.CTkCheckBox(self, text="Manter áudio")
        self.check_audio.select()
        self.check_audio.pack(anchor="w", padx=pad + 15, pady=(0, 10))

        # --- Botão comprimir ---
        self.botao_comprimir = ctk.CTkButton(
            self, text="Comprimir", height=42, font=ctk.CTkFont(size=15, weight="bold"),
            command=self.iniciar_compressao
        )
        self.botao_comprimir.pack(fill="x", padx=pad, pady=(10, 5))

        self.barra_progresso = ctk.CTkProgressBar(self)
        self.barra_progresso.set(0)
        self.barra_progresso.pack(fill="x", padx=pad, pady=(5, 5))

        self.label_status = ctk.CTkLabel(self, text="", text_color="gray")
        self.label_status.pack(pady=(0, 5))

        # --- Log ---
        self.caixa_log = ctk.CTkTextbox(self, height=150)
        self.caixa_log.pack(fill="both", expand=True, padx=pad, pady=(5, pad))
        self.caixa_log.configure(state="disabled")

    # ---------- Ações ----------

    def log(self, texto: str):
        self.caixa_log.configure(state="normal")
        self.caixa_log.insert("end", texto + "\n")
        self.caixa_log.see("end")
        self.caixa_log.configure(state="disabled")

    def escolher_arquivos(self):
        caminhos = filedialog.askopenfilenames(
            title="Escolha um ou mais vídeos",
            filetypes=[("Vídeos", " ".join(f"*{ext}" for ext in EXTENSOES_VIDEO)), ("Todos os arquivos", "*.*")]
        )
        if caminhos:
            self.arquivos = [Path(c) for c in caminhos]
            self.pasta_saida = None
            self._atualizar_label_selecao()

    def escolher_pasta(self):
        pasta = filedialog.askdirectory(title="Escolha uma pasta com vídeos")
        if pasta:
            pasta_path = Path(pasta)
            self.arquivos = sorted([f for f in pasta_path.iterdir() if f.suffix.lower() in EXTENSOES_VIDEO])
            if not self.arquivos:
                messagebox.showwarning("Aviso", "Nenhum vídeo encontrado nessa pasta.")
            self._atualizar_label_selecao()

    def limpar_selecao(self):
        self.arquivos = []
        self._atualizar_label_selecao()

    def _atualizar_label_selecao(self):
        if not self.arquivos:
            self.label_selecionados.configure(text="Nenhum vídeo selecionado")
        elif len(self.arquivos) == 1:
            self.label_selecionados.configure(text=f"1 vídeo selecionado: {self.arquivos[0].name}")
        else:
            nomes = ", ".join(a.name for a in self.arquivos[:3])
            extra = f" e mais {len(self.arquivos) - 3}" if len(self.arquivos) > 3 else ""
            self.label_selecionados.configure(text=f"{len(self.arquivos)} vídeos selecionados: {nomes}{extra}")

    def iniciar_compressao(self):
        if self.processando:
            return
        if not self.arquivos:
            messagebox.showwarning("Aviso", "Escolha ao menos um vídeo primeiro.")
            return
        if not shutil.which("ffmpeg"):
            messagebox.showerror(
                "FFmpeg não encontrado",
                "Instale o FFmpeg antes de continuar:\n\n"
                "Windows: winget install ffmpeg\n"
                "Mac: brew install ffmpeg\n"
                "Linux: sudo apt install ffmpeg"
            )
            return

        self.processando = True
        self.botao_comprimir.configure(state="disabled", text="Comprimindo...")
        self.barra_progresso.set(0)

        thread = threading.Thread(target=self._comprimir_todos, daemon=True)
        thread.start()

    def _comprimir_todos(self):
        crf = PRESETS_QUALIDADE[self.combo_qualidade.get()]
        resolucao = RESOLUCOES[self.combo_resolucao.get()]
        codec = "libx264" if "H.264" in self.combo_codec.get() else "libx265"
        manter_audio = bool(self.check_audio.get())

        total = len(self.arquivos)
        for i, entrada in enumerate(self.arquivos, start=1):
            self._set_status(f"Comprimindo {i}/{total}: {entrada.name}")
            self._log_thread_safe(f"\n🎬 {entrada.name}")

            saida = entrada.parent / f"{entrada.stem}_comprimido.mp4"

            cmd = ["ffmpeg", "-y", "-i", str(entrada), "-c:v", codec, "-crf", str(crf), "-preset", "medium"]
            if resolucao:
                cmd += ["-vf", f"scale=-2:{resolucao}"]
            if manter_audio:
                cmd += ["-c:a", "aac", "-b:a", "128k"]
            else:
                cmd += ["-an"]
            cmd += [str(saida)]

            resultado = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            if resultado.returncode != 0:
                self._log_thread_safe(f"❌ Erro ao comprimir {entrada.name}")
                self._log_thread_safe(resultado.stdout[-500:])
            else:
                original = entrada.stat().st_size
                novo = saida.stat().st_size
                reducao = (1 - novo / original) * 100 if original else 0
                self._log_thread_safe(
                    f"✅ {saida.name} — {formatar_tamanho(original)} → {formatar_tamanho(novo)} "
                    f"({reducao:.1f}% menor)"
                )

            self.barra_progresso.set(i / total)

        self._set_status(f"Concluído! {total} vídeo(s) processado(s).")
        self.processando = False
        self.botao_comprimir.configure(state="normal", text="Comprimir")

    def _set_status(self, texto: str):
        self.label_status.configure(text=texto)

    def _log_thread_safe(self, texto: str):
        self.after(0, lambda: self.log(texto))


if __name__ == "__main__":
    app = App()
    app.mainloop()
